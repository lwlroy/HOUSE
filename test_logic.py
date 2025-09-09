#!/usr/bin/env python3
"""
測試比較邏輯和 Notion 上傳決策
"""

import json
import os
from datetime import datetime

def create_mock_data():
    """創建模擬資料來測試比較邏輯"""
    
    # 模擬昨天的資料
    previous_data = [
        {
            "object_id": "obj1",
            "title": "蘆洲大樓A",
            "address": "新北市蘆洲區成功路100號",
            "price": 1500,
            "room_count": 3,
            "size": 30.5,
            "main_area": 25.0
        },
        {
            "object_id": "obj2", 
            "title": "蘆洲華廈B",
            "address": "新北市蘆洲區中山路200號",
            "price": 1200,
            "room_count": 2,
            "size": 25.0,
            "main_area": 20.0
        }
    ]
    
    # 模擬今天的資料
    current_data = [
        {
            "object_id": "obj1",
            "title": "蘆洲大樓A",
            "address": "新北市蘆洲區成功路100號", 
            "price": 1550,  # 價格變動
            "room_count": 3,
            "size": 30.5,
            "main_area": 25.0
        },
        {
            "object_id": "obj2",
            "title": "蘆洲華廈B", 
            "address": "新北市蘆洲區中山路200號",
            "price": 1200,  # 價格無變動
            "room_count": 2,
            "size": 25.0,
            "main_area": 20.0
        },
        {
            "object_id": "obj3",
            "title": "蘆洲新建案C",  # 新增物件
            "address": "新北市蘆洲區民族路300號",
            "price": 1800,
            "room_count": 4,
            "size": 40.0,
            "main_area": 35.0
        }
    ]
    
    return previous_data, current_data

def test_property_key_generation():
    """測試物件鍵值生成邏輯"""
    print("🔑 測試物件鍵值生成邏輯")
    print("-" * 30)
    
    def _generate_property_key(prop):
        """複製相同的鍵值生成邏輯"""
        address = prop.get('address', '').strip()
        room_count = prop.get('room_count', 0)
        size = prop.get('size', 0)
        main_area = prop.get('main_area', size)
        
        # 使用地址、房數、坪數作為唯一識別
        return f"{address}_{room_count}_{main_area}"
    
    previous_data, current_data = create_mock_data()
    
    print("昨天的物件鍵值:")
    for prop in previous_data:
        key = _generate_property_key(prop)
        print(f"  {prop['title']}: {key}")
    
    print("\n今天的物件鍵值:")
    for prop in current_data:
        key = _generate_property_key(prop)
        print(f"  {prop['title']}: {key}")

def test_comparison_logic():
    """測試比較邏輯"""
    print("\n📊 測試比較邏輯")
    print("-" * 30)
    
    def _generate_property_key(prop):
        """複製相同的鍵值生成邏輯"""
        address = prop.get('address', '').strip()
        room_count = prop.get('room_count', 0) 
        size = prop.get('size', 0)
        main_area = prop.get('main_area', size)
        
        return f"{address}_{room_count}_{main_area}"
    
    def compare_with_previous(current_properties, previous_data):
        """複製比較邏輯"""
        if not previous_data:
            return {
                'has_previous_data': False,
                'new_properties': current_properties,
                'removed_properties': [],
                'price_changed_properties': [],
                'unchanged_properties': [],
                'total_new': len(current_properties),
                'total_removed': 0,
                'total_price_changed': 0,
                'current_count': len(current_properties),
                'previous_count': 0,
                'message': '首次爬取，所有物件都是新的'
            }
        
        # 建立昨天的物件映射
        previous_map = {}
        for prop in previous_data:
            key = _generate_property_key(prop)
            previous_map[key] = prop
        
        # 建立今天的物件映射
        current_map = {}
        for prop in current_properties:
            key = _generate_property_key(prop)
            current_map[key] = prop
        
        # 找出新增的物件
        new_properties = []
        unchanged_properties = []
        price_changed_properties = []
        
        for key, current_prop in current_map.items():
            if key not in previous_map:
                # 新增的物件
                new_properties.append(current_prop)
            else:
                # 存在的物件，檢查價格是否變動
                previous_prop = previous_map[key]
                current_price = current_prop.get('price', 0)
                previous_price = previous_prop.get('price', 0)
                
                if abs(current_price - previous_price) > 0:  # 價格有變動
                    price_changed_properties.append({
                        'property': current_prop,
                        'old_price': previous_price,
                        'new_price': current_price,
                        'change': current_price - previous_price
                    })
                else:
                    # 價格無變動的物件
                    unchanged_properties.append(current_prop)
        
        # 找出下架的物件
        removed_properties = []
        for key, previous_prop in previous_map.items():
            if key not in current_map:
                removed_properties.append(previous_prop)
        
        # 計算變化
        change = len(current_properties) - len(previous_data)
        
        return {
            'has_previous_data': True,
            'new_properties': new_properties,
            'removed_properties': removed_properties,
            'price_changed_properties': price_changed_properties,
            'unchanged_properties': unchanged_properties,
            'total_new': len(new_properties),
            'total_removed': len(removed_properties),
            'total_price_changed': len(price_changed_properties),
            'current_count': len(current_properties),
            'previous_count': len(previous_data),
            'change': change,
            'message': f'與昨天比較：新增 {len(new_properties)} 個、下架 {len(removed_properties)} 個、變價 {len(price_changed_properties)} 個物件'
        }
    
    previous_data, current_data = create_mock_data()
    
    # 測試有前一天資料的情況
    print("情境1: 有前一天資料")
    comparison = compare_with_previous(current_data, previous_data)
    
    print(f"  has_previous_data: {comparison['has_previous_data']}")
    print(f"  新增物件數量: {comparison['total_new']}")
    print(f"  下架物件數量: {comparison['total_removed']}")
    print(f"  變價物件數量: {comparison['total_price_changed']}")
    print(f"  目前物件數量: {comparison['current_count']}")
    print(f"  前一天物件數量: {comparison['previous_count']}")
    print(f"  訊息: {comparison['message']}")
    
    if comparison['new_properties']:
        print("\n  🆕 新增物件:")
        for prop in comparison['new_properties']:
            print(f"    - {prop['title']} ({prop['price']}萬)")
    
    if comparison['price_changed_properties']:
        print("\n  💰 變價物件:")
        for change_info in comparison['price_changed_properties']:
            prop = change_info['property']
            print(f"    - {prop['title']}: {change_info['old_price']} → {change_info['new_price']}萬 ({change_info['change']:+})")
    
    # 測試沒有前一天資料的情況 
    print("\n情境2: 沒有前一天資料")
    comparison_first_run = compare_with_previous(current_data, [])
    
    print(f"  has_previous_data: {comparison_first_run['has_previous_data']}")
    print(f"  新增物件數量: {comparison_first_run['total_new']}")
    print(f"  訊息: {comparison_first_run['message']}")

def test_notion_upload_decision():
    """測試 Notion 上傳決策邏輯"""
    print("\n📝 測試 Notion 上傳決策邏輯")
    print("-" * 30)
    
    def simulate_upload_decision(properties, comparison_data):
        """模擬上傳決策邏輯"""
        print(f"比較資料調試資訊:")
        if comparison_data:
            print(f"  • has_previous_data: {comparison_data.get('has_previous_data', False)}")
            print(f"  • 新增物件數量: {len(comparison_data.get('new_properties', []))}")
            print(f"  • 價格變動物件數量: {len(comparison_data.get('price_changed_properties', []))}")
            print(f"  • 總計目前物件: {comparison_data.get('current_count', 0)}")
            print(f"  • 總計前一天物件: {comparison_data.get('previous_count', 0)}")
        else:
            print(f"  • comparison_data 為 None")
        
        # 決定要上傳的物件
        if comparison_data and comparison_data.get('has_previous_data'):
            # 如果有前一天資料，只上傳新增和價格變動的物件
            properties_to_upload = []
            
            # 新增的物件
            if comparison_data.get('new_properties'):
                properties_to_upload.extend(comparison_data['new_properties'])
                print(f"📝 將上傳 {len(comparison_data['new_properties'])} 個新增物件")
            
            # 價格變動的物件
            if comparison_data.get('price_changed_properties'):
                for change_info in comparison_data['price_changed_properties']:
                    prop = change_info['property'].copy()
                    change_amount = change_info['change']
                    change_emoji = "📈" if change_amount > 0 else "📉"
                    prop['title'] = f"{prop['title']} {change_emoji} 價格變動: {change_info['old_price']:,}→{change_info['new_price']:,}萬"
                    properties_to_upload.append(prop)
                print(f"📝 將上傳 {len(comparison_data['price_changed_properties'])} 個價格變動物件")
            
            if not properties_to_upload:
                print("✅ 沒有新增或變動的物件，Notion 筆記保持不變")
                return True
                
            print(f"📝 總共上傳 {len(properties_to_upload)} 個有變化的物件到 Notion")
        else:
            # 如果沒有前一天資料，上傳所有物件
            properties_to_upload = properties
            print(f"📝 首次執行，將上傳所有 {len(properties)} 個物件到 Notion")
        
        return properties_to_upload
    
    # 重新使用上面的比較邏輯
    def _generate_property_key(prop):
        address = prop.get('address', '').strip()
        room_count = prop.get('room_count', 0)
        size = prop.get('size', 0)
        main_area = prop.get('main_area', size)
        return f"{address}_{room_count}_{main_area}"
    
    def compare_with_previous(current_properties, previous_data):
        if not previous_data:
            return {
                'has_previous_data': False,
                'new_properties': current_properties,
                'removed_properties': [],
                'price_changed_properties': [],
                'unchanged_properties': [],
                'total_new': len(current_properties),
                'total_removed': 0,
                'total_price_changed': 0,
                'current_count': len(current_properties),
                'previous_count': 0,
                'message': '首次爬取，所有物件都是新的'
            }
        
        previous_map = {}
        for prop in previous_data:
            key = _generate_property_key(prop)
            previous_map[key] = prop
        
        current_map = {}
        for prop in current_properties:
            key = _generate_property_key(prop)
            current_map[key] = prop
        
        new_properties = []
        unchanged_properties = []
        price_changed_properties = []
        
        for key, current_prop in current_map.items():
            if key not in previous_map:
                new_properties.append(current_prop)
            else:
                previous_prop = previous_map[key]
                current_price = current_prop.get('price', 0)
                previous_price = previous_prop.get('price', 0)
                
                if abs(current_price - previous_price) > 0:
                    price_changed_properties.append({
                        'property': current_prop,
                        'old_price': previous_price,
                        'new_price': current_price,
                        'change': current_price - previous_price
                    })
                else:
                    unchanged_properties.append(current_prop)
        
        removed_properties = []
        for key, previous_prop in previous_map.items():
            if key not in current_map:
                removed_properties.append(previous_prop)
        
        change = len(current_properties) - len(previous_data)
        
        return {
            'has_previous_data': True,
            'new_properties': new_properties,
            'removed_properties': removed_properties,
            'price_changed_properties': price_changed_properties,
            'unchanged_properties': unchanged_properties,
            'total_new': len(new_properties),
            'total_removed': len(removed_properties),
            'total_price_changed': len(price_changed_properties),
            'current_count': len(current_properties),
            'previous_count': len(previous_data),
            'change': change,
            'message': f'與昨天比較：新增 {len(new_properties)} 個、下架 {len(removed_properties)} 個、變價 {len(price_changed_properties)} 個物件'
        }
    
    previous_data, current_data = create_mock_data()
    
    print("情境1: 有前一天資料的情況")
    comparison = compare_with_previous(current_data, previous_data)
    properties_to_upload = simulate_upload_decision(current_data, comparison)
    print(f"結果: 將上傳 {len(properties_to_upload)} 個物件")
    
    print("\n情境2: 沒有前一天資料的情況（首次執行）")
    comparison_first = compare_with_previous(current_data, [])
    properties_to_upload_first = simulate_upload_decision(current_data, comparison_first)
    print(f"結果: 將上傳 {len(properties_to_upload_first)} 個物件")

if __name__ == "__main__":
    print("🧪 比較邏輯測試")
    print("=" * 50)
    
    test_property_key_generation()
    test_comparison_logic()
    test_notion_upload_decision()
    
    print("\n✅ 測試完成")
