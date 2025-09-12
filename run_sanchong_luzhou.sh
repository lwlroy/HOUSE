#!/bin/bash
# 三重蘆洲爬蟲執行腳本

echo "🏠 三重蘆洲華廈大樓爬蟲"
echo "======================="

# 檢查虛擬環境
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    PYTHON_CMD="python"
elif [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    PYTHON_CMD="python"
else
    PYTHON_CMD="/Users/al02425709/Desktop/HOUSE-1/.venv/bin/python"
fi

# 檢查Python環境
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo "❌ Python環境不存在"
    exit 1
fi

echo "🚀 執行三重蘆洲爬蟲..."
$PYTHON_CMD sanchong_luzhou_crawler.py

if [ $? -eq 0 ]; then
    echo "✅ 執行成功！"
else
    echo "❌ 執行失敗"
    exit 1
fi
