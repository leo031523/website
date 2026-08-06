import { test, expect, request as playwrightRequest, type APIRequestContext, type Page } from '@playwright/test'

// 對應 AI_FEATURE_REQUIREMENTS.md 14.3（AI 助理 E2E Test）：
// - 開啟 AI drawer、送出問題、看到答案與來源
// - 點擊來源後進入正確公開頁面
// - 重新整理後 session 對話保留
// - 清除對話後 storage 與畫面清空
// - 鍵盤可完成開啟、輸入、送出與關閉
// - Rate limit 與 provider 錯誤顯示正確 UI
//
// 「看到答案與來源」這一段用 page.route() 在瀏覽器網路層攔截
// /api/ai/chat，回傳固定的假回應，不會真的打到付費的 Gemini API——
// RAG 檢索、citation 驗證、prompt injection 防護這些後端邏輯已經在
// backend 的 integration test（respx mock）驗證過，E2E 這層要驗證的是
// 前端在收到一個成功回應時渲染是否正確，而不是重新證明一次後端邏輯。
// 「provider 認證失敗」與「速率限制」這兩段則是打真正的後端／真正的
// Gemini（用一把故意無效的假 key，認證失敗會很快回應，不會產生費用）。

const ADMIN_USERNAME = process.env.E2E_ADMIN_USERNAME ?? 'e2e-admin'
const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD ?? 'e2e-admin-password-123456'
const API_BASE_URL = process.env.E2E_API_BASE_URL ?? 'http://localhost:8000/api'

const ENTRY_BUTTON_NAME = '開啟 AI 助理對話視窗'
const KEYWORD = `泡泡龍語言${Date.now()}`

async function openDrawer(page: Page) {
  await page.goto('/')
  await page.getByRole('button', { name: ENTRY_BUTTON_NAME }).click()
  await expect(page.getByRole('dialog')).toBeVisible()
}

test.describe.serial('AI 助理', () => {
  let api: APIRequestContext
  let articleId: number
  let articleSlug: string
  let settingsId: number

  test.beforeAll(async () => {
    // 注意：不用 newContext({ baseURL }) + 相對路徑，因為 Playwright／WHATWG URL
    // 對「路徑開頭有斜線」的相對路徑，是相對「origin」而不是相對 baseURL 的路徑組合，
    // 會把 baseURL 裡的 /api 整段吃掉（例如算出 http://localhost:8000/auth/login
    // 而不是 http://localhost:8000/api/auth/login）。改用完整字串組合，行為明確不模糊。
    api = await playwrightRequest.newContext()
    const loginRes = await api.post(`${API_BASE_URL}/auth/login`, {
      data: { username: ADMIN_USERNAME, password: ADMIN_PASSWORD },
    })
    if (!loginRes.ok()) {
      throw new Error(`E2E setup 登入失敗：${loginRes.status()} ${await loginRes.text()}`)
    }

    const articleRes = await api.post(`${API_BASE_URL}/articles`, {
      data: {
        title: `AI 助理 E2E 測試文章 ${KEYWORD}`,
        content_md: `這篇文章介紹作者的 ${KEYWORD} 專案細節與心得。`,
        status: 'published',
      },
    })
    const article = await articleRes.json()
    articleId = article.id
    articleSlug = article.slug

    const settingsRes = await api.post(`${API_BASE_URL}/ai/settings`, {
      data: { provider: 'gemini', model: 'gemini-2.0-flash', api_key: 'e2e-invalid-fake-key-000' },
    })
    const settingsRow = await settingsRes.json()
    settingsId = settingsRow.id
    await api.post(`${API_BASE_URL}/ai/settings/${settingsId}/enable`)
  })

  test.afterAll(async () => {
    await api.delete(`${API_BASE_URL}/ai/settings/${settingsId}`)
    await api.delete(`${API_BASE_URL}/articles/${articleId}`)
    await api.dispose()
  })

  test('可以只用鍵盤完成開啟、輸入、送出與關閉，且會揭露訊息會送往哪個服務商', async ({ page }) => {
    await page.goto('/')

    const entry = page.getByRole('button', { name: ENTRY_BUTTON_NAME })
    await entry.focus()
    await page.keyboard.press('Enter')

    const dialog = page.getByRole('dialog')
    await expect(dialog).toBeVisible()
    await expect(dialog).toContainText('你的訊息會傳送給 Google Gemini 進行處理')

    // Escape 關閉，焦點還原回入口按鈕
    await page.keyboard.press('Escape')
    await expect(dialog).toBeHidden()
    await expect(entry).toBeFocused()
  })

  test('啟用的 provider 認證失敗時，顯示安全錯誤訊息並可重試，絕不洩漏金鑰', async ({ page }) => {
    await openDrawer(page)

    await page.locator('#ai-assistant-input').fill(`作者的${KEYWORD}專案是什麼？`)
    await page.keyboard.press('Enter')

    await expect(page.getByText('AI 服務目前設定有誤，請聯絡網站管理者')).toBeVisible({ timeout: 20_000 })
    await expect(page.getByRole('button', { name: '重試' })).toBeVisible()
    await expect(page.getByRole('dialog')).not.toContainText('e2e-invalid-fake-key-000')
  })

  test('看到答案與來源、來源可點擊進入正確頁面、重新整理後保留、清除對話後歸零', async ({ page }) => {
    const mockAnswer = `作者的 ${KEYWORD} 專案是一個示範用的測試專案。`
    const chunkId = `article:${articleId}#chunk-0`

    // 前端 fetch 用 credentials: 'include'，跨來源（:3000 打 :8000）又帶
    // cookie 時，瀏覽器要求 Access-Control-Allow-Origin 給明確的 origin
    // （不能是 "*"）且要有 Allow-Credentials，並且會先送一個 OPTIONS
    // preflight，這裡兩種 method 都要各自回應正確的 CORS header，
    // 否則瀏覽器會直接擋下請求，前端只會看到籠統的 "Failed to fetch"。
    const corsHeaders = {
      'access-control-allow-origin': 'http://localhost:3000',
      'access-control-allow-credentials': 'true',
      'access-control-allow-methods': 'POST, OPTIONS',
      'access-control-allow-headers': 'Content-Type',
    }

    await page.route('**/api/ai/chat', async route => {
      if (route.request().method() === 'OPTIONS') {
        await route.fulfill({ status: 204, headers: corsHeaders })
        return
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        headers: corsHeaders,
        body: JSON.stringify({
          answer: mockAnswer,
          sources: [
            {
              id: chunkId,
              title: `AI 助理 E2E 測試文章 ${KEYWORD}`,
              url: `/blog/${articleSlug}`,
              source_type: 'article',
              snippet: `這篇文章介紹作者的 ${KEYWORD} 專案細節與心得。`,
            },
          ],
          provider: 'gemini',
          model: 'gemini-2.0-flash',
          request_id: 'e2e-mock-request-id',
          grounded: true,
        }),
      })
    })

    await openDrawer(page)
    await page.locator('#ai-assistant-input').fill(`作者的${KEYWORD}專案是什麼？`)
    await page.keyboard.press('Enter')

    await expect(page.getByText(mockAnswer)).toBeVisible()
    const citation = page.getByRole('link', { name: new RegExp(`AI 助理 E2E 測試文章 ${KEYWORD}`) })
    await expect(citation).toBeVisible()

    await citation.click()
    await page.waitForURL(`**/blog/${articleSlug}`)
    await expect(
      page.getByRole('heading', { name: `AI 助理 E2E 測試文章 ${KEYWORD}` })
    ).toBeVisible()

    // 重新整理、甚至換一頁再回來，session 對話都要還在
    await page.goto('/')
    await page.reload()
    await page.getByRole('button', { name: ENTRY_BUTTON_NAME }).click()
    await expect(page.getByText(mockAnswer)).toBeVisible()

    // 清除對話：畫面與 storage 都要歸零
    await page.getByRole('button', { name: '清除對話' }).click()
    await expect(page.getByText(mockAnswer)).toHaveCount(0)
    const storedAfterClear = await page.evaluate(() => sessionStorage.getItem('ai-chat-history'))
    expect(storedAfterClear === null || JSON.parse(storedAfterClear).length === 0).toBe(true)

    await page.reload()
    await page.getByRole('button', { name: ENTRY_BUTTON_NAME }).click()
    await expect(page.getByText(mockAnswer)).toHaveCount(0)
  })

  test('達到速率限制時顯示明確的錯誤訊息', async ({ page }) => {
    await openDrawer(page)

    let sawRateLimitError = false
    for (let i = 0; i < 15 && !sawRateLimitError; i++) {
      await page.locator('#ai-assistant-input').fill(`不會命中任何文章的隨機問題-${Date.now()}-${i}`)
      await page.keyboard.press('Enter')
      await page.waitForFunction(
        () => !document.querySelector('[role="dialog"]')?.textContent?.includes('思考中'),
        { timeout: 20_000 }
      )
      sawRateLimitError = await page.getByText('請求過於頻繁，請稍後再試').isVisible()
    }

    expect(sawRateLimitError).toBe(true)
  })
})
