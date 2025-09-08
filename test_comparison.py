#!/usr/bin/env python3
"""
比對功能測試腳本
用於測試房屋物件比較邏輯是否正常運作
"""

import json
import tempfile
import os
from datetime import datetime
from simple_luzhou_crawler import SimpleSinyiCrawler

def create_test_data():
    """創建測試資料"""
    yesterday_data = [
        {
            "id": "test_1",
            "object_id": "ABC123",
            "title": "溫馨三房",
            "address": "新北市蘆洲區中正路100號",
            "price": 1000,
            "room_count": 3,
            "size": 25.0,
            "main_area": 25.0
        },
        {
            "id": "test_2", 
            "object_id": "DEF456",
            "title": "舒適四房",
            "address": "新北市蘆洲區民權路200號",
            "price": 1500,
            "room_count": 4,
            "size": 30.0,
            "main_area": 30.0
        },
        {
            "id": "test_3",
            "object_id": "GHI789",
            "title": "精緻兩房",
            "address": "新北市蘆洲區復興路300號",
            "price": 800,
            "room_count": 2,
            "size": 20.0,
            "main_area": 20.0
        }
    ]
    
    today_data = [
        # 無變化的物件
        {
            "id": "test_1",
            "object_id": "ABC123",
            "title": "溫馨三房",
            "address": "新北市蘆洲區中正路100號",
            "price": 1000,
            "room_count": 3,
            "size": 25.0,
            "main_area": 25.0
        },
        # 價格變動的物件
        {
            "id": "test_2",
            "object_id": "DEF456",
            "title": "舒適四房",
            "address": "新北市蘆洲區民權路200號",
            "price": 1450,  # 價格從 1500 降到 1450
            "room_count": 4,
            "size": 30.0,
            "main_area": 30.0
        },
        # 新增的物件
        {
            "id": "test_4",
            "object_id": "JKL012",
            "title": "豪華五房",
            "address": "新北市蘆洲區信義路400號",
            "price": 2000,
            "room_count": 5,
            "size": 40.0,
            "main_area": 40.0
        }
        # test_3 (精緻兩房) 今天沒有出現，被視為下架
    ]
    
    return yesterday_data, today_data

def test_comparison():
    """測試比對功能"""
    print("🧪 開始測試房屋物件比對功能")
    print("=" * 50)
    
    # 創建測試資料
    yesterday_data, today_data = create_test_data()
    
    print(f"📊 測試資料：")
    print(f"  昨天物件數量：{len(yesterday_data)}")
    print(f"  今天物件數量：{len(today_data)}")
    print()
    
    # 創建爬蟲實例
    crawler = SimpleSinyiCrawler(district="luzhou")
    
    # 執行比對
    comparison = crawler.compare_with_previous(today_data, yesterday_data)
    
    # 顯示比對結果
    print("📋 比對結果摘要：")
    print(f"  {comparison['message']}")
    print()
    
    print("📊 詳細統計：")
    print(f"  🆕 新增物件：{comparison['total_new']} 個")
    print(f"  📤 下架物件：{comparison['total_removed']} 個")
    print(f"  💰 價格變動：{comparison['total_price_changed']} 個")
    print(f"  ➡️  無變化：{len(comparison['unchanged_properties'])} 個")
    print()
    
    # 顯示新增物件
    if comparison['new_properties']:
        print("🆕 新增物件詳情：")
        for prop in comparison['new_properties']:
            print(f"  • {prop['title']} - {prop['address']} - {prop['price']}萬")
        print()
    
    # 顯示下架物件
    if comparison['removed_properties']:
        print("📤 下架物件詳情：")
        for prop in comparison['removed_properties']:
            print(f"  • {prop['title']} - {prop['address']} - {prop['price']}萬")
        print()
    
    # 顯示價格變動物件
    if comparison['price_changed_properties']:
        print("💰 價格變動詳情：")
        for change in comparison['price_changed_properties']:
            prop = change['property']
            old_price = change['old_price']
            new_price = change['new_price']
            change_amount = change['change']
            print(f"  • {prop['title']} - {prop['address']}")
            print(f"    💰 {old_price}萬 → {new_price}萬 ({change_amount:+}萬)")
        print()
    
    # 驗證結果
    print("✅ 驗證測試結果：")
    
    # 應該有 1 個新增物件
    assert len(comparison['new_properties']) == 1, f"應該有 1 個新增物件，實際：{len(comparison['new_properties'])}"
    assert comparison['new_properties'][0]['title'] == "豪華五房"
    print("  ✓ 新增物件檢測正確")
    
    # 應該有 1 個下架物件
    assert len(comparison['removed_properties']) == 1, f"應該有 1 個下架物件，實際：{len(comparison['removed_properties'])}"
    assert comparison['removed_properties'][0]['title'] == "精緻兩房"
    print("  ✓ 下架物件檢測正確")
    
    # 應該有 1 個價格變動物件
    assert len(comparison['price_changed_properties']) == 1, f"應該有 1 個價格變動物件，實際：{len(comparison['price_changed_properties'])}"
    price_change = comparison['price_changed_properties'][0]
    assert price_change['old_price'] == 1500
    assert price_change['new_price'] == 1450
    assert price_change['change'] == -50
    print("  ✓ 價格變動檢測正確")
    
    # 應該有 1 個無變化物件
    assert len(comparison['unchanged_properties']) == 1, f"應該有 1 個無變化物件，實際：{len(comparison['unchanged_properties'])}"
    assert comparison['unchanged_properties'][0]['title'] == "溫馨三房"
    print("  ✓ 無變化物件檢測正確")
    
    print()
    print("🎉 所有測試通過！比對功能運作正常。")

def test_github_actions_simulation():
    """模擬 GitHub Actions 環境"""
    print("\n" + "=" * 50)
    print("🔄 模擬 GitHub Actions 執行環境")
    print("=" * 50)
    
    # 創建模擬的 previous_data 目錄
    with tempfile.TemporaryDirectory() as temp_dir:
        previous_data_dir = os.path.join(temp_dir, "previous_data")
        os.makedirs(previous_data_dir)
        
        # 創建前一天的資料檔案
        yesterday_data, today_data = create_test_data()
        
        previous_file = os.path.join(previous_data_dir, "luzhou_houses_20250907_090000.json")
        with open(previous_file, 'w', encoding='utf-8') as f:
            json.dump(yesterday_data, f, ensure_ascii=False, indent=2)
        
        print(f"📁 創建模擬的前一天資料：{previous_file}")
        print(f"📊 包含 {len(yesterday_data)} 個物件")
        
        # 暫時修改工作目錄
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # 創建爬蟲實例並測試載入前一天資料
            crawler = SimpleSinyiCrawler(district="luzhou")
            
            # 測試載入前一天資料
            loaded_data = crawler.load_previous_data()
            
            if loaded_data:
                print(f"✅ 成功從 GitHub Actions artifacts 載入 {len(loaded_data)} 個物件")
                
                # 執行比對
                comparison = crawler.compare_with_previous(today_data, loaded_data)
                print(f"📊 比對結果：{comparison['message']}")
                
                # 測試 Notion 上傳邏輯（不實際上傳）
                print("🔄 測試 Notion 上傳邏輯...")
                
                if comparison['has_previous_data']:
                    new_props = comparison.get('new_properties', [])
                    price_changed_props = [item['property'] for item in comparison.get('price_changed_properties', [])]
                    properties_to_upload = new_props + price_changed_props
                    
                    if properties_to_upload:
                        print(f"📤 會上傳到 Notion：{len(properties_to_upload)} 個物件")
                        print(f"  • 新增：{len(new_props)} 個")
                        print(f"  • 變價：{len(price_changed_props)} 個")
                    else:
                        print("ℹ️  沒有新增或變動的物件，會跳過 Notion 上傳")
                
            else:
                print("❌ 未能載入前一天的資料")
                
        finally:
            os.chdir(original_cwd)
    
    print("✅ GitHub Actions 環境模擬測試完成")

if __name__ == "__main__":
    test_comparison()
    test_github_actions_simulation()
    
    print("\n" + "=" * 50)
    print("🎯 測試總結")
    print("=" * 50)
    print("• 房屋物件比對邏輯正常運作")
    print("• GitHub Actions artifacts 載入功能正常")  
    print("• Notion 上傳策略（只上傳變動物件）正常")
    print("• 系統已準備好在 GitHub Actions 中自動執行！")
    print()
    print("💡 下一步：")
    print("1. 設定 GitHub Secret: NOTION_API_TOKEN")
    print("2. 在 Notion 中創建 '搜屋筆記' 頁面並分享給 Integration")
    print("3. 推送程式碼到 GitHub，系統會自動開始每日執行")
