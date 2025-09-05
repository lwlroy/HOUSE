#!/bin/bash
# 房屋爬蟲快速執行腳本

echo "🏠 信義房屋物件爬蟲系統"
echo "====================="
echo ""
echo "請選擇要爬取的區域："
echo "1) 蘆洲區華廈大樓"
echo "2) 三重區華廈大樓" 
echo "3) 台北市公寓"
echo "4) 全部區域（推薦）"
echo "5) 查看幫助"
echo ""
read -p "請輸入選項 (1-5): " choice

# 啟動虛擬環境
source venv/bin/activate

case $choice in
    1)
        echo "🎯 開始爬取蘆洲區華廈大樓..."
        python simple_luzhou_crawler.py --district luzhou
        ;;
    2)
        echo "🎯 開始爬取三重區華廈大樓..."
        python simple_luzhou_crawler.py --district sanchong
        ;;
    3)
        echo "🎯 開始爬取台北市公寓..."
        python simple_luzhou_crawler.py --district taipei
        ;;
    4)
        echo "🎯 開始爬取全部區域..."
        python simple_luzhou_crawler.py --district all
        ;;
    5)
        python simple_luzhou_crawler.py --help
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
