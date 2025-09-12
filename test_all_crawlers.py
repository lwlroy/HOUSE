#!/usr/bin/env python3
"""
模擬 GitHub Actions 執行環境測試
"""

import os
import sys
from pathlib import Path

# 設定環境
os.environ['PYTHONPATH'] = str(Path(__file__).parent)

def test_all_crawlers():
    """測試所有爬蟲的執行"""
    print("🧪 開始測試所有爬蟲...")
    print("=" * 60)
    
    # 1. 測試三重蘆洲整合爬蟲
    print("🏠 測試三重蘆洲整合爬蟲...")
    try:
        import subprocess
        result = subprocess.run([
            sys.executable, 'sanchong_luzhou_crawler.py'
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ 三重蘆洲整合爬蟲執行成功")
            print("📄 輸出摘要:")
            lines = result.stdout.split('\n')
            for line in lines:
                if '📊' in line or '✅' in line or '❌' in line or '🎉' in line:
                    print(f"   {line}")
        else:
            print("❌ 三重蘆洲整合爬蟲執行失敗")
            print("錯誤輸出:")
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ 三重蘆洲整合爬蟲測試異常: {e}")
    
    print("\n" + "-" * 40 + "\n")
    
    # 2. 測試台北公寓爬蟲
    print("🏢 測試台北公寓爬蟲...")
    try:
        result = subprocess.run([
            sys.executable, 'simple_luzhou_crawler.py', '--district', 'taipei'
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ 台北公寓爬蟲執行成功")
            print("📄 輸出摘要:")
            lines = result.stdout.split('\n')
            for line in lines:
                if '📊' in line or '✅' in line or '❌' in line or '🎉' in line:
                    print(f"   {line}")
        else:
            print("❌ 台北公寓爬蟲執行失敗")
            print("錯誤輸出:")
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ 台北公寓爬蟲測試異常: {e}")
    
    print("\n" + "-" * 40 + "\n")
    
    # 3. 測試原始的全部爬蟲（用於對比）
    print("🔄 測試原始的全部爬蟲（用於對比）...")
    try:
        result = subprocess.run([
            sys.executable, 'simple_luzhou_crawler.py', '--district', 'all'
        ], capture_output=True, text=True, timeout=600)
        
        if result.returncode == 0:
            print("✅ 原始全部爬蟲執行成功")
            print("📄 輸出摘要:")
            lines = result.stdout.split('\n')
            for line in lines:
                if '📊' in line or '✅' in line or '❌' in line or '🎉' in line or '🎯 開始爬取' in line:
                    print(f"   {line}")
        else:
            print("❌ 原始全部爬蟲執行失敗")
            print("錯誤輸出:")
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ 原始全部爬蟲測試異常: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 所有測試完成")

if __name__ == "__main__":
    test_all_crawlers()
