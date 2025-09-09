#!/usr/bin/env python3
"""
診斷台北區域比較資料問題
"""

import os
import json
from pathlib import Path
from datetime import datetime, timedelta

def check_taipei_data():
    """檢查台北區域資料"""
    print("🔍 台北區域比較資料診斷")
    print("=" * 50)
    
    # 檢查是否有台北的前一天資料
    data_dirs = ["./previous_data", "data"]
    
    for data_dir in data_dirs:
        if not os.path.exists(data_dir):
            print(f"❌ {data_dir} 目錄不存在")
            continue
            
        print(f"\n📁 檢查 {data_dir} 目錄")
        files = os.listdir(data_dir)
        
        # 尋找台北相關檔案
        taipei_files = [f for f in files if 'taipei' in f.lower() and f.endswith('.json')]
        
        print(f"🎯 台北相關檔案: {taipei_files}")
        
        for taipei_file in taipei_files:
            filepath = os.path.join(data_dir, taipei_file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"📊 {taipei_file}: {len(data)} 個物件")
                    
                    # 顯示前3個物件的摘要
                    if data:
                        print("📋 資料範例:")
                        for i, item in enumerate(data[:3], 1):
                            print(f"  {i}. {item.get('title', 'No title')[:30]}... - {item.get('price', 'No price')}萬")
                            print(f"     📍 {item.get('address', 'No address')}")
                            
                            # 檢查用於比較的關鍵欄位
                            address = item.get('address', '').strip()
                            room_count = item.get('room_count', 0)
                            main_area = item.get('main_area', item.get('size', 0))
                            key = f"{address}_{room_count}_{main_area}"
                            print(f"     🔑 比較鍵值: {key}")
                            print("")
                    
            except Exception as e:
                print(f"❌ 載入 {taipei_file} 失敗: {e}")

def simulate_taipei_comparison():
    """模擬台北區域比較邏輯"""
    print("\n🧪 模擬台北區域比較邏輯")
    print("-" * 30)
    
    def _generate_property_key(prop):
        """生成物件鍵值"""
        address = prop.get('address', '').strip()
        room_count = prop.get('room_count', 0)
        size = prop.get('size', 0)
        main_area = prop.get('main_area', size)
        return f"{address}_{room_count}_{main_area}"
    
    # 嘗試載入前一天的台北資料
    previous_data = []
    data_dirs = ["./previous_data", "data"]
    
    for data_dir in data_dirs:
        if os.path.exists(data_dir):
            files = os.listdir(data_dir)
            taipei_files = [f for f in files if 'taipei' in f.lower() and f.endswith('.json')]
            
            if taipei_files:
                taipei_file = taipei_files[0]  # 取第一個找到的
                filepath = os.path.join(data_dir, taipei_file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        previous_data = json.load(f)
                        print(f"✅ 載入前一天台北資料: {len(previous_data)} 個物件")
                        break
                except Exception as e:
                    print(f"❌ 載入失敗: {e}")
    
    if not previous_data:
        print("❌ 沒有找到前一天的台北資料")
        return
    
    # 檢查前一天資料的物件鍵值
    print("\n🔑 前一天台北物件鍵值範例:")
    for i, prop in enumerate(previous_data[:5], 1):
        key = _generate_property_key(prop)
        print(f"  {i}. {key}")
        print(f"     📍 {prop.get('address', 'No address')}")
        print(f"     💰 {prop.get('price', 'No price')}萬")
    
    print(f"\n📊 前一天台北資料統計:")
    print(f"  • 總物件數: {len(previous_data)}")
    
    # 檢查物件鍵值的唯一性
    keys = [_generate_property_key(prop) for prop in previous_data]
    unique_keys = set(keys)
    
    print(f"  • 唯一鍵值數: {len(unique_keys)}")
    
    if len(keys) != len(unique_keys):
        print(f"  ⚠️ 發現重複鍵值: {len(keys) - len(unique_keys)} 個")
        
        # 找出重複的鍵值
        key_counts = {}
        for key in keys:
            key_counts[key] = key_counts.get(key, 0) + 1
        
        duplicates = {k: v for k, v in key_counts.items() if v > 1}
        print(f"  🔍 重複鍵值: {list(duplicates.keys())[:3]}...")

def check_comparison_data_structure():
    """檢查比較資料結構"""
    print("\n📋 檢查比較資料結構規範")
    print("-" * 30)
    
    expected_fields = [
        'has_previous_data',
        'new_properties', 
        'removed_properties',
        'price_changed_properties',
        'unchanged_properties',
        'total_new',
        'total_removed', 
        'total_price_changed',
        'current_count',
        'previous_count',
        'change',
        'message'
    ]
    
    print("✅ 比較資料應包含以下欄位:")
    for field in expected_fields:
        print(f"  • {field}")
    
    print("\n💡 Notion 顯示比較資訊的條件:")
    print("  • comparison.get('has_previous_data') == True")
    print("  • comparison 不能為 None")
    print("  • 必須正確傳遞給 create_district_house_list()")

if __name__ == "__main__":
    check_taipei_data()
    simulate_taipei_comparison()
    check_comparison_data_structure()
    
    print("\n🎯 可能的問題原因:")
    print("1. 台北區域前一天資料檔案不存在或格式錯誤")
    print("2. 台北區域物件鍵值生成邏輯有問題")
    print("3. 比較資料沒有正確傳遞給 Notion")
    print("4. 台北區域的比較結果確實沒有變化（所有物件都相同）")
    
    print("\n🔧 建議檢查:")
    print("1. 查看 GitHub Actions 執行日誌中台北區域的比較資訊")
    print("2. 確認 ./previous_data/ 中是否有 taipei_houses_*.json 檔案")
    print("3. 檢查台北區域是否真的有新增或價格變動的物件")
