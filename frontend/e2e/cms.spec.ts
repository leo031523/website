import { test, expect, type Page } from '@playwright/test'

// 對應 AI_FEATURE_REQUIREMENTS.md P0 4.6：
// 「至少增加一條 Playwright E2E：登入、建立草稿、發布、前台讀取」。
// 帳號由 CI（或本機執行前）用 `python -m app.cli create-admin` 建立，
// 密碼不寫死在測試檔裡。

const ADMIN_USERNAME = process.env.E2E_ADMIN_USERNAME ?? 'e2e-admin'
const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD ?? 'e2e-admin-password-123456'

async function login(page: Page) {
  await page.goto('/admin/login')
  await page.getByLabel('帳號').fill(ADMIN_USERNAME)
  await page.getByLabel('密碼').fill(ADMIN_PASSWORD)
  await page.getByRole('button', { name: '登入' }).click()
  await page.waitForURL('/admin')
}

test('登入、建立草稿、發布、前台讀取；草稿在發布前不可公開讀取', async ({ page }) => {
  const title = `E2E 測試文章 ${Date.now()}`

  await login(page)

  await page.goto('/admin/articles/new')
  await page.locator('#article-title').fill(title)
  await page.locator('#article-content').fill('這是 Playwright E2E 測試建立的文章內容。')

  await page.getByRole('button', { name: '儲存草稿' }).click()
  await expect(page.getByText('草稿已儲存')).toBeVisible()
  await page.waitForURL(/\/admin\/articles\/\d+$/)

  const editUrl = page.url()
  // 換頁後編輯器會重新用 id 打 GET 取回文章、填回欄位，slug 欄位在那之前是空的
  await expect(page.locator('#article-slug')).not.toHaveValue('', { timeout: 10_000 })
  const slug = await page.locator('#article-slug').inputValue()
  expect(slug).toBeTruthy()

  // 草稿不可在前台被讀到：列表不出現、詳細頁回傳 404
  await page.goto('/blog')
  await expect(page.getByRole('heading', { name: title })).toHaveCount(0)

  const draftResponse = await page.goto(`/blog/${slug}`)
  expect(draftResponse?.status()).toBe(404)

  // 回到編輯頁發布；重新載入後欄位要等文章資料 GET 回來才會填值，
  // 太早點發布會因為標題欄位還是空的而被表單驗證擋下來
  await page.goto(editUrl)
  await expect(page.locator('#article-title')).toHaveValue(title, { timeout: 10_000 })
  await page.getByRole('button', { name: '發布' }).click()
  await expect(page.getByText('文章已發布')).toBeVisible()

  // 前台應該讀得到：列表與詳細頁都要看到剛發布的文章
  await page.goto('/blog')
  await expect(page.getByRole('heading', { name: title })).toBeVisible()

  const publishedResponse = await page.goto(`/blog/${slug}`)
  expect(publishedResponse?.status()).toBe(200)
  await expect(page.getByRole('heading', { name: title })).toBeVisible()
  await expect(page.getByText('這是 Playwright E2E 測試建立的文章內容。')).toBeVisible()

  // 清理：CI 用的是每次全新的資料庫，這裡主要是為了本機重複執行時不留垃圾資料。
  // page.request 跟 page 共用瀏覽器的登入 cookie，可以直接呼叫後台 API。
  const articleId = editUrl.match(/\/admin\/articles\/(\d+)$/)?.[1]
  if (articleId) {
    const apiBase = process.env.E2E_API_BASE_URL ?? 'http://localhost:8000/api'
    await page.request.delete(`${apiBase}/articles/${articleId}`).catch(() => {})
  }
})
