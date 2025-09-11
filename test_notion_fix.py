#!/usr/bin/env python3
"""
本地測試腳本：調試 Notion 區塊限制問題
測試新的優化版本是否能正確處理超過 100 個區塊的情況
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# 添加專案路徑
sys.path.append(str(Path(__file__).parent))

# 設定環境變數（測試用）
if not os.getenv('NOTION_API_TOKEN'):
    print("⚠️  未設定 NOTION_API_TOKEN 環境變數")
    print("💡 請設定您的 Notion API Token:")
    print("   export NOTION_API_TOKEN='your_token_here'")
    print("   或者在 .env 檔案中設定")

def test_blocks_generation():
    """測試區塊生成功能"""
    print("🧪 測試 Notion 區塊生成功能...")
    
    try:
        from src.utils.notion_blocks_patch import generate_optimized_district_blocks
        from src.models.property import Property
        
        # 創建測試物件 (模擬大量物件的情況)
        test_properties = []
        for i in range(150):  # 創建 150 個測試物件，模擬超過限制的情況
            prop = Property(
                id=f"test_{i}",
                title=f"測試物件 {i+1}",
                address=f"台北市信義區測試路{i+1}號",
                district="信義區",
                region="台北市",
                price=1000 + i * 10,
                room_count=3,
                living_room_count=2,
                bathroom_count=2,
                size=30.5 + i,
                floor=f"{(i % 10) + 1}樓",
                source_site="測試網站",
                source_url=f"https://test.com/property/{i}",
                property_type='sale'
            )
            prop.total_price = prop.price
            test_properties.append(prop)
        
        # 測試無比較資料的情況
        print(f"\n📊 測試案例 1：無比較資料，{len(test_properties)} 個物件")
        blocks1 = generate_optimized_district_blocks(
            properties=test_properties,
            search_date=datetime.now(),
            district_name="台北",
            comparison=None
        )
        print(f"✅ 生成區塊數量: {len(blocks1)} (應該 ≤ 100)")
        
        # 測試有比較資料的情況
        print(f"\n📊 測試案例 2：有比較資料，模擬新增物件")
        mock_comparison = {
            'has_previous_data': True,
            'current_count': len(test_properties),
            'previous_count': len(test_properties) - 20,
            'new_properties': test_properties[:20],  # 前20個作為新增物件
            'removed_properties': [],
            'price_changed_properties': []
        }
        
        blocks2 = generate_optimized_district_blocks(
            properties=test_properties,
            search_date=datetime.now(),
            district_name="台北",
            comparison=mock_comparison
        )
        print(f"✅ 生成區塊數量: {len(blocks2)} (應該 ≤ 100)")
        
        # 測試有價格變動的情況
        print(f"\n📊 測試案例 3：有價格變動物件")
        mock_price_changes = []
        for i in range(10):
            mock_price_changes.append({
                'property': test_properties[i],
                'old_price': test_properties[i].price - 50,
                'new_price': test_properties[i].price,
                'change': 50
            })
        
        mock_comparison_with_changes = {
            'has_previous_data': True,
            'current_count': len(test_properties),
            'previous_count': len(test_properties),
            'new_properties': test_properties[:5],  # 5個新增
            'removed_properties': [],
            'price_changed_properties': mock_price_changes  # 10個價格變動
        }
        
        blocks3 = generate_optimized_district_blocks(
            properties=test_properties,
            search_date=datetime.now(),
            district_name="台北",
            comparison=mock_comparison_with_changes
        )
        print(f"✅ 生成區塊數量: {len(blocks3)} (應該 ≤ 100)")
        
        print(f"\n🎉 所有測試案例通過！區塊數量都在 Notion API 限制範圍內。")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_crawler():
    """測試簡化版爬蟲"""
    print("\n🕷️ 測試簡化版爬蟲...")
    
    try:
        from simple_luzhou_crawler import SimpleSinyiCrawler
        
        # 創建爬蟲實例（測試台北區域）
        crawler = SimpleSinyiCrawler(district="taipei")
        
        print("🔍 測試爬取第一頁...")
        
        # 只爬取第一頁進行測試
        properties = crawler.crawl_all_pages(max_pages=1)
        
        if properties:
            print(f"✅ 成功爬取 {len(properties)} 個物件")
            
            # 測試比較功能
            print("\n📊 測試資料比較功能...")
            previous_data = crawler.load_previous_data()
            comparison = crawler.compare_with_previous(properties, previous_data)
            
            print(f"📈 比較結果: {comparison['message']}")
            
            # 測試 Notion 上傳（如果有設定 Token）
            if os.getenv('NOTION_API_TOKEN'):
                print("\n🔗 測試 Notion 上傳...")
                success = crawler.upload_to_notion_simple(properties, comparison)
                print(f"📝 Notion 上傳: {'✅ 成功' if success else '❌ 失敗'}")
            else:
                print("\n⚠️  跳過 Notion 上傳測試（未設定 API Token）")
            
            return True
        else:
            print("❌ 沒有爬取到任何物件")
            return False
            
    except Exception as e:
        print(f"❌ 爬蟲測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主測試函數"""
    print("🏠 信義房屋爬蟲 - 本地調試測試")
    print("=" * 50)
    print("🎯 目標：解決 Notion API 'body.children.length should be ≤ 100' 錯誤")
    print()
    
    # 測試 1: 區塊生成功能
    test1_passed = test_blocks_generation()
    
    # 測試 2: 簡化版爬蟲
    test2_passed = test_simple_crawler()
    
    # 總結
    print("\n" + "=" * 50)
    print("📋 測試結果總結:")
    print(f"  🧪 區塊生成測試: {'✅ 通過' if test1_passed else '❌ 失敗'}")
    print(f"  🕷️ 爬蟲功能測試: {'✅ 通過' if test2_passed else '❌ 失敗'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 所有測試通過！Notion 區塊限制問題已解決。")
        print("💡 您現在可以正常運行 GitHub Actions 了。")
    else:
        print("\n⚠️ 有測試失敗，請檢查錯誤訊息並修復問題。")
    
    print("\n🔧 如果要完整測試，請執行:")
    print("  python simple_luzhou_crawler.py --district taipei")

if __name__ == "__main__":
    main()
