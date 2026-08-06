import { defineConfig, devices } from '@playwright/test'

// E2E 測試需要一個真的在跑的後端（含資料庫、已建立好的管理者帳號）。
// 本機開發時可以先用 docker compose 把 backend/db 啟動，並用對應的環境變數
// 指向它們；CI 的設定見 .github/workflows/ci.yml 的 e2e job。
export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [['github'], ['html', { open: 'never' }]] : 'list',
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? 'http://localhost:3000',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
  // next.config.ts 設定了 output: 'standalone'（給 Docker 正式部署用），
  // 用 `next start` 執行它會印出一個警告說建議改用 standalone server.js，
  // 但 `next start` 本身仍會正常啟動、正常服務——這裡就是刻意繼續用
  // `next start`，因為 standalone 產物還需要另外手動複製 static/public
  // 才能跑，對測試用途來說沒必要，這個警告可以忽略。
  webServer: {
    command: 'npm run build && npm run start',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 180_000,
  },
})
