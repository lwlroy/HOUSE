#!/bin/bash
# 房屋爬蟲執行腳本

echo "🏠 信義房屋物件爬蟲系統"
echo "====================="
echo ""
echo "請選擇要執行的爬蟲："
echo "1) 三重蘆洲華廈大樓"
echo "2) 台北市公寓"
echo "3) 全部執行"
echo ""
read -p "請輸入選項 (1-3): " choice

# 檢查虛擬環境
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
elif [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "⚠️ 未找到虛擬環境，使用系統Python"
fi

case $choice in
    1)
        echo "🎯 執行三重蘆洲華廈大樓爬蟲..."
        python sanchong_luzhou_crawler.py
        ;;
    2)
        #!/bin/bash

# 啟動台北爬蟲
echo "� 啟動台北公寓爬蟲..."

echo "📋 檢查依賴..."
pip install -r requirements.txt

echo "🎯 開始爬取台北區域..."
python taipei_crawler.py taipei

echo "✅ 台北區域完成"
        ;;
    3)
        echo "🎯 執行全部爬蟲..."
        python sanchong_luzhou_crawler.py
        python simple_luzhou_crawler.py --district taipei
        ;;
    *)
        echo "❌ 無效的選項"
        exit 1
        ;;
esac

echo ""
echo "✅ 執行完成！"
echo "📁 資料已儲存到 data/ 目錄"
echo "🔗 Notion 頁面已更新（如有設定）"
