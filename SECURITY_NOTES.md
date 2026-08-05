# 依賴安全稽核紀錄

## 前端 `npm audit`（最後檢查：2026-08-05，Next.js 15.5.22）

已修正：

- Next.js 由 15.3.3 升級至 15.5.22（15.x 線最後一個發行版），解決約 20 個 Next.js 核心的資安公告（RSC 快取污染、Middleware bypass、SSRF、DoS 等）。
- `js-yaml`（透過 `eslint` 的傳遞依賴）由 `npm audit fix` 自動修復，僅影響開發期 lint，不影響正式產出。

殘留（無法在不升級 Next.js 大版本的情況下解決）：

| 套件 | 嚴重度 | 說明 | 風險判斷 |
|---|---|---|---|
| `postcss`（`next/node_modules/postcss`） | High | Next.js 15.5.22 內部固定捆綁 postcss@8.4.31，同版本的 CVE 需等 Next.js 發新版才會更新 | Postcss 只在 `next build` 建置期間處理**開發者自己撰寫**的 CSS/Tailwind 輸出，並未在執行期處理任何使用者輸入，實際可利用面很低 |
| `sharp` | High | Next.js 內建圖片優化 API 使用的選用依賴，`<0.35.0` 有 libvips 相關 CVE | 本專案**未使用** `next/image`（所有圖片皆為一般 `<img>` 標籤），此依賴的程式碼路徑從未被呼叫，實際曝險為零 |

以上三項都只能透過升級到 Next.js 16（major version）解決，屬於有明確 breaking change 風險的變更，故列為獨立追蹤事項，不在本輪處理範圍內。CI 的 `npm audit --audit-level=critical` 只擋新增的 critical 漏洞，不會因這三項既有 high 漏洞而失敗。

## 後端

後端 `requirements.txt` 目前無已知 critical 漏洞（未安裝額外稽核工具，之後可評估導入 `pip-audit`）。

## 追蹤機制

已啟用 Dependabot（見 `.github/dependabot.yml`），每週自動檢查 `frontend`（npm）、`backend`（pip）與 GitHub Actions 的依賴更新。
