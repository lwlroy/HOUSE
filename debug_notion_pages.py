#!/usr/bin/env python3
"""
Notion 頁面調試腳本
檢查 Notion 中的頁面結構和內容
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# 加入專案路徑
sys.path.append(str(Path(__file__).parent))

try:
    from src.utils.full_notion import create_full_notion_client
except ImportError as e:
    print(f"❌ 無法載入 Notion 功能: {e}")
    sys.exit(1)


def debug_notion_pages():
    """調試 Notion 頁面結構"""
    notion_token = os.getenv('NOTION_API_TOKEN', os.getenv('NOTION_TOKEN'))
    
    if not notion_token:
        print("❌ 未設定 NOTION_API_TOKEN")
        return
    
    client = create_full_notion_client(notion_token)
    
    if not client.test_connection():
        print("❌ Notion API 連接失敗")
        return
    
    print("🔍 開始調試 Notion 頁面結構...")
    print("=" * 60)
    
    # 1. 尋找父頁面
    print("🔍 尋找父頁面...")
    parent_page = client.find_parent_page("搜屋筆記")
    
    if not parent_page:
        print("❌ 找不到父頁面 '搜屋筆記'")
        return
    
    parent_page_id = parent_page["id"]
    parent_title = client._extract_page_title(parent_page)
    print(f"✅ 找到父頁面: {parent_title} (ID: {parent_page_id})")
    
    # 2. 檢查今天的日期頁面
    today = datetime.now()
    date_str = today.strftime('%Y/%m/%d')
    print(f"\n🔍 檢查今天的日期頁面: {date_str}")
    
    # 獲取父頁面的所有子頁面
    children_data = client._make_request(f"{client.base_url}/blocks/{parent_page_id}/children")
    
    if children_data.get("error"):
        print(f"❌ 獲取子頁面失敗: {children_data.get('message')}")
        return
    
    children = children_data.get("results", [])
    print(f"📄 父頁面共有 {len(children)} 個子頁面")
    
    # 3. 列出所有子頁面
    print(f"\n📝 所有子頁面列表:")
    today_pages = []
    
    for i, child in enumerate(children, 1):
        if child.get("type") == "child_page":
            child_title = child.get("child_page", {}).get("title", "")
            child_id = child["id"]
            print(f"  {i}. {child_title} (ID: {child_id})")
            
            # 檢查是否為今天的頁面
            if date_str in child_title:
                today_pages.append(child)
    
    # 4. 檢查今天的頁面詳情
    if today_pages:
        print(f"\n🎯 找到 {len(today_pages)} 個今天的頁面:")
        
        for page in today_pages:
            page_title = page.get("child_page", {}).get("title", "")
            page_id = page["id"]
            print(f"\n📋 頁面: {page_title}")
            print(f"   ID: {page_id}")
            
            # 獲取該頁面的子頁面（區域物件清單）
            page_children_data = client._make_request(f"{client.base_url}/blocks/{page_id}/children")
            
            if not page_children_data.get("error"):
                page_children = page_children_data.get("results", [])
                district_pages = [child for child in page_children if child.get("type") == "child_page"]
                
                print(f"   📊 包含 {len(district_pages)} 個區域物件清單:")
                
                for district_page in district_pages:
                    district_title = district_page.get("child_page", {}).get("title", "")
                    district_id = district_page["id"]
                    print(f"     • {district_title} (ID: {district_id})")
                    
                    # 檢查該區域頁面的內容
                    district_content = client._make_request(f"{client.base_url}/blocks/{district_id}/children")
                    if not district_content.get("error"):
                        content_blocks = district_content.get("results", [])
                        print(f"       📝 包含 {len(content_blocks)} 個內容區塊")
                    else:
                        print(f"       ❌ 無法獲取內容: {district_content.get('message')}")
            else:
                print(f"   ❌ 無法獲取子頁面: {page_children_data.get('message')}")
    else:
        print(f"\n⚠️ 沒有找到今天 ({date_str}) 的頁面")
    
    # 5. 檢查是否有重複頁面問題
    print(f"\n🔍 檢查重複頁面...")
    duplicate_count = {}
    
    for child in children:
        if child.get("type") == "child_page":
            child_title = child.get("child_page", {}).get("title", "")
            if child_title in duplicate_count:
                duplicate_count[child_title] += 1
            else:
                duplicate_count[child_title] = 1
    
    duplicates = {title: count for title, count in duplicate_count.items() if count > 1}
    
    if duplicates:
        print("⚠️ 發現重複頁面:")
        for title, count in duplicates.items():
            print(f"   • '{title}' 重複 {count} 次")
    else:
        print("✅ 沒有重複頁面")
    
    print("\n" + "=" * 60)
    print("🎉 Notion 頁面調試完成")


if __name__ == "__main__":
    debug_notion_pages()
