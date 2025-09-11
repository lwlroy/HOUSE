#!/bin/bash

# 三重蘆洲整合爬蟲運行腳本
# 替代原有的個別區域爬蟲

echo "🏠 開始執行三重蘆洲整合爬蟲..."
echo "=================================================="

# 設定環境變數（如果需要）
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 獲取Python執行檔路徑
PYTHON_CMD="/Users/al02425709/Desktop/HOUSE-1/.venv/bin/python"

# 檢查Python環境
if [ ! -f "$PYTHON_CMD" ]; then
    echo "❌ Python環境不存在，請先設定虛擬環境"
    exit 1
fi

# 執行三重蘆洲整合爬蟲
echo "🚀 執行三重蘆洲整合爬蟲..."
$PYTHON_CMD sanchong_luzhou_crawler.py

# 檢查執行結果
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 三重蘆洲整合爬蟲執行成功！"
    echo "📊 結果已上傳到 Notion 和儲存到本地JSON檔案"
    echo "=================================================="
else
    echo ""
    echo "❌ 三重蘆洲整合爬蟲執行失敗"
    echo "=================================================="
    exit 1
fi
