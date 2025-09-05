# 信義房屋物件爬蟲系統

這是一個自動化的房屋物件爬蟲系統，可以爬取信義房屋網站的房屋資訊，並自動上傳到 Notion 進行管理。

## 📋 功能特色

- 🏠 **多區域支援**：蘆洲、三重、台北
- 🔄 **自動比較**：與前一天資料比較，標示新增物件
- 📊 **Notion 整合**：自動上傳到 Notion 頁面，重複資料會自動刪除
- 💾 **本地儲存**：JSON 格式儲存到 `data/` 目錄
- 🛡️ **錯誤處理**：網路錯誤自動重試，穩定運行

## 🚀 快速開始

### 1. 環境準備

確保你的系統已安裝 Python 3.7 或更高版本：

```bash
python --version
```

### 2. 安裝依賴套件

```bash
# 建立虛擬環境（推薦）
python -m venv venv

# 啟動虛擬環境
# macOS/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# 安裝必要套件
pip install -r requirements.txt
```

### 3. Notion 設定（可選）

如果要使用 Notion 同步功能，需要設定環境變數：

```bash
export NOTION_API_TOKEN="你的_Notion_API_Token"
```

## 🎯 使用方法

### 基本指令

```bash
# 啟動虛擬環境
source venv/bin/activate

# 查看幫助訊息
python simple_luzhou_crawler.py --help
```

### 各區域爬取指令

#### 1. 蘆洲區華廈大樓
```bash
python simple_luzhou_crawler.py --district luzhou
```
- **搜尋條件**：新北市蘆洲區，華廈/大樓，3000萬以下，陽台20坪+，3-5房
- **預期結果**：約 84 個物件（5頁）

#### 2. 三重區華廈大樓
```bash
python simple_luzhou_crawler.py --district sanchong
```
- **搜尋條件**：新北市三重區，華廈/大樓，3000萬以下，陽台20坪+，3-5房
- **預期結果**：約 84 個物件（5頁）

#### 3. 台北市公寓
```bash
python simple_luzhou_crawler.py --district taipei
```
- **搜尋條件**：台北市，公寓，1-3樓，3000萬以下，陽台20坪+，3-5房
- **包含區域**：中正、大同、中山、松山、大安、萬華、信義、南港區
- **預期結果**：約 143 個物件（8頁）

#### 4. 全部區域（推薦）
```bash
python simple_luzhou_crawler.py --district all
```
- **執行順序**：蘆洲 → 三重 → 台北
- **總計物件**：約 311 個物件
- **執行時間**：約 10-15 分鐘

### 完整執行範例

```bash
# 一次性執行所有區域
source venv/bin/activate && python simple_luzhou_crawler.py --district all
```

## 📁 檔案結構

```
house/
├── README.md                          # 說明文件
├── requirements.txt                   # Python 依賴套件
├── simple_luzhou_crawler.py          # 主程式
├── venv/                             # 虛擬環境目錄
├── data/                             # 爬取資料儲存目錄
│   ├── luzhou_houses_YYYYMMDD_HHMMSS.json
│   ├── sanchong_houses_YYYYMMDD_HHMMSS.json
│   └── taipei_houses_YYYYMMDD_HHMMSS.json
├── logs/                             # 執行日誌目錄
└── src/                              # 輔助模組目錄
    ├── models/
    │   └── property.py               # 物件資料模型
    └── utils/
        ├── full_notion.py            # Notion API 整合
        └── logger.py                 # 日誌功能
```

## 📊 輸出結果

### 本地檔案
- **格式**：JSON
- **位置**：`data/` 目錄
- **命名規則**：`{區域}_houses_{日期}_{時間}.json`

### Notion 頁面
自動在 "搜屋筆記" 父頁面下創建：
- `2025/09/05 信義蘆洲華廈大樓物件清單`
- `2025/09/05 信義三重華廈大樓物件清單`
- `2025/09/05 信義台北公寓物件清單`

## ⚙️ 高級設定

### 環境變數配置

```bash
# Notion API Token（可選）
export NOTION_API_TOKEN="secret_xxxxxxxxxxxxxxxx"

# 自訂搜尋延遲（秒，預設2秒）
export CRAWL_DELAY="3"
```

### 自訂搜尋條件

如需修改搜尋條件，請編輯 `simple_luzhou_crawler.py` 中的 `districts` 配置：

```python
self.districts = {
    "luzhou": {
        "name": "蘆洲",
        "search_url": "https://www.sinyi.com.tw/buy/list/...",
        "notion_title": "信義蘆洲華廈大樓物件清單"
    },
    # ... 其他區域配置
}
```

## 🔧 常見問題

### Q: 執行時出現 "No module named 'src.utils.config'" 警告？
A: 這是正常的警告訊息，程式會自動使用簡化模式運行，不影響功能。

### Q: Notion 上傳失敗？
A: 請檢查：
1. `NOTION_API_TOKEN` 環境變數是否正確設定
2. Notion API Token 是否有效
3. 是否存在 "搜屋筆記" 父頁面

### Q: 爬取速度太慢？
A: 程式內建 2 秒延遲以避免對網站造成負擔，這是正常的禮貌性設定。

### Q: 物件數量與預期不符？
A: 網站物件數量會隨時變動，這是正常現象。

## 📝 維護說明

### 定期維護
1. **每日執行**：建議每天執行一次以獲取最新物件
2. **資料清理**：定期清理 `data/` 目錄的舊檔案
3. **依賴更新**：定期更新 Python 套件

### 套件更新
```bash
# 更新所有套件到最新版本
pip install --upgrade -r requirements.txt

# 重新生成 requirements.txt
pip freeze > requirements.txt
```

### 日誌監控
- 檢查 `logs/` 目錄下的日誌檔案
- 關注錯誤訊息和異常狀況

## 🔒 注意事項

1. **使用頻率**：請勿過於頻繁執行，建議間隔至少 1 小時
2. **網站政策**：遵守信義房屋網站的使用條款
3. **資料用途**：僅供個人研究使用，請勿用於商業用途
4. **備份**：重要資料請定期備份

## 📞 技術支援

如遇到技術問題，請檢查：
1. Python 版本是否符合要求
2. 所有依賴套件是否正確安裝
3. 網路連線是否正常
4. Notion API 設定是否正確

---

**版本資訊**：v1.0.0  
**最後更新**：2025/09/05  
**相容性**：Python 3.7+
