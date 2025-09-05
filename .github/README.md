# GitHub Actions 環境變數設置說明

## 📋 需要在 GitHub Secrets 中設置的變數

在您的 GitHub repository 中設置以下 Secrets：

1. 前往：https://github.com/lwlroy/HOUSE/settings/secrets/actions
2. 點擊 "New repository secret"
3. 添加以下變數：

### NOTION_TOKEN
- Name: `NOTION_TOKEN`
- Value: 您的 Notion Integration Token

### NOTION_DATABASE_ID (可選)
- Name: `NOTION_DATABASE_ID` 
- Value: 您的 Notion Database ID (如果需要)

## 🔧 如何獲取 Notion Token：

1. 前往：https://www.notion.so/my-integrations
2. 點擊 "New integration"
3. 設置名稱：House Crawler
4. 選擇 workspace
5. 複製 "Internal Integration Token"

## ⏰ 執行時間設置

當前設置為每天台灣時間早上 9:00 執行
如需修改時間，編輯 `.github/workflows/house-crawler.yml` 中的 cron 表達式

### Cron 時間對照：
- `0 1 * * *` = 台灣時間 09:00 (UTC+8)
- `0 13 * * *` = 台灣時間 21:00 (UTC+8)
- `0 */6 * * *` = 每 6 小時執行一次

## 🚀 手動執行

也可以在 GitHub Actions 頁面手動觸發執行
