# GitHub Actions 自動化設定指南

## 📋 功能說明

這個 GitHub Actions workflow 會每天自動執行房屋爬蟲，並與前一天的資料進行比較，**只在 Notion 中記錄新增和變動的物件**。

## 🔧 設定步驟

### 1. 設定 GitHub Secrets

在您的 GitHub 倉庫中設定以下 Secret：

1. 進入倉庫設定：`Settings` → `Secrets and variables` → `Actions`
2. 點擊 `New repository secret`
3. 設定以下 Secret：

| Secret 名稱 | 值 | 說明 |
|------------|----|----- |
| `NOTION_API_TOKEN` | `secret_xxxxxxxxxxxxx` | 您的 Notion Integration Token |

1. 前往 [Notion Integrations](https://www.notion.so/my-integrations)
2. 點擊 `+ New integration`
3. 填寫基本資訊：
   - **Name**: `House Crawler`
   - **Associated workspace**: 選擇您的工作區
   - **Type**: `Internal`
4. 點擊 `Submit` 創建
5. 複製 `Internal Integration Token`（以 `secret_` 開頭）
6. 將此 Token 設定為 GitHub Secret `NOTION_API_TOKEN`

### 3. 設定 Notion 頁面權限

1. 在 Notion 中創建一個名為 `搜屋筆記` 的頁面（或使用現有頁面）
2. 點擊頁面右上角的 `Share` 按鈕
3. 點擊 `Invite` 並搜尋您剛創建的 Integration 名稱
4. 給予 `Can edit` 權限
5. 點擊 `Invite`

## ⚙️ 執行策略

### 自動執行時間
- **每日執行**：台灣時間早上 9:00（UTC 01:00）
- **手動觸發**：可在 Actions 頁面手動執行

### 資料比較邏輯
1. **第一次執行**：上傳所有找到的物件
2. **後續執行**：
   - 下載前一天的資料（從 GitHub Actions artifacts）
   - 與今天的資料比較
   - **只上傳新增和價格變動的物件到 Notion**
   - 完整資料仍會儲存為 artifacts

### 比較標準
物件被視為相同的條件：
- 相同地址
- 相同房間數
- 相同坪數

如果以上條件相同但價格不同，會被標記為「價格變動」。

## 📊 Notion 頁面結構

```
搜屋筆記/
├── 2025/09/08/
│   ├── 信義蘆洲華廈大樓物件清單
│   ├── 信義三重華廈大樓物件清單
│   └── 信義台北公寓物件清單
└── 2025/09/09/
    ├── 信義蘆洲華廈大樓物件清單
    ├── 信義三重華廈大樓物件清單
    └── 信義台北公寓物件清單
```

每個區域清單只會包含：
- 🆕 **新增物件**：昨天沒有的物件
- 💰 **價格變動**：價格有變化的物件
- 📊 **變化摘要**：與前一天的比較統計

## 🔍 監控和除錯

### 查看執行結果
1. 進入 GitHub 倉庫的 `Actions` 頁面
2. 點擊最新的 `Daily House Crawler` 執行
3. 查看每個步驟的日誌輸出

### 常見問題排除

#### 1. 第一次執行顯示 "未找到前一天的資料"
- **正常現象**：第一次執行時沒有前一天的資料
- **結果**：會上傳所有找到的物件

#### 2. Notion 上傳失敗
檢查項目：
- GitHub Secret `NOTION_API_TOKEN` 是否正確設定
- Notion Integration 是否有 `搜屋筆記` 頁面的編輯權限
- Token 是否過期

#### 3. 找不到新增物件但實際有新增
可能原因：
- 物件的地址、房數、坪數完全相同
- 需要檢查比較邏輯的精確度

### 手動觸發測試
1. 進入 `Actions` 頁面
2. 點擊 `Daily House Crawler`
3. 點擊 `Run workflow`
4. 選擇分支（通常是 `main`）
5. 點擊 `Run workflow` 按鈕

## 📁 資料保存

### GitHub Actions Artifacts
- **保存期限**：7 天
- **用途**：用於次日比較
- **格式**：JSON 檔案
- **路徑**：`./data/` 目錄

## 💡 重要提醒

### ✅ 優勢
- **節省 Notion 空間**：只記錄變化，不會累積大量重複資料
- **關注重點**：突出新增和變動的物件
- **自動化**：無需手動干預，每天自動執行
- **歷史追蹤**：可以看到房屋市場的變化趨勢

### ⚠️ 注意事項
- 第一次執行會上傳所有物件
- 如果物件的地址、房數、坪數完全相同，會被視為同一物件
- Notion 中只會看到有變化的物件，完整資料仍保存在 GitHub Artifacts 中

1. 前往 GitHub 倉庫的 `Actions` 頁面
2. 選擇 `Daily House Crawler` 工作流程
3. 點擊 `Run workflow` 按鈕
4. 選擇分支並執行

## 📁 資料結構

```
Artifacts (GitHub Actions):
├── house-data/
│   ├── luzhou_houses_YYYYMMDD_HHMMSS.json
│   ├── sanchong_houses_YYYYMMDD_HHMMSS.json
│   └── taipei_houses_YYYYMMDD_HHMMSS.json

Notion 結構:
搜屋筆記/
├── YYYY/MM/DD/
│   ├── 信義蘆洲華廈大樓物件清單 (僅新增/變價)
│   ├── 信義三重華廈大樓物件清單 (僅新增/變價)
│   └── 信義台北公寓物件清單 (僅新增/變價)
```

## ⚠️ 注意事項

1. **首次執行**: 會上傳所有物件到 Notion
2. **Artifacts 保留**: 僅保留 7 天，超過會自動刪除
3. **時區設定**: 已設定為台灣時間早上 9:00 執行
4. **錯誤處理**: 首次執行時找不到前一天資料是正常的

## 🛠️ 故障排除

### 如果 Notion 上傳失敗
1. 檢查 `NOTION_API_TOKEN` 是否正確設定
2. 確認 Notion Integration 有權限存取「搜屋筆記」頁面
3. 檢查 Actions 執行日誌中的錯誤訊息

### 如果找不到前一天資料
- 第一次執行時這是正常的
- 確認前一次執行有成功儲存 Artifacts
- 檢查 Artifacts 保留期間設定

### 手動重置
如果需要重置比對基準，可以：
1. 刪除 GitHub Artifacts 中的 house-data
2. 手動執行一次工作流程作為新基準
