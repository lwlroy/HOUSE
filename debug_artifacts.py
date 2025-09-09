#!/usr/bin/env python3
"""
診斷 GitHub Actions Artifacts 載入問題
"""

import os
import json
from pathlib import Path

def debug_artifacts():
    """診斷 Artifacts 載入問題"""
    print("🔍 Artifacts 載入診斷")
    print("=" * 50)
    
    # 檢查目錄結構
    directories_to_check = ["./previous_data", "./data", "data", "previous_data"]
    
    for dir_path in directories_to_check:
        print(f"\n📁 檢查目錄: {dir_path}")
        if os.path.exists(dir_path):
            print(f"  ✅ 目錄存在")
            try:
                files = os.listdir(dir_path)
                print(f"  📄 檔案數量: {len(files)}")
                for file in files:
                    file_path = os.path.join(dir_path, file)
                    if os.path.isfile(file_path):
                        file_size = os.path.getsize(file_path)
                        print(f"    📋 {file} ({file_size} bytes)")
                        
                        # 如果是 JSON 檔案，嘗試載入並顯示內容摘要
                        if file.endswith('.json'):
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    data = json.load(f)
                                    if isinstance(data, list):
                                        print(f"       📊 JSON 陣列，{len(data)} 個物件")
                                        if data:
                                            first_item = data[0]
                                            if isinstance(first_item, dict):
                                                print(f"       🏠 範例物件鍵值: {list(first_item.keys())}")
                                    else:
                                        print(f"       📊 JSON 物件，類型: {type(data)}")
                            except Exception as e:
                                print(f"       ❌ JSON 解析錯誤: {e}")
            except Exception as e:
                print(f"  ❌ 無法列出檔案: {e}")
        else:
            print(f"  ❌ 目錄不存在")
    
    # 模擬 load_previous_data 邏輯
    print(f"\n🔄 模擬 load_previous_data 邏輯")
    print("-" * 30)
    
    previous_data_dirs = ["./previous_data", "data"]
    
    for data_dir in previous_data_dirs:
        if not os.path.exists(data_dir):
            print(f"❌ {data_dir} 不存在，跳過")
            continue
            
        print(f"🔍 在 {data_dir} 目錄中搜尋前一天的資料...")
        
        # 如果是 previous_data 目錄（GitHub Actions 下載的）
        if data_dir == "./previous_data":
            for district in ['luzhou', 'sanchong', 'taipei']:
                filename_prefix = f"{district}_houses"
                print(f"   🎯 搜尋 {district} 區域檔案 (前綴: {filename_prefix})")
                
                for filename in os.listdir(data_dir):
                    if filename.startswith(filename_prefix) and filename.endswith('.json'):
                        filepath = os.path.join(data_dir, filename)
                        print(f"     ✅ 找到匹配檔案: {filename}")
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                print(f"     📊 載入成功: {len(data)} 個物件")
                                return data
                        except Exception as e:
                            print(f"     ❌ 載入失敗: {str(e)}")
    
    print("📂 未找到任何前一天的資料")
    return []

if __name__ == "__main__":
    debug_artifacts()
