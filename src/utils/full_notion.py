"""
完整版 Notion API 整合
能夠真正創建 Notion 頁面
"""

import json
import urllib.request
import urllib.parse
from datetime import datetime
from typing import List, Dict, Any, Optional

from ..models.property import Property


class FullNotionClient:
    """完整版 Notion API 客戶端"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
    
    def _make_request(self, url: str, method: str = "GET", data: Dict = None) -> Dict:
        """發送HTTP請求"""
        try:
            req = urllib.request.Request(url, headers=self.headers)
            req.get_method = lambda: method
            
            if data:
                req.data = json.dumps(data).encode('utf-8')
            
            with urllib.request.urlopen(req) as response:
                response_data = response.read().decode('utf-8')
                return json.loads(response_data)
                
        except urllib.error.HTTPError as e:
            error_data = e.read().decode('utf-8')
            print(f"HTTP錯誤 {e.code}: {error_data}")
            return {"error": True, "code": e.code, "message": error_data}
        except Exception as e:
            print(f"請求失敗: {str(e)}")
            return {"error": True, "message": str(e)}
    
    def test_connection(self) -> bool:
        """測試 API 連接"""
        try:
            result = self._make_request(f"{self.base_url}/users/me")
            if not result.get("error"):
                print(f"✅ Notion API 連接成功，用戶: {result.get('name', 'Unknown')}")
                return True
            else:
                print(f"❌ Notion API 連接失敗: {result.get('message', 'Unknown error')}")
                return False
        except Exception as e:
            print(f"❌ Notion API 測試失敗: {str(e)}")
            return False
    
    def search_pages(self, query: str = "") -> List[Dict]:
        """搜尋可用的頁面"""
        try:
            search_data = {
                "query": query,
                "filter": {
                    "property": "object",
                    "value": "page"
                }
            }
            
            result = self._make_request(f"{self.base_url}/search", "POST", search_data)
            
            if not result.get("error"):
                pages = result.get("results", [])
                print(f"✅ 找到 {len(pages)} 個可存取的頁面")
                return pages
            else:
                print(f"❌ 搜尋頁面失敗: {result.get('message')}")
                return []
                
        except Exception as e:
            print(f"❌ 搜尋頁面時發生錯誤: {str(e)}")
            return []
    
    def find_parent_page(self, target_title: str = "搜屋筆記") -> Optional[Dict]:
        """尋找指定名稱的父頁面"""
        try:
            pages = self.search_pages(target_title)
            
            for page in pages:
                page_title = self._extract_page_title(page)
                if target_title in page_title or page_title in target_title:
                    print(f"✅ 找到父頁面: {page_title}")
                    return page
            
            # 如果找不到，嘗試不指定查詢詞搜尋所有頁面
            if target_title != "":
                all_pages = self.search_pages("")
                for page in all_pages:
                    page_title = self._extract_page_title(page)
                    if target_title in page_title or page_title in target_title:
                        print(f"✅ 找到父頁面: {page_title}")
                        return page
            
            print(f"❌ 找不到 '{target_title}' 頁面")
            return None
            
        except Exception as e:
            print(f"❌ 尋找父頁面時發生錯誤: {str(e)}")
            return None
    
    def find_or_create_date_page(self, parent_page_id: str, date_str: str) -> Optional[str]:
        """尋找或創建日期頁面"""
        try:
            # 獲取父頁面的子頁面
            children_data = self._make_request(f"{self.base_url}/blocks/{parent_page_id}/children")
            
            if children_data.get("error"):
                print(f"❌ 獲取子頁面失敗: {children_data.get('message')}")
                return None
            
            children = children_data.get("results", [])
            
            # 尋找現有的日期頁面
            for child in children:
                if child.get("type") == "child_page":
                    child_title = child.get("child_page", {}).get("title", "")
                    if child_title == date_str:
                        print(f"✅ 找到現有日期頁面: {date_str}")
                        return child["id"]
            
            # 如果沒找到，則創建新的日期頁面
            print(f"📅 創建新的日期頁面: {date_str}")
            date_page_data = {
                "parent": {"type": "page_id", "page_id": parent_page_id},
                "properties": {
                    "title": {
                        "title": [
                            {
                                "text": {
                                    "content": date_str
                                }
                            }
                        ]
                    }
                },
                "children": [
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": f"📅 {date_str} 的搜屋記錄"}
                                }
                            ]
                        }
                    }
                ]
            }
            
            result = self._make_request(f"{self.base_url}/pages", "POST", date_page_data)
            
            if not result.get("error"):
                date_page_id = result["id"]
                print(f"✅ 成功創建日期頁面: {date_str}")
                return date_page_id
            else:
                print(f"❌ 創建日期頁面失敗: {result.get('message')}")
                return None
                
        except Exception as e:
            print(f"❌ 處理日期頁面時發生錯誤: {str(e)}")
            return None

    def find_duplicate_pages(self, parent_page_id: str, date_str: str, district_name: str = None) -> List[Dict]:
        """尋找同一天同一區域的重複頁面"""
        try:
            # 獲取父頁面的子頁面
            children_data = self._make_request(f"{self.base_url}/blocks/{parent_page_id}/children")
            
            if children_data.get("error"):
                print(f"❌ 獲取子頁面失敗: {children_data.get('message')}")
                return []
            
            duplicate_pages = []
            children = children_data.get("results", [])
            
            print(f"🔍 尋找重複頁面: 日期={date_str}, 區域={district_name}")
            
            for child in children:
                if child.get("type") == "child_page":
                    child_title = child.get("child_page", {}).get("title", "")
                    # 檢查是否包含同一天的日期
                    if date_str in child_title:
                        # 如果指定了區域，則必須同時匹配區域名稱
                        if district_name:
                            # 更靈活的匹配邏輯：檢查是否包含 "信義{區域名稱}" 和 "物件清單"
                            if f"信義{district_name}" in child_title and "物件清單" in child_title:
                                # 獲取完整的頁面信息
                                page_data = self._make_request(f"{self.base_url}/pages/{child['id']}")
                                if not page_data.get("error"):
                                    duplicate_pages.append(page_data)
                                    print(f"🔍 找到同日同區域頁面: {child_title}")
                            else:
                                print(f"ℹ️  同日期但不同區域，保留: {child_title}")
                        else:
                            # 如果沒有指定區域，則匹配所有同日期頁面（保持舊行為）
                            page_data = self._make_request(f"{self.base_url}/pages/{child['id']}")
                            if not page_data.get("error"):
                                duplicate_pages.append(page_data)
                                print(f"🔍 找到同日頁面: {child_title}")
            
            if duplicate_pages:
                print(f"📝 共找到 {len(duplicate_pages)} 個需要刪除的重複頁面")
            else:
                print(f"ℹ️  沒有找到重複頁面 (日期: {date_str}, 區域: {district_name})")
            
            return duplicate_pages
            
        except Exception as e:
            print(f"❌ 尋找重複頁面時發生錯誤: {str(e)}")
            return []
    
    def delete_page(self, page_id: str) -> bool:
        """刪除頁面（實際上是歸檔）"""
        try:
            archive_data = {
                "archived": True
            }
            
            result = self._make_request(f"{self.base_url}/pages/{page_id}", "PATCH", archive_data)
            
            if not result.get("error"):
                print(f"✅ 成功刪除頁面: {page_id}")
                return True
            else:
                print(f"❌ 刪除頁面失敗: {result.get('message')}")
                return False
                
        except Exception as e:
            print(f"❌ 刪除頁面時發生錯誤: {str(e)}")
            return False
    
    def create_page_in_workspace(self, title: str, content_blocks: List[Dict]) -> Optional[str]:
        """直接在工作區創建頁面"""
        try:
            page_data = {
                "parent": {"type": "page_id", "page_id": ""},  # 空的表示工作區根目錄
                "properties": {
                    "title": {
                        "title": [
                            {
                                "text": {
                                    "content": title
                                }
                            }
                        ]
                    }
                },
                "children": content_blocks
            }
            
            result = self._make_request(f"{self.base_url}/pages", "POST", page_data)
            
            if not result.get("error"):
                page_url = result.get("url", "")
                print(f"✅ 成功創建頁面: {title}")
                print(f"🔗 頁面連結: {page_url}")
                return page_url
            else:
                print(f"❌ 創建頁面失敗: {result.get('message')}")
                return None
                
        except Exception as e:
            print(f"❌ 創建頁面時發生錯誤: {str(e)}")
            return None
    
    def try_create_in_existing_page(self, parent_page_id: str, title: str, content_blocks: List[Dict]) -> Optional[str]:
        """在現有頁面下創建子頁面"""
        try:
            page_data = {
                "parent": {"type": "page_id", "page_id": parent_page_id},
                "properties": {
                    "title": {
                        "title": [
                            {
                                "text": {
                                    "content": title
                                }
                            }
                        ]
                    }
                },
                "children": content_blocks
            }
            
            result = self._make_request(f"{self.base_url}/pages", "POST", page_data)
            
            if not result.get("error"):
                page_url = result.get("url", "")
                print(f"✅ 成功在父頁面下創建: {title}")
                print(f"🔗 頁面連結: {page_url}")
                return page_url
            else:
                print(f"❌ 在父頁面創建失敗: {result.get('message')}")
                return None
                
        except Exception as e:
            print(f"❌ 在父頁面創建時發生錯誤: {str(e)}")
            return None
    
    def create_district_house_list(self, properties: List[Property], search_date: datetime, district_name: str, comparison: Dict = None) -> bool:
        """創建區域物件清單（新的層級結構）"""
        try:
            date_str = search_date.strftime('%Y/%m/%d')
            
            # 根據區域名稱決定標題
            district_map = {
                'luzhou': '蘆洲',
                'sanchong': '三重', 
                'taipei': '台北'
            }
            
            district_chinese = district_map.get(district_name, district_name)
            
            # 決定物件類型
            property_type = "公寓" if district_name == 'taipei' else "華廈大樓"
            
            # 生成物件清單標題
            list_title = f"{date_str} 信義{district_chinese}{property_type}物件清單"
            
            print(f"🎯 開始創建區域物件清單: {list_title}")
            
            # 1. 尋找或創建父頁面 "搜屋筆記"
            parent_page = self.find_parent_page("搜屋筆記")
            
            if not parent_page:
                # 嘗試使用第一個可用頁面
                all_pages = self.search_pages("")
                if all_pages:
                    parent_page = all_pages[0]
                    print(f"⚠️  使用第一個可用頁面作為父頁面: {self._extract_page_title(parent_page)}")
                else:
                    print("❌ 找不到任何可用的父頁面")
                    return False
            
            parent_page_id = parent_page["id"]
            
            # 2. 尋找或創建日期頁面
            date_page_id = self.find_or_create_date_page(parent_page_id, date_str)
            if not date_page_id:
                print("❌ 無法創建或找到日期頁面")
                return False
            
            # 3. 檢查並刪除同一天同區域的舊清單
            duplicate_pages = self.find_duplicate_pages(date_page_id, date_str, district_chinese)
            
            if duplicate_pages:
                print(f"🗑️  發現 {len(duplicate_pages)} 個同日期同區域({district_chinese})的舊筆記，準備刪除...")
                for old_page in duplicate_pages:
                    old_title = self._extract_page_title(old_page)
                    if self.delete_page(old_page["id"]):
                        print(f"✅ 已刪除舊筆記: {old_title}")
                    else:
                        print(f"❌ 刪除失敗: {old_title}")
            
            # 4. 生成新的內容塊
            content_blocks = self._generate_district_blocks(properties, search_date, district_chinese, comparison)
            
            # 5. 在日期頁面下創建新的區域物件清單
            page_url = self.try_create_in_existing_page(date_page_id, list_title, content_blocks)
            
            if page_url:
                print(f"✅ 成功創建: {list_title}")
                print(f"🔗 頁面連結: {page_url}")
                return True
            else:
                print(f"❌ 創建區域物件清單失敗")
                return False
                
        except Exception as e:
            print(f"❌ 創建區域物件清單時發生錯誤: {str(e)}")
            return False

    def create_daily_house_note(self, properties: List[Property], search_date: datetime, comparison: Dict = None, auto_mode: bool = False) -> bool:
        """創建每日搜屋筆記（改進版，保持向後兼容）"""
        try:
            # 生成標題
            title = f"{search_date.strftime('%Y/%m/%d')} 搜屋筆記"
            date_str = search_date.strftime('%Y/%m/%d')
            
            # 1. 尋找或創建父頁面 "搜屋筆記"
            parent_page = self.find_parent_page("搜屋筆記")
            
            if not parent_page:
                # 嘗試使用第一個可用頁面
                all_pages = self.search_pages("")
                if all_pages:
                    parent_page = all_pages[0]
                    print(f"⚠️  使用第一個可用頁面作為父頁面: {self._extract_page_title(parent_page)}")
                else:
                    print("❌ 找不到任何可用的父頁面")
                    return False
            
            parent_page_id = parent_page["id"]
            
            # 2. 檢查並刪除同一天的舊筆記
            duplicate_pages = self.find_duplicate_pages(parent_page_id, date_str)
            
            if duplicate_pages:
                print(f"🗑️  發現 {len(duplicate_pages)} 個同日期的舊筆記，準備刪除...")
                for old_page in duplicate_pages:
                    old_title = self._extract_page_title(old_page)
                    if self.delete_page(old_page["id"]):
                        print(f"✅ 已刪除舊筆記: {old_title}")
                    else:
                        print(f"❌ 刪除失敗: {old_title}")
            
            # 3. 生成新的內容塊
            content_blocks = self._generate_notion_blocks(properties, search_date, comparison)
            
            # 4. 在父頁面下創建新筆記
            page_url = self.try_create_in_existing_page(parent_page_id, title, content_blocks)
            
            if page_url:
                print(f"✅ 成功創建每日筆記: {title}")
                print(f"🔗 頁面連結: {page_url}")
                return True
            else:
                print(f"❌ 創建每日筆記失敗")
                return False
                
        except Exception as e:
            print(f"❌ 創建每日筆記時發生錯誤: {str(e)}")
            return False
    
    def _extract_page_title(self, page: Dict) -> str:
        """提取頁面標題"""
        try:
            properties = page.get("properties", {})
            title_prop = properties.get("title") or properties.get("Name") or properties.get("名稱")
            
            if title_prop and title_prop.get("title"):
                return title_prop["title"][0]["text"]["content"]
            
            return "未命名頁面"
        except:
            return "未命名頁面"
    
    def _generate_district_blocks(self, properties: List[Property], search_date: datetime, district_name: str, comparison: Dict = None) -> List[Dict]:
        """生成區域物件清單的 Notion 頁面內容塊"""
        blocks = []
        
        # 區域標題和搜尋條件
        property_type = "公寓" if district_name == '台北' else "華廈大樓"
        search_url = self._get_search_url(district_name)
        
        blocks.append({
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": f"🎯 {district_name}區 {property_type} 搜尋條件："},
                    },
                    {
                        "type": "text",
                        "text": {
                            "content": "點擊查看搜尋頁面",
                            "link": {"url": search_url}
                        },
                        "annotations": {"color": "blue", "underline": True}
                    }
                ],
                "icon": {"emoji": "🎯"}
            }
        })
        
        # 如果有比較資料，顯示變化摘要
        if comparison and comparison.get('has_previous_data'):
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "📊 與昨日比較"}
                        }
                    ]
                }
            })
            
            # 變化摘要
            change = comparison['current_count'] - comparison['previous_count']
            change_text = ""
            if change > 0:
                change_text = f"📈 淨增加 +{change} 筆"
            elif change < 0:
                change_text = f"📉 淨減少 {abs(change)} 筆"
            else:
                change_text = "➡️ 數量相同"
            
            summary_text = f"""昨日物件：{comparison['previous_count']} 筆
今日物件：{comparison['current_count']} 筆
{change_text}"""
            
            if comparison['new_properties']:
                summary_text += f"\n🆕 新增物件：{len(comparison['new_properties'])} 筆"
            
            if comparison['removed_properties']:
                summary_text += f"\n📤 下架物件：{len(comparison['removed_properties'])} 筆"
            
            if comparison['price_changed_properties']:
                summary_text += f"\n💰 價格變動：{len(comparison['price_changed_properties'])} 筆"
            
            blocks.append({
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": summary_text}
                        }
                    ],
                    "icon": {"emoji": "📊"}
                }
            })
        
        # 搜尋摘要
        if properties:
            stats = self._calculate_stats(properties)
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": f"📋 {district_name}區搜尋摘要"}
                        }
                    ]
                }
            })
            
            summary_text = f"""找到物件：{len(properties)} 筆
平均價格：{stats.get('avg_price', 0):,.0f} 萬元
平均坪數：{stats.get('avg_size', 0):.1f} 坪
價格區間：{stats.get('min_price', 0):,} - {stats.get('max_price', 0):,} 萬元"""
            
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": summary_text}
                        }
                    ]
                }
            })
        
        # 如果有變化，先顯示新增和變動的物件
        if comparison and comparison.get('has_previous_data'):
            self._add_comparison_sections(blocks, comparison)
        
        # 物件詳情
        blocks.append({
            "object": "block",
            "type": "heading_2", 
            "heading_2": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": f"🏘️ {district_name}區所有物件詳情"}
                    }
                ]
            }
        })
        
        for i, prop in enumerate(properties, 1):
            # 檢查是否為新增物件
            is_new = False
            if comparison and comparison.get('new_properties'):
                for new_prop in comparison['new_properties']:
                    if self._properties_match(prop, new_prop):
                        is_new = True
                        break
            
            # 物件標題（新增物件標註）
            title_text = f"🏠 物件 {i}: {prop.title}"
            if is_new:
                title_text += " 🆕"
            
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": title_text}
                        }
                    ]
                }
            })
            
            # 物件詳細資訊
            info_text = f"""📍 地址：{prop.address}
💰 總價：{prop.total_price:,} 萬元"""
            
            if prop.unit_price:
                info_text += f" (單價: {prop.unit_price:.1f} 萬/坪)"
            
            info_text += f"""
🏢 房型：{prop.room_count}房{prop.living_room_count}廳{prop.bathroom_count}衛
📐 坪數：{prop.size} 坪"""
            
            if prop.main_area and prop.main_area != prop.size:
                info_text += f" (主建物: {prop.main_area} 坪)"
            
            info_text += f"\n🏗️ 樓層：{prop.floor}"
            if prop.total_floors:
                info_text += f"/{prop.total_floors}樓"
            
            if prop.age:
                info_text += f"\n📅 屋齡：{prop.age} 年"
            
            if prop.building_type:
                info_text += f"\n🏘️ 建物類型：{prop.building_type}"
            
            info_text += f"\n🔗 來源：{prop.source_site}"
            
            # 構建可點擊的連結
            link_blocks = []
            if prop.source_url:
                link_blocks.append({
                    "type": "text",
                    "text": {"content": f"\n🌐 連結："}
                })
                link_blocks.append({
                    "type": "text",
                    "text": {
                        "content": "點擊查看物件詳情",
                        "link": {"url": prop.source_url}
                    },
                    "annotations": {
                        "color": "blue",
                        "underline": True
                    }
                })
            
            # 基本資訊區塊
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": info_text}
                        }
                    ] + link_blocks
                }
            })
            
            # 分隔線
            if i < len(properties):
                blocks.append({
                    "object": "block",
                    "type": "divider",
                    "divider": {}
                })
        
        return blocks
    
    def _get_search_url(self, district_name: str) -> str:
        """獲取對應區域的搜尋 URL"""
        urls = {
            '蘆洲': 'https://www.sinyi.com.tw/buy/list/3000-down-price/apartment-type/20-up-balconyarea/3-5-roomtotal/1-3-floor/Luzhou-dist/default-desc/1',
            '三重': 'https://www.sinyi.com.tw/buy/list/3000-down-price/apartment-type/20-up-balconyarea/3-5-roomtotal/1-3-floor/Sanchong-dist/default-desc/1',
            '台北': 'https://www.sinyi.com.tw/buy/list/3000-down-price/apartment-type/20-up-balconyarea/3-5-roomtotal/1-3-floor/Taipei-city/100-103-104-105-106-108-110-115-zip/default-desc/1'
        }
        return urls.get(district_name, 'https://www.sinyi.com.tw')

    def _generate_notion_blocks(self, properties: List[Property], search_date: datetime, comparison: Dict = None) -> List[Dict]:
        """生成 Notion 頁面內容塊"""
        blocks = []
        
        # 標題和搜尋條件（加入超連結）
        blocks.append({
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": "🎯 "},
                    },
                    {
                        "type": "text",
                        "text": {
                            "content": "搜尋條件",
                            "link": {"url": "https://www.sinyi.com.tw/buy/list/3000-down-price/1-3-floor/20-up-area/3-5-roomtotal/Taipei-city/default-desc/1"}
                        },
                        "annotations": {"color": "blue", "underline": True}
                    },
                    {
                        "type": "text",
                        "text": {"content": "：台北市全區 | 主建物20坪+ | 1-3樓 | 3000萬內 | 3-5房"}
                    }
                ],
                "icon": {"emoji": "🎯"}
            }
        })
        
        # 如果有比較資料，顯示變化摘要
        if comparison and comparison.get('has_previous_data'):
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "📊 與昨日比較"}
                        }
                    ]
                }
            })
            
            # 變化摘要
            change = comparison['current_count'] - comparison['previous_count']
            change_text = ""
            if change > 0:
                change_text = f"📈 淨增加 +{change} 筆"
            elif change < 0:
                change_text = f"📉 淨減少 {abs(change)} 筆"
            else:
                change_text = "➡️ 數量相同"
            
            summary_text = f"""昨日物件：{comparison['previous_count']} 筆
今日物件：{comparison['current_count']} 筆
{change_text}"""
            
            if comparison['new_properties']:
                summary_text += f"\n🆕 新增物件：{len(comparison['new_properties'])} 筆"
            
            if comparison['removed_properties']:
                summary_text += f"\n📤 下架物件：{len(comparison['removed_properties'])} 筆"
            
            if comparison['price_changed_properties']:
                summary_text += f"\n💰 價格變動：{len(comparison['price_changed_properties'])} 筆"
            
            blocks.append({
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": summary_text}
                        }
                    ],
                    "icon": {"emoji": "📊"}
                }
            })
        
        # 搜尋摘要
        if properties:
            stats = self._calculate_stats(properties)
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "� 今日搜尋摘要"}
                        }
                    ]
                }
            })
            
            summary_text = f"""找到物件：{len(properties)} 筆
平均價格：{stats.get('avg_price', 0):,.0f} 萬元
平均坪數：{stats.get('avg_size', 0):.1f} 坪
價格區間：{stats.get('min_price', 0):,} - {stats.get('max_price', 0):,} 萬元"""
            
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": summary_text}
                        }
                    ]
                }
            })
        
        # 如果有變化，先顯示新增和變動的物件
        if comparison and comparison.get('has_previous_data'):
            self._add_comparison_sections(blocks, comparison)
        
        # 物件詳情
        blocks.append({
            "object": "block",
            "type": "heading_2", 
            "heading_2": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": "🏘️ 所有物件詳情"}
                    }
                ]
            }
        })
        
        for i, prop in enumerate(properties, 1):
            # 檢查是否為新增物件
            is_new = False
            if comparison and comparison.get('new_properties'):
                for new_prop in comparison['new_properties']:
                    if self._properties_match(prop, new_prop):
                        is_new = True
                        break
            
            # 物件標題（新增物件標註）
            title_text = f"🏠 物件 {i}: {prop.title}"
            if is_new:
                title_text += " 🆕"
            
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": title_text}
                        }
                    ]
                }
            })
            
            # 物件詳細資訊
            info_text = f"""📍 地址：{prop.address}
💰 總價：{prop.total_price:,} 萬元"""
            
            if prop.unit_price:
                info_text += f" (單價: {prop.unit_price:.1f} 萬/坪)"
            
            info_text += f"""
🏢 房型：{prop.room_count}房{prop.living_room_count}廳{prop.bathroom_count}衛
📐 坪數：{prop.size} 坪"""
            
            if prop.main_area and prop.main_area != prop.size:
                info_text += f" (主建物: {prop.main_area} 坪)"
            
            info_text += f"\n🏗️ 樓層：{prop.floor}"
            if prop.total_floors:
                info_text += f"/{prop.total_floors}樓"
            
            if prop.age:
                info_text += f"\n📅 屋齡：{prop.age} 年"
            
            if prop.building_type:
                info_text += f"\n🏘️ 建物類型：{prop.building_type}"
            
            info_text += f"\n🔗 來源：{prop.source_site}"
            
            # 構建可點擊的連結
            link_blocks = []
            if prop.source_url:
                link_blocks.append({
                    "type": "text",
                    "text": {"content": f"\n🌐 連結："}
                })
                link_blocks.append({
                    "type": "text",
                    "text": {
                        "content": "點擊查看物件詳情",
                        "link": {"url": prop.source_url}
                    },
                    "annotations": {
                        "color": "blue",
                        "underline": True
                    }
                })
            
            # 基本資訊區塊
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": info_text}
                        }
                    ] + link_blocks
                }
            })
            
            # 分隔線
            if i < len(properties):
                blocks.append({
                    "object": "block",
                    "type": "divider",
                    "divider": {}
                })
        
        return blocks
    
    def _add_comparison_sections(self, blocks: List[Dict], comparison: Dict):
        """添加比較區塊"""
        # 新增物件區塊
        if comparison['new_properties']:
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": f"🆕 新增物件 ({len(comparison['new_properties'])} 筆)"}
                        }
                    ]
                }
            })
            
            for i, prop in enumerate(comparison['new_properties'], 1):
                new_item_text = f"""🏠 {prop.title}
📍 {prop.address}
💰 {prop.total_price:,} 萬元 ({prop.unit_price:.1f} 萬/坪)
🏢 {prop.room_count}房{prop.living_room_count}廳{prop.bathroom_count}衛 | {prop.main_area or prop.size} 坪"""
                
                blocks.append({
                    "object": "block",
                    "type": "callout",
                    "callout": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": new_item_text}
                            }
                        ],
                        "icon": {"emoji": "🆕"}
                    }
                })
        
        # 價格變動物件區塊
        if comparison['price_changed_properties']:
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": f"💰 價格變動 ({len(comparison['price_changed_properties'])} 筆)"}
                        }
                    ]
                }
            })
            
            for change_info in comparison['price_changed_properties']:
                prop = change_info['property']
                old_price = change_info['old_price']
                new_price = change_info['new_price']
                change_amount = change_info['change']
                
                change_emoji = "📈" if change_amount > 0 else "📉"
                change_text = f"+{change_amount}" if change_amount > 0 else str(change_amount)
                
                price_change_text = f"""{change_emoji} {prop.title}
📍 {prop.address}
💰 {old_price:,} → {new_price:,} 萬元 ({change_text} 萬)
🏢 {prop.room_count}房{prop.living_room_count}廳{prop.bathroom_count}衛"""
                
                blocks.append({
                    "object": "block",
                    "type": "callout",
                    "callout": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": price_change_text}
                            }
                        ],
                        "icon": {"emoji": change_emoji}
                    }
                })
        
        # 下架物件區塊
        if comparison['removed_properties']:
            blocks.append({
                "object": "block",
                "type": "toggle",
                "toggle": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": f"📤 昨日下架物件 ({len(comparison['removed_properties'])} 筆)"}
                        }
                    ],
                    "children": []
                }
            })
            
            # 為下架物件添加子項目
            removed_children = []
            for prop in comparison['removed_properties']:
                removed_text = f"""🏠 {prop.title}
📍 {prop.address}
💰 {prop.total_price:,} 萬元
🏢 {prop.room_count}房{prop.living_room_count}廳{prop.bathroom_count}衛"""
                
                removed_children.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": removed_text}
                            }
                        ]
                    }
                })
            
            # 更新 toggle 區塊的子項目
            blocks[-1]["toggle"]["children"] = removed_children
    
    def _properties_match(self, prop1: Property, prop2: Property) -> bool:
        """檢查兩個物件是否相同"""
        return (prop1.address == prop2.address and 
                prop1.room_count == prop2.room_count and
                (prop1.main_area or prop1.size) == (prop2.main_area or prop2.size))
    
    def _calculate_stats(self, properties: List[Property]) -> Dict[str, float]:
        """計算統計資訊"""
        if not properties:
            return {}
        
        prices = [p.total_price for p in properties if p.total_price and p.total_price > 0]
        sizes = [p.main_area or p.size for p in properties if (p.main_area or p.size) and (p.main_area or p.size) > 0]
        
        stats = {}
        
        if prices:
            stats['avg_price'] = sum(prices) / len(prices)
            stats['min_price'] = min(prices)
            stats['max_price'] = max(prices)
        
        if sizes:
            stats['avg_size'] = sum(sizes) / len(sizes)
        
        return stats
    
    def _create_local_backup(self, properties: List[Property], search_date: datetime):
        """創建本地備份檔案"""
        from .ultra_simple_notion import UltraSimpleNotionClient
        
        backup_client = UltraSimpleNotionClient(self.api_key)
        backup_client.create_daily_house_note_simple(properties, search_date)
    
    def _show_setup_instructions(self):
        """顯示設定說明"""
        print("\n" + "="*60)
        print("🔧 Notion Integration 設定指南")
        print("="*60)
        print("看起來你的 Integration 還沒有頁面存取權限。")
        print("請按照以下步驟設定：")
        print()
        print("1. 在 Notion 中創建一個新頁面作為筆記本")
        print("2. 點擊頁面右上角的 'Share' 按鈕")
        print("3. 點擊 'Invite' 並搜尋你的 Integration 名稱")
        print("4. 給予 'Can edit' 權限")
        print("5. 重新執行搜尋工具")
        print()
        print("💡 或者你可以：")
        print("- 手動複製生成的 .md 檔案內容到 Notion")
        print("- 在 https://www.notion.so/my-integrations 檢查 Integration 設定")
        print("="*60)
    
    def _find_existing_daily_note(self, search_date: datetime) -> Optional[Dict]:
        """尋找指定日期的現有搜屋筆記"""
        target_title = search_date.strftime("%Y/%m/%d搜屋筆記")
        
        try:
            pages = self.search_pages()
            for page in pages:
                title = self._extract_page_title(page)
                if title == target_title:
                    return page
        except Exception as e:
            print(f"⚠️  搜尋現有筆記時發生錯誤: {e}")
        
        return None
    
    def _update_existing_page(self, page_id: str, content_blocks: List[Dict]) -> bool:
        """更新現有頁面的內容"""
        try:
            # 先刪除現有內容
            self._clear_page_content(page_id)
            
            # 添加新內容
            for block in content_blocks:
                success = self._append_block_to_page(page_id, block)
                if not success:
                    print(f"⚠️  添加內容塊失敗")
            
            return True
            
        except Exception as e:
            print(f"❌ 更新頁面失敗: {e}")
            return False
    
    def _clear_page_content(self, page_id: str):
        """清除頁面現有內容"""
        try:
            # 取得頁面的所有子區塊
            url = f"https://api.notion.com/v1/blocks/{page_id}/children"
            response = self._make_request(url)
            
            blocks = response.get('results', [])
            
            # 刪除所有區塊
            for block in blocks:
                block_id = block.get('id')
                if block_id:
                    delete_url = f"https://api.notion.com/v1/blocks/{block_id}"
                    self._make_request(delete_url, method="DELETE")
                    
        except Exception as e:
            print(f"⚠️  清除頁面內容時發生錯誤: {e}")
    
    def _append_block_to_page(self, page_id: str, block: Dict) -> bool:
        """添加區塊到頁面"""
        try:
            url = f"https://api.notion.com/v1/blocks/{page_id}/children"
            data = {"children": [block]}
            
            response = self._make_request(url, method="PATCH", data=data)
            return 'results' in response
            
        except Exception as e:
            print(f"❌ 添加區塊失敗: {e}")
            return False


def create_full_notion_client(api_key: str) -> FullNotionClient:
    """創建完整版 Notion 客戶端"""
    return FullNotionClient(api_key=api_key)
