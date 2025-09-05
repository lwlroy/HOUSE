#!/usr/bin/env python3
"""
信義房屋蘆洲華廈大樓簡化版爬蟲
使用 requests 和基本套件，避免複雜依賴
"""

import json
import re
import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin
import sys
from pathlib import Path

# 嘗試匯入套件
try:
    import requests
    from bs4 import BeautifulSoup
except ImportError as e:
    print(f"❌ 缺少必要套件: {e}")
    print("請安裝: pip3 install requests beautifulsoup4 --user")
    sys.exit(1)

# 加入專案路徑
sys.path.append(str(Path(__file__).parent))

try:
    from src.models.property import Property
    from src.utils.full_notion import create_full_notion_client
    from src.utils.logger import get_logger
except ImportError as e:
    print(f"⚠️  無法載入專案模組: {e}")
    print("將使用簡化模式運行...")
    Property = None


class SimpleSinyiCrawler:
    """信義房屋華廈大樓簡化版爬蟲（支援多區域）"""
    
    def __init__(self, district="luzhou"):
        self.base_url = "https://www.sinyi.com.tw"
        
        # 定義不同區域的搜尋配置
        self.districts = {
            "luzhou": {
                "name": "蘆洲",
                "zip_code": "247",
                "search_url": "https://www.sinyi.com.tw/buy/list/3000-down-price/huaxia-dalou-type/20-up-balconyarea/3-5-roomtotal/NewTaipei-city/247-zip/default-desc",
                "notion_title": "信義蘆洲華廈大樓物件清單"
            },
            "sanchong": {
                "name": "三重",
                "zip_code": "241",
                "search_url": "https://www.sinyi.com.tw/buy/list/3000-down-price/huaxia-dalou-type/20-up-balconyarea/3-5-roomtotal/NewTaipei-city/241-zip/default-desc",
                "notion_title": "信義三重華廈大樓物件清單"
            },
            "taipei": {
                "name": "台北",
                "zip_code": "100-103-104-105-106-108-110-115",
                "search_url": "https://www.sinyi.com.tw/buy/list/3000-down-price/apartment-type/20-up-balconyarea/3-5-roomtotal/1-3-floor/Taipei-city/100-103-104-105-106-108-110-115-zip/default-desc",
                "notion_title": "信義台北公寓物件清單"
            }
        }
        
        # 設定當前區域
        if district not in self.districts:
            raise ValueError(f"不支援的區域: {district}。支援的區域: {list(self.districts.keys())}")
        
        self.current_district = district
        self.district_config = self.districts[district]
        self.search_base_url = self.district_config["search_url"]
        
        print(f"🎯 設定爬蟲區域: {self.district_config['name']}區")
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        # 處理 SSL 憑證問題
        self.session.verify = False
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # 確保目錄存在
        os.makedirs("data", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
    
    def fetch_page(self, url: str, delay: float = 2.0) -> Optional[str]:
        """獲取頁面內容"""
        try:
            time.sleep(delay)  # 禮貌性延遲
            
            print(f"🔍 正在獲取: {url}")
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                print(f"✅ 成功獲取頁面，內容長度: {len(response.text)}")
                return response.text
            else:
                print(f"❌ HTTP錯誤 {response.status_code}: {url}")
                return None
                
        except Exception as e:
            print(f"❌ 獲取頁面失敗 {url}: {str(e)}")
            return None
    
    def get_total_pages(self) -> int:
        """獲取總頁數"""
        first_page_url = f"{self.search_base_url}/1"
        html = self.fetch_page(first_page_url)
        
        if not html:
            return 1
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # 尋找分頁相關的文字
        page_text = soup.get_text()
        
        # 尋找類似 "第 1 頁，共 5 頁" 的文字
        page_match = re.search(r'共\s*(\d+)\s*頁', page_text)
        if page_match:
            total_pages = int(page_match.group(1))
            print(f"📄 檢測到總頁數: {total_pages}")
            return total_pages
        
        # 尋找 "第X頁" 的模式
        page_match2 = re.search(r'第\s*\d+\s*頁，共\s*(\d+)\s*頁', page_text)
        if page_match2:
            total_pages = int(page_match2.group(1))
            print(f"📄 檢測到總頁數: {total_pages}")
            return total_pages
        
        # 尋找分頁導航元素
        pagination_selectors = [
            'ul.pagination a',
            '.pagination a',
            'nav a',
            '.page-numbers a',
            'a[href*="/buy/list/"]'
        ]
        
        max_page = 1
        for selector in pagination_selectors:
            try:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href', '')
                    # 尋找包含頁碼的URL
                    page_match = re.search(r'/(\d+)$', href)
                    if page_match:
                        page_num = int(page_match.group(1))
                        if 1 <= page_num <= 100:  # 合理的頁數範圍
                            max_page = max(max_page, page_num)
                            
                    # 也檢查連結文字是否為數字
                    link_text = link.get_text().strip()
                    if link_text.isdigit():
                        page_num = int(link_text)
                        if 1 <= page_num <= 100:
                            max_page = max(max_page, page_num)
            except:
                continue
        
        # 如果還是找不到，嘗試通過檢查下一頁是否存在來確定總頁數
        if max_page == 1:
            print("📄 嘗試通過檢查頁面存在性來確定總頁數...")
            for test_page in range(2, 21):  # 測試到第20頁
                test_url = f"{self.search_base_url}/{test_page}"
                print(f"   檢查第 {test_page} 頁...")
                test_html = self.fetch_page(test_url, delay=1.0)
                
                if test_html:
                    test_soup = BeautifulSoup(test_html, 'html.parser')
                    # 檢查是否有物件資料
                    property_links = test_soup.find_all('a', href=re.compile(r'/buy/house/'))
                    if property_links:
                        max_page = test_page
                        print(f"   ✅ 第 {test_page} 頁有資料")
                    else:
                        print(f"   ❌ 第 {test_page} 頁無資料，停止檢查")
                        break
                else:
                    print(f"   ❌ 第 {test_page} 頁無法存取，停止檢查")
                    break
        
        print(f"📄 確定總頁數: {max_page}")
        return max_page
    
    def parse_property_list(self, html: str) -> List[Dict[str, Any]]:
        """解析房屋列表頁面"""
        properties = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # 尋找包含 /buy/house/ 的連結
        property_links = soup.find_all('a', href=re.compile(r'/buy/house/'))
        
        print(f"🏠 找到 {len(property_links)} 個物件連結")
        
        # 已處理的物件ID，避免重複
        processed_ids = set()
        
        for link in property_links:
            try:
                href = link.get('href', '')
                if not href:
                    continue
                
                # 提取物件ID
                url_match = re.search(r'/buy/house/([A-Za-z0-9]+)', href)
                if not url_match:
                    continue
                
                object_id = url_match.group(1)
                
                # 避免重複處理
                if object_id in processed_ids:
                    continue
                processed_ids.add(object_id)
                
                # 找到這個連結所在的容器
                container = link.find_parent(['div', 'article', 'section'])
                if not container:
                    container = link
                
                property_info = self.extract_property_info(container, object_id, href)
                if property_info:
                    properties.append(property_info)
                    print(f"✅ 解析物件: {property_info.get('title', 'Unknown')[:30]}...")
                
            except Exception as e:
                print(f"⚠️  解析物件時發生錯誤: {str(e)}")
                continue
        
        return properties
    
    def extract_property_info(self, container, object_id: str, href: str) -> Optional[Dict[str, Any]]:
        """從容器中提取房屋資訊"""
        
        detail_url = urljoin(self.base_url, href)
        
        # 取得容器內的所有文字
        container_text = container.get_text()
        
        # 提取標題 - 通常是連結的文字
        title_elem = container.find('a', href=re.compile(r'/buy/house/'))
        title = self.clean_text(title_elem.get_text()) if title_elem else "未知物件"
        
        # 如果標題太短，嘗試尋找更詳細的標題
        if len(title) < 5:
            title_candidates = container.find_all(['h1', 'h2', 'h3', 'h4', 'h5'])
            for candidate in title_candidates:
                candidate_text = self.clean_text(candidate.get_text())
                if len(candidate_text) > len(title):
                    title = candidate_text
                    break
        
        # 提取價格
        price = self.extract_price(container_text)
        
        # 提取地址
        address = self.extract_address(container_text)
        
        # 提取房型資訊
        room_info = self.extract_room_info(container_text)
        
        # 提取坪數
        size_info = self.extract_size_info(container_text)
        
        # 提取樓層
        floor_info = self.extract_floor_info(container_text)
        
        # 提取屋齡
        age_info = self.extract_age_info(container_text)
        
        property_info = {
            'id': f"sinyi_{self.current_district}_{object_id}",
            'object_id': object_id,
            'title': title,
            'address': address,
            'district': f'{self.district_config["name"]}區',
            'region': '新北市',
            'price': price,
            'total_price': price,
            'room_count': room_info.get('rooms', 3),
            'living_room_count': room_info.get('living_rooms', 2),
            'bathroom_count': room_info.get('bathrooms', 2),
            'size': size_info.get('total_size', 0),
            'main_area': size_info.get('main_area', 0),
            'floor': floor_info,
            'age': age_info,
            'building_type': '華廈/大樓',
            'source_site': '信義房屋',
            'source_url': detail_url,
            'property_type': 'sale',
            'features': [],
            'equipment': [],
            'image_urls': [],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        return property_info
    
    def clean_text(self, text: str) -> str:
        """清理文字"""
        if not text:
            return ""
        return re.sub(r'\s+', ' ', str(text)).strip()
    
    def extract_price(self, text: str) -> float:
        """提取價格（萬元）"""
        # 尋找價格模式
        price_patterns = [
            r'(\d{1,4}(?:,\d{3})*(?:\.\d+)?)\s*萬',
            r'總價[：:\s]*(\d{1,4}(?:,\d{3})*(?:\.\d+)?)',
            r'(\d{3,4})\s*萬'
        ]
        
        for pattern in price_patterns:
            price_match = re.search(pattern, text)
            if price_match:
                price_str = price_match.group(1).replace(',', '')
                try:
                    return float(price_str)
                except:
                    continue
        
        return 0
    
    def extract_address(self, text: str) -> str:
        """提取地址"""
        district_name = self.district_config["name"]
        
        # 尋找包含該區域的地址
        address_patterns = [
            f'(新北市{district_name}區[^，\\n]{{1,30}})',
            f'({district_name}區[^，\\n]{{1,30}})',
            f'新北市\\s*{district_name}區\\s*([^，\\n]{{1,20}})'
        ]
        
        for pattern in address_patterns:
            match = re.search(pattern, text)
            if match:
                return self.clean_text(match.group(1))
        
        return f"{district_name}區"
    
    def extract_room_info(self, text: str) -> Dict[str, int]:
        """提取房型資訊"""
        # 優先尋找標準格式
        room_match = re.search(r'(\d+)房(\d+)廳(\d+)衛', text)
        if room_match:
            rooms = int(room_match.group(1))
            living_rooms = int(room_match.group(2))
            bathrooms = int(room_match.group(3))
            
            # 合理性檢查
            if 1 <= rooms <= 10 and 1 <= living_rooms <= 5 and 1 <= bathrooms <= 5:
                return {
                    'rooms': rooms,
                    'living_rooms': living_rooms,
                    'bathrooms': bathrooms
                }
        
        # 尋找其他格式
        room_match2 = re.search(r'(\d+)R(\d+)L(\d+)B', text)
        if room_match2:
            rooms = int(room_match2.group(1))
            living_rooms = int(room_match2.group(2))
            bathrooms = int(room_match2.group(3))
            
            if 1 <= rooms <= 10 and 1 <= living_rooms <= 5 and 1 <= bathrooms <= 5:
                return {
                    'rooms': rooms,
                    'living_rooms': living_rooms,
                    'bathrooms': bathrooms
                }
        
        # 只尋找房間數
        room_only_match = re.search(r'(\d+)\s*房', text)
        if room_only_match:
            rooms = int(room_only_match.group(1))
            if 1 <= rooms <= 10:
                return {
                    'rooms': rooms,
                    'living_rooms': 2,  # 預設值
                    'bathrooms': 2      # 預設值
                }
        
        # 預設值
        return {'rooms': 3, 'living_rooms': 2, 'bathrooms': 2}
    
    def extract_size_info(self, text: str) -> Dict[str, float]:
        """提取坪數資訊"""
        # 建坪
        size_patterns = [
            r'建坪[：:\s]*(\d+(?:\.\d+)?)',
            r'總坪數[：:\s]*(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*坪'
        ]
        
        total_size = 0
        for pattern in size_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    total_size = float(match.group(1))
                    break
                except:
                    continue
        
        # 主建物
        main_match = re.search(r'主建物[：:\s]*(\d+(?:\.\d+)?)', text)
        main_area = float(main_match.group(1)) if main_match else total_size * 0.8
        
        return {
            'total_size': total_size,
            'main_area': main_area
        }
    
    def extract_floor_info(self, text: str) -> str:
        """提取樓層資訊"""
        floor_patterns = [
            r'(\d+)樓/(\d+)樓',
            r'(\d+)F/(\d+)F',
            r'(\d+)樓',
            r'(\d+)F'
        ]
        
        for pattern in floor_patterns:
            floor_match = re.search(pattern, text)
            if floor_match:
                if len(floor_match.groups()) >= 2 and floor_match.group(2):
                    return f"{floor_match.group(1)}樓/{floor_match.group(2)}樓"
                else:
                    return f"{floor_match.group(1)}樓"
        
        return "未知樓層"
    
    def extract_age_info(self, text: str) -> int:
        """提取屋齡"""
        age_patterns = [
            r'屋齡[：:\s]*(\d+(?:\.\d+)?)\s*年',
            r'(\d+(?:\.\d+)?)\s*年屋',
            r'民國\s*(\d+)\s*年'
        ]
        
        for pattern in age_patterns:
            age_match = re.search(pattern, text)
            if age_match:
                try:
                    age = float(age_match.group(1))
                    # 如果是民國年份，轉換為屋齡
                    if pattern.startswith(r'民國') and age > 50:
                        current_year = datetime.now().year - 1911  # 民國年
                        age = current_year - age
                    return int(age)
                except:
                    continue
        
        return 0
    
    def crawl_all_pages(self, max_pages: int = None) -> List[Dict[str, Any]]:
        """爬取所有頁面的物件"""
        district_name = self.district_config["name"]
        print(f"🔍 開始爬取信義房屋{district_name}華廈大樓物件...")
        
        # 獲取總頁數
        detected_total_pages = self.get_total_pages()
        
        # 如果指定了最大頁數限制，則使用較小值
        if max_pages is not None:
            total_pages = min(detected_total_pages, max_pages)
            print(f"📄 檢測到 {detected_total_pages} 頁，但限制為 {max_pages} 頁，將爬取 {total_pages} 頁")
        else:
            total_pages = detected_total_pages
            print(f"📄 將爬取所有 {total_pages} 頁")
        
        all_properties = []
        
        # 爬取每一頁
        for page in range(1, total_pages + 1):
            page_url = f"{self.search_base_url}/{page}"
            print(f"📄 正在爬取第 {page}/{total_pages} 頁...")
            
            html = self.fetch_page(page_url, delay=2.0)  # 適當延遲避免被封
            
            if html:
                page_properties = self.parse_property_list(html)
                
                # 如果當前頁面沒有找到任何物件，可能是到了最後一頁
                if not page_properties:
                    print(f"⚠️  第 {page} 頁沒有找到任何物件，可能已到達最後一頁")
                    break
                
                all_properties.extend(page_properties)
                print(f"✅ 第 {page} 頁找到 {len(page_properties)} 個物件")
                
                # 檢查是否找到重複的物件ID（表示可能循環到已爬過的頁面）
                if page > 1:
                    current_ids = {prop['object_id'] for prop in page_properties}
                    previous_ids = {prop['object_id'] for prop in all_properties[:-len(page_properties)]}
                    duplicate_ids = current_ids.intersection(previous_ids)
                    
                    if duplicate_ids:
                        print(f"⚠️  第 {page} 頁發現重複物件，可能已到達實際最後一頁")
                        # 移除重複的物件
                        all_properties = all_properties[:-len(page_properties)]
                        break
                        
            else:
                print(f"❌ 第 {page} 頁爬取失敗")
                if page > 1:  # 如果不是第一頁就失敗，可能是到了最後
                    print(f"⚠️  可能已到達最後一頁")
                    break
        
        # 去除重複物件（以防萬一）
        unique_properties = []
        seen_ids = set()
        for prop in all_properties:
            if prop['object_id'] not in seen_ids:
                unique_properties.append(prop)
                seen_ids.add(prop['object_id'])
        
        if len(unique_properties) != len(all_properties):
            print(f"⚠️  移除了 {len(all_properties) - len(unique_properties)} 個重複物件")
        
        print(f"🎉 爬取完成！總共找到 {len(unique_properties)} 個唯一物件")
        return unique_properties
    
    def save_to_local_file(self, properties: List[Dict[str, Any]], filename_prefix: str = None) -> str:
        """儲存到本地檔案"""
        if filename_prefix is None:
            filename_prefix = f"{self.current_district}_houses"
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_filename = f"data/{filename_prefix}_{timestamp}.json"
        
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(properties, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"📁 已儲存到: {json_filename}")
        return json_filename
    
    def load_previous_data(self) -> List[Dict[str, Any]]:
        """載入前一天的資料用於比較"""
        yesterday = datetime.now() - timedelta(days=1)
        yesterday_str = yesterday.strftime('%Y%m%d')
        
        # 尋找昨天的檔案
        data_dir = "data"
        if not os.path.exists(data_dir):
            return []
        
        filename_prefix = f"{self.current_district}_houses"
        for filename in os.listdir(data_dir):
            if filename.startswith(f"{filename_prefix}_{yesterday_str}") and filename.endswith('.json'):
                filepath = os.path.join(data_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        print(f"📂 載入昨天的資料: {len(data)} 個物件")
                        return data
                except Exception as e:
                    print(f"❌ 載入昨天資料失敗: {str(e)}")
        
        print("📂 未找到昨天的資料")
        return []
    
    def compare_with_previous(self, current_properties: List[Dict[str, Any]], previous_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """與前一天的資料比較"""
        if not previous_data:
            return {
                'new_properties': current_properties,
                'total_new': len(current_properties),
                'message': '首次爬取，所有物件都是新的'
            }
        
        # 建立昨天的物件ID集合
        previous_ids = {prop.get('object_id', prop.get('id', '')) for prop in previous_data}
        
        # 找出新增的物件
        new_properties = []
        for prop in current_properties:
            if prop['object_id'] not in previous_ids:
                new_properties.append(prop)
        
        return {
            'new_properties': new_properties,
            'total_new': len(new_properties),
            'total_current': len(current_properties),
            'total_previous': len(previous_data),
            'message': f'與昨天比較：新增 {len(new_properties)} 個物件'
        }
    
    def upload_to_notion_simple(self, properties: List[Dict[str, Any]], comparison_data: Dict = None) -> bool:
        """嘗試上傳到 Notion（直接字典版本）"""
        notion_token = os.getenv('NOTION_API_TOKEN', os.getenv('NOTION_TOKEN'))
        
        if not notion_token:
            print("⚠️  未設定 NOTION_API_TOKEN，跳過 Notion 上傳")
            print("💡 請設定環境變數或執行 setup_notion.py")
            return False
        
        try:
            # 嘗試匯入 Notion 功能
            from src.utils.full_notion import create_full_notion_client
            
            print("🔄 正在上傳到 Notion...")
            
            client = create_full_notion_client(notion_token)
            
            if not client.test_connection():
                print("❌ Notion API 連接失敗")
                return False
            
            # 直接使用字典資料，建立今天的標題
            today = datetime.now()
            title = f"{today.strftime('%Y/%m/%d')} {self.district_config['notion_title']}"
            
            # 嘗試直接創建內容
            success = self._create_notion_content_directly(client, title, properties, comparison_data, today)
            
            if success:
                print("✅ 成功上傳到 Notion！")
                return True
            else:
                print("❌ Notion 上傳失敗")
                return False
                
        except ImportError:
            print("⚠️  無法載入 Notion 功能，跳過上傳")
            return False
        except Exception as e:
            print(f"❌ Notion 上傳錯誤: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def _create_notion_content_directly(self, client, title: str, properties: List[Dict], comparison_data: Dict, today: datetime) -> bool:
        """直接創建 Notion 內容，不需要 Property 對象轉換"""
        try:
            # 生成日期字串用於重複檢測
            date_str = today.strftime('%Y/%m/%d')
            
            # 1. 尋找父頁面 "搜屋筆記"
            parent_page = client.find_parent_page("搜屋筆記")
            
            if not parent_page:
                # 嘗試使用第一個可用頁面
                all_pages = client.search_pages("")
                if all_pages:
                    parent_page = all_pages[0]
                    print(f"⚠️  使用第一個可用頁面作為父頁面: {client._extract_page_title(parent_page)}")
                else:
                    print("❌ 找不到任何可用的父頁面")
                    return False
            
            parent_page_id = parent_page["id"]
            
            # 2. 檢查並刪除同一天同一區域的舊筆記
            district_name = self.district_config['name']
            duplicate_pages = client.find_duplicate_pages(parent_page_id, date_str, district_name)
            
            if duplicate_pages:
                print(f"🗑️  發現 {len(duplicate_pages)} 個同日期同區域({district_name})的舊筆記，準備刪除...")
                for old_page in duplicate_pages:
                    old_title = client._extract_page_title(old_page)
                    if client.delete_page(old_page["id"]):
                        print(f"✅ 已刪除舊筆記: {old_title}")
                    else:
                        print(f"❌ 刪除失敗: {old_title}")
            
            # 3. 準備內容塊
            content_blocks = []
            
            # 標題說明（包含搜尋URL超連結）
            district_name = self.district_config['name']
            search_url = self.district_config['search_url'] + "/1"
            
            content_blocks.append({
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
                                "link": {"url": search_url}
                            },
                            "annotations": {"color": "blue", "underline": True}
                        },
                        {
                            "type": "text",
                            "text": {"content": f"：新北市{district_name}區 | 華廈/大樓 | 3000萬以下 | 陽台20坪+ | 3-5房"}
                        }
                    ],
                    "icon": {"emoji": "🎯"}
                }
            })
            
            # 摘要統計
            total_count = len(properties)
            if total_count > 0:
                prices = [p['price'] for p in properties if p.get('price', 0) > 0]
                if prices:
                    avg_price = sum(prices) / len(prices)
                    min_price = min(prices)
                    max_price = max(prices)
                    
                    summary_text = f"""找到物件：{total_count} 筆
平均價格：{avg_price:,.0f} 萬元
價格區間：{min_price:,} - {max_price:,} 萬元"""
                    
                    if comparison_data:
                        summary_text += f"\n{comparison_data.get('message', '')}"
                    
                    content_blocks.append({
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
            
            # 如果有新增物件，先顯示
            if comparison_data and comparison_data.get('new_properties'):
                new_properties = comparison_data['new_properties']
                content_blocks.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": f"🆕 新增物件 ({len(new_properties)} 個)"}
                            }
                        ]
                    }
                })
                
                for i, prop in enumerate(new_properties[:5], 1):  # 只顯示前5個
                    title_text = prop.get('title', '未知物件')
                    if len(title_text) > 50:
                        title_text = title_text[:50] + "..."
                    
                    detail_text = f"""地址：{prop.get('address', '未知地址')[:30]}
總價：{prop.get('price', 0):,.0f} 萬元
房型：{prop.get('room_count', 3)}房{prop.get('living_room_count', 2)}廳{prop.get('bathroom_count', 2)}衛
坪數：{prop.get('size', 0):.1f} 坪
樓層：{prop.get('floor', '未知')}"""
                    
                    content_blocks.append({
                        "object": "block",
                        "type": "callout",
                        "callout": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": f"{i}. {title_text}"}
                                },
                                {"type": "text", "text": {"content": "\n"}},
                                {
                                    "type": "text",
                                    "text": {"content": detail_text}
                                },
                                {"type": "text", "text": {"content": "\n🔗 "}},
                                {
                                    "type": "text",
                                    "text": {"content": "查看詳情", "link": {"url": prop.get('source_url', '')}},
                                    "annotations": {"color": "blue"}
                                }
                            ],
                            "icon": {"emoji": "🆕"}
                        }
                    })
            
            # 全部物件表格
            content_blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "🏠 完整物件清單"}
                        }
                    ]
                }
            })
            
            # 建立表格
            table_rows = []
            
            # 表格標題行
            table_rows.append({
                "type": "table_row",
                "table_row": {
                    "cells": [
                        [{"type": "text", "text": {"content": "物件名稱"}}],
                        [{"type": "text", "text": {"content": "總價(萬)"}}],
                        [{"type": "text", "text": {"content": "房型"}}],
                        [{"type": "text", "text": {"content": "坪數"}}],
                        [{"type": "text", "text": {"content": "樓層"}}],
                        [{"type": "text", "text": {"content": "連結"}}]
                    ]
                }
            })
            
            # 物件數據行（限制在99行以內，因為還有標題行）
            max_rows = 99  # Notion 表格最大限制是 100 行，其中 1 行是標題
            displayed_properties = properties[:max_rows]
            
            for prop in displayed_properties:
                # 清理標題
                title_text = prop.get('title', '未知物件')
                if len(title_text) > 25:
                    title_text = title_text[:25] + "..."
                
                # 房型
                room_info = f"{prop.get('room_count', 3)}房{prop.get('living_room_count', 2)}廳{prop.get('bathroom_count', 2)}衛"
                
                # 連結
                source_url = prop.get('source_url', '')
                
                table_rows.append({
                    "type": "table_row",
                    "table_row": {
                        "cells": [
                            [{"type": "text", "text": {"content": title_text}}],
                            [{"type": "text", "text": {"content": f"{prop.get('price', 0):,.0f}"}}],
                            [{"type": "text", "text": {"content": room_info}}],
                            [{"type": "text", "text": {"content": f"{prop.get('size', 0):.1f}"}}],
                            [{"type": "text", "text": {"content": prop.get('floor', '')}}],
                            [{"type": "text", "text": {"content": "連結", "link": {"url": source_url}}, "annotations": {"color": "blue"}}] if source_url else [{"type": "text", "text": {"content": "-"}}]
                        ]
                    }
                })
            
            # 如果有超過限制的物件，添加說明
            if len(properties) > max_rows:
                remaining_count = len(properties) - max_rows
                content_blocks.append({
                    "object": "block",
                    "type": "callout",
                    "callout": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": f"⚠️ 因 Notion 表格限制，此處僅顯示前 {max_rows} 個物件，另外還有 {remaining_count} 個物件請參考本地檔案。"}
                            }
                        ],
                        "icon": {"emoji": "⚠️"}
                    }
                })
            
            # 加入表格
            content_blocks.append({
                "object": "block",
                "type": "table",
                "table": {
                    "table_width": 6,
                    "has_column_header": True,
                    "children": table_rows
                }
            })
            
            # 4. 在父頁面下創建新筆記
            page_url = client.try_create_in_existing_page(parent_page_id, title, content_blocks)
            if page_url:
                print(f"✅ 成功創建頁面: {page_url}")
                return True
            else:
                print("❌ 頁面創建失敗")
                return False
                
        except Exception as e:
            print(f"❌ 創建內容錯誤: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """主程式"""
    import argparse
    
    parser = argparse.ArgumentParser(description='信義房屋華廈大樓物件爬蟲')
    parser.add_argument('--district', 
                       choices=['luzhou', 'sanchong', 'taipei', 'all'], 
                       default='luzhou',
                       help='選擇爬取區域: luzhou(蘆洲), sanchong(三重), taipei(台北), all(全部)')
    
    args = parser.parse_args()
    
    if args.district == 'all':
        # 爬取所有區域
        districts_to_crawl = ['luzhou', 'sanchong', 'taipei']
    else:
        districts_to_crawl = [args.district]
    
    print("🏠 信義房屋華廈大樓物件爬蟲")
    print("=" * 50)
    
    for district in districts_to_crawl:
        print(f"\n🎯 開始爬取 {district} 區域...")
        print("-" * 30)
        
        try:
            crawler = SimpleSinyiCrawler(district=district)
            
            # 1. 載入前一天的資料
            print("📂 載入前一天的資料...")
            previous_data = crawler.load_previous_data()
            
            # 2. 爬取今天的資料（不限制頁數，爬取所有頁面）
            properties = crawler.crawl_all_pages()  # 移除 max_pages 限制
            
            if not properties:
                print("❌ 沒有爬取到任何資料")
                continue
            
            # 3. 與前一天比較
            comparison = crawler.compare_with_previous(properties, previous_data)
            print(f"📈 {comparison['message']}")
            
            if comparison['new_properties']:
                print("\n🆕 新增的物件:")
                for i, prop in enumerate(comparison['new_properties'][:5], 1):  # 只顯示前5個
                    print(f"  {i}. {prop['title'][:30]}... - {prop['price']}萬元")
                    print(f"     🔗 {prop['source_url']}")
            
            # 4. 儲存本地檔案
            json_file = crawler.save_to_local_file(properties)
            
            # 5. 嘗試上傳到 Notion
            success = crawler.upload_to_notion_simple(properties, comparison)
            
            # 6. 總結
            print(f"\n📊 {crawler.district_config['name']}區爬取總結:")
            print(f"  • 今天找到物件: {len(properties)} 個")
            print(f"  • 新增物件: {comparison['total_new']} 個")
            print(f"  • 本地檔案: {json_file}")
            print(f"  • Notion上傳: {'✅ 成功' if success else '❌ 失敗'}")
            
            if comparison['new_properties']:
                print(f"\n💡 發現 {len(comparison['new_properties'])} 個新物件！")
                
        except KeyboardInterrupt:
            print(f"\n⏹️  使用者中斷執行")
            break
        except Exception as e:
            print(f"\n❌ {district} 區域執行錯誤: {str(e)}")
            continue


if __name__ == "__main__":
    main()
