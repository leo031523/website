 1. 一句話定位

  ▎ 個人作品集與技術筆記網站，同時作為全鏈路工程能力的展示。

  2. Tech Stack 表格（招募方最在意）
  - 前端：Next.js 15 App Router + TypeScript + Tailwind CSS
  - 後端：FastAPI + SQLAlchemy + Alembic
  - 資料庫：PostgreSQL 16
  - 部署：Docker Compose + nginx + Certbot / Let's Encrypt
  - CI：GitHub Actions

  3. 功能列表
  列出 M1–M6 完成的主要功能（SSG/ISR、JWT 認證、後台 CMS、媒體上傳、全文搜尋、RSS、深色模式）

  4. 本地開發啟動步驟
  git clone ...
  cp .env.example .env  # 填入必要的密碼
  docker compose up -d
  docker compose exec backend alembic upgrade head
  建立管理者帳號（一次性）
  docker compose exec backend python scripts/seed_admin.py
  前往 http://localhost

  5. 架構圖（直接用規格書裡的 Mermaid 圖）

  6. CI Badge（放在最頂部）
  ![CI](https://github.com/leo031523/website/actions/workflows/ci.yml/badge.svg)

  7. 里程碑進度（展示工程紀律）
  ✅ M0 專案骨架
  ✅ M1 後端 v1（資料模型 + JWT + 文章 API）
  ✅ M2 後台 CMS
  ✅ M3 公開前台（SSG/ISR + SEO）
  ✅ M4 部署（HTTPS + 自動備份）
  ✅ M5 作品集 v2
  ✅ M6 搜尋 / 標籤 / RSS / 深色模式

  ---
