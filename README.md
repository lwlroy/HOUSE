# 信義房屋物件爬蟲系統

這是一個自動化的房屋物件爬蟲系統，專門爬取信義房屋網站的房屋資訊，並自動上傳到 Notion 進行管理。

## 📋 功能特色

- 🏠 **雙區域支援**：三重蘆洲華廈大樓、台北公寓
- 🔄 **自動比較**：與前一天資料比較，標示新增物件
- 📊 **Notion 整合**：自動上傳到 Notion 頁面，重複資料會自動刪除
- 💾 **本地儲存**：JSON 格式儲存到 `data/` 目錄
- 🛡️ **錯誤處理**：網路錯誤自動重試，穩定運行
- ⏰ **GitHub Actions**：每日自動執行

## 🚀 快速開始

### 環境設定

```bash
# 1. 複製專案
git clone https://github.com/your-username/HOUSE.git
cd HOUSE

# 2. 建立虛擬環境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. 安裝依賴
pip install -r requirements.txt

# 4. 設定 Notion API Token (可選)
export NOTION_API_TOKEN="your_token_here"
```

### 執行爬蟲

```bash
# 使用互動式腳本
./run.sh

# 或直接執行個別爬蟲
python sanchong_luzhou_crawler.py          # 三重蘆洲華廈大樓
python simple_luzhou_crawler.py taipei     # 台北公寓
```

## 🎯 爬蟲說明

### 1. 三重蘆洲華廈大樓爬蟲
- **檔案**：`sanchong_luzhou_crawler.py`
- **搜尋條件**：新北市三重+蘆洲區，華廈/大樓，3000萬以下，陽台20坪+，3-5房
- **預期結果**：約 80-100 個物件

### 2. 台北公寓爬蟲
- **檔案**：`simple_luzhou_crawler.py`
- **搜尋條件**：台北市，公寓，1-3樓，3000萬以下，陽台20坪+，3-5房
- **包含區域**：中正、大同、中山、松山、大安、萬華、信義、南港區
- **預期結果**：約 140-160 個物件

## 📊 輸出結果

### 本地檔案
- **格式**：JSON
- **位置**：`data/` 目錄
- **命名規則**：`{區域}_houses_{日期}_{時間}.json`

### Notion 頁面
自動在 "搜屋筆記" 父頁面下創建：
- `2025/09/12 信義sanchong_luzhou華廈大樓物件清單`
- `2025/09/12 信義台北公寓物件清單`

## ⚙️ Notion 設定

1. 前往 [Notion Integrations](https://www.notion.so/my-integrations)
2. 創建新的 Integration
3. 複製 Integration Token
4. 在 Notion 中創建 "搜屋筆記" 頁面
5. 將 Integration 加入該頁面權限

## 🔧 GitHub Actions 設定

系統會每天自動執行，需要設定：

1. **GitHub Secret**：
   - `NOTION_API_TOKEN`：你的 Notion API Token

2. **執行時間**：
   - 每天台灣時間早上 9:00

## 📁 檔案結構

```
HOUSE-1/
├── sanchong_luzhou_crawler.py    # 三重蘆洲爬蟲
├── simple_luzhou_crawler.py      # 台北爬蟲
├── src/
│   ├── models/
│   │   └── property.py           # 物件資料模型
│   └── utils/
│       ├── full_notion.py        # Notion API 整合
│       └── notion_blocks_patch.py # Notion 區塊生成
├── .github/workflows/
│   └── daily-crawler.yml         # GitHub Actions 工作流程
├── data/                          # 爬取結果儲存目錄
├── requirements.txt               # Python 依賴套件
└── README.md                      # 說明文檔
```

## 🔒 注意事項

1. **使用頻率**：建議間隔至少 1 小時
2. **網站政策**：遵守信義房屋網站的使用條款
3. **資料用途**：僅供個人研究使用，請勿用於商業用途
4. **備份**：重要資料請定期備份

## 📞 技術支援

如遇到技術問題，請檢查：
1. Python 版本是否符合要求 (3.7+)
2. 所有依賴套件是否正確安裝
3. 網路連線是否正常
4. Notion API 設定是否正確

---

**版本資訊**：v2.0.0  
**最後更新**：2025/09/12  
**相容性**：Python 3.7+
