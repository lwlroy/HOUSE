#!/usr/bin/env python3
"""
信義房屋三重蘆洲整合版爬蟲
使用指定網址爬取三重蘆洲的華廈大樓物件
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


class SanchongLuzhouCrawler:
    """信義房屋三重蘆洲整合版爬蟲"""
    
    def __init__(self):
        self.base_url = "https://www.sinyi.com.tw"
        
        # 使用指定的搜尋URL
        self.search_base_url = "https://www.sinyi.com.tw/buy/list/3000-down-price/dalou-huaxia-type/20-up-balconyarea/3-5-roomtotal/NewTaipei-city/241-247-zip/default-desc"
        
        self.district_name = "三重蘆洲"
        self.region_name = "新北市"
        
        print(f"🎯 設定爬蟲區域: {self.district_name}區 (三重+蘆洲)")
        print(f"🔗 搜尋網址: {self.search_base_url}")
        
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
        raw_title = self.clean_text(title_elem.get_text()) if title_elem else "未知物件"
        
        # 如果原始標題太短，嘗試尋找更詳細的標題
        if len(raw_title) < 5:
            title_candidates = container.find_all(['h1', 'h2', 'h3', 'h4', 'h5'])
            for candidate in title_candidates:
                candidate_text = self.clean_text(candidate.get_text())
                if len(candidate_text) > len(raw_title):
                    raw_title = candidate_text
                    break
        
        # 從完整標題中提取簡潔的物件名稱
        title = self.extract_property_name(raw_title)
        
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
            'id': f"sinyi_sanchong_luzhou_{object_id}",
            'object_id': object_id,
            'title': title,
            'address': address,
            'district': self.district_name,
            'region': self.region_name,
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
    
    def extract_property_name(self, title: str) -> str:
        """從完整標題中提取簡潔的物件名稱"""
        if not title:
            return "未知物件"
        
        # 移除常見的前綴
        title = re.sub(r'^(店長推薦|專任|獨家|急售|出價就談|可看|新接|稀有|推薦)\s*[★❤️⭐✿㊣\[\]｜·]*\s*', '', title)
        
        # 嘗試提取社區名稱
        patterns = [
            # 模式1: 社區名稱重複出現的情況 (如: "榮耀巴黎...榮耀巴黎新北市")
            r'([A-Za-z\u4e00-\u9fff]{3,15}).*?\1新北市',
            # 模式2: 明確的社區名稱 (如: "全球嘉年華新北市")
            r'([A-Za-z\u4e00-\u9fff]{3,15})新北市',
            # 模式3: 社區名稱在最末尾 (如: "森活大市新北市") 
            r'([A-Za-z\u4e00-\u9fff]{3,12})新北市[^A-Za-z\u4e00-\u9fff]*$',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title)
            if match:
                extracted = match.group(1).strip()
                
                # 檢查是否為有效的社區名稱
                if 3 <= len(extracted) <= 15:
                    # 避免一些通用詞彙
                    avoid_words = ['三房', '四房', '電梯', '車位', '大樓', '華廈', '建坪', '年華', '年大']
                    if not any(word in extracted for word in avoid_words):
                        return extracted
        
        # 如果沒有找到社區名稱，嘗試提取描述性標題
        descriptive_patterns = [
            # 描述 + 社區名稱
            r'^([^新北台北0-9]{5,20}?)(?:新北|台北)',
            # 純描述性標題
            r'^([^新北台北0-9]{3,15}?)(?:[0-9]+年|建坪)',
        ]
        
        for pattern in descriptive_patterns:
            match = re.search(pattern, title)
            if match:
                extracted = match.group(1).strip()
                # 清理結尾的常見詞彙
                extracted = re.sub(r'(車位|三房|四房|電梯|景觀|庭院|綠意|邊間|高樓|方正|美學|豪邸)$', '', extracted)
                if 3 <= len(extracted) <= 20:
                    return extracted
        
        # 最後的備用方案：取前15個字符
        short_title = title[:15]
        for separator in ['新北', '台北', '建坪', '年', '房', '萬']:
            if separator in short_title:
                short_title = short_title.split(separator)[0]
                break
        
        return short_title.strip() if short_title.strip() else "未知物件"
    
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
        # 針對三重蘆洲的地址提取
        address_patterns = [
            r'(新北市(?:三重|蘆洲)區[^，\n]{1,30})',
            r'((?:三重|蘆洲)區[^，\n]{1,30})',
            r'新北市\s*(?:三重|蘆洲)區\s*([^，\n]{1,20})'
        ]
        
        for pattern in address_patterns:
            match = re.search(pattern, text)
            if match:
                return self.clean_text(match.group(1))
        
        # 如果沒找到具體地址，檢查是否至少包含區域名稱
        if '三重' in text:
            return "三重區"
        elif '蘆洲' in text:
            return "蘆洲區"
        else:
            return "三重蘆洲區"
    
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
        print(f"🔍 開始爬取信義房屋三重蘆洲華廈大樓物件...")
        
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
    
    def save_to_local_file(self, properties: List[Dict[str, Any]], filename_prefix: str = "sanchong_luzhou_houses") -> str:
        """儲存到本地檔案"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_filename = f"data/{filename_prefix}_{timestamp}.json"
        
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(properties, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"📁 已儲存到: {json_filename}")
        return json_filename
    
    def load_previous_data(self) -> List[Dict[str, Any]]:
        """載入前一天的資料用於比較"""
        # 優先檢查 GitHub Actions 下載的前一天資料
        previous_data_dirs = ["./previous_data", "data"]
        
        print(f"🔍 正在搜尋前一天的三重蘆洲資料...")
        print(f"  • 搜尋目錄: {previous_data_dirs}")
        
        for data_dir in previous_data_dirs:
            if not os.path.exists(data_dir):
                print(f"  ❌ {data_dir} 目錄不存在")
                continue
                
            print(f"  🔍 在 {data_dir} 目錄中搜尋前一天的資料...")
            
            # 列出目錄中的所有檔案
            try:
                files_in_dir = os.listdir(data_dir)
                print(f"     📄 找到 {len(files_in_dir)} 個檔案: {files_in_dir}")
            except Exception as e:
                print(f"     ❌ 無法列出檔案: {e}")
                continue
            
            # 如果是 previous_data 目錄（GitHub Actions 下載的）
            if data_dir == "./previous_data":
                filename_prefix = "sanchong_luzhou_houses"
                print(f"     🎯 搜尋檔案前綴: {filename_prefix}")
                
                for filename in files_in_dir:
                    if filename.startswith(filename_prefix) and filename.endswith('.json'):
                        filepath = os.path.join(data_dir, filename)
                        print(f"     ✅ 找到匹配檔案: {filename}")
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                print(f"     📂 從 GitHub Actions artifacts 載入前一天資料: {len(data)} 個物件")
                                return data
                        except Exception as e:
                            print(f"     ❌ 載入前一天資料失敗: {str(e)}")
            else:
                # 原本的邏輯：尋找昨天日期的檔案
                yesterday = datetime.now() - timedelta(days=1)
                yesterday_str = yesterday.strftime('%Y%m%d')
                filename_prefix = "sanchong_luzhou_houses"
                target_pattern = f"{filename_prefix}_{yesterday_str}"
                
                print(f"     🎯 搜尋昨天日期檔案模式: {target_pattern}*.json")
                
                for filename in files_in_dir:
                    if filename.startswith(target_pattern) and filename.endswith('.json'):
                        filepath = os.path.join(data_dir, filename)
                        print(f"     ✅ 找到昨天的檔案: {filename}")
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                print(f"     📂 載入昨天的資料: {len(data)} 個物件")
                                return data
                        except Exception as e:
                            print(f"     ❌ 載入昨天資料失敗: {str(e)}")
        
        print("📂 未找到前一天的資料")
        return []
    
    def compare_with_previous(self, current_properties: List[Dict[str, Any]], previous_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """與前一天的資料比較，詳細分類差異物件"""
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
        
        # 建立昨天的物件映射 (使用地址+房型+坪數作為 key)
        previous_map = {}
        for prop in previous_data:
            key = self._generate_property_key(prop)
            previous_map[key] = prop
        
        # 建立今天的物件映射
        current_map = {}
        for prop in current_properties:
            key = self._generate_property_key(prop)
            current_map[key] = prop
        
        # 找出新增的物件
        new_properties = []
        unchanged_properties = []
        price_changed_properties = []
        
        for key, current_prop in current_map.items():
            if key not in previous_map:
                # 新增的物件
                new_properties.append(current_prop)
                print(f"🆕 新增物件: {current_prop.get('title', 'Unknown')[:30]}")
            else:
                # 存在的物件，檢查價格是否變動
                previous_prop = previous_map[key]
                current_price = current_prop.get('price', 0)
                previous_price = previous_prop.get('price', 0)
                
                if abs(current_price - previous_price) > 0:  # 價格有變動
                    change_info = {
                        'property': current_prop,
                        'old_price': previous_price,
                        'new_price': current_price,
                        'change': current_price - previous_price,
                        'change_percentage': ((current_price - previous_price) / previous_price * 100) if previous_price > 0 else 0
                    }
                    price_changed_properties.append(change_info)
                    
                    change_emoji = "📈" if change_info['change'] > 0 else "📉"
                    print(f"{change_emoji} 變價物件: {current_prop.get('title', 'Unknown')[:30]} - {previous_price:,}→{current_price:,}萬 ({change_info['change']:+.0f}萬)")
                else:
                    # 價格無變動的物件
                    unchanged_properties.append(current_prop)
        
        # 找出下架的物件
        removed_properties = []
        for key, previous_prop in previous_map.items():
            if key not in current_map:
                removed_properties.append(previous_prop)
                print(f"📤 下架物件: {previous_prop.get('title', 'Unknown')[:30]}")
        
        # 計算變化
        change = len(current_properties) - len(previous_data)
        
        # 生成詳細的比較摘要
        summary_parts = []
        if new_properties:
            summary_parts.append(f"新增 {len(new_properties)} 個")
        if removed_properties:
            summary_parts.append(f"下架 {len(removed_properties)} 個")
        if price_changed_properties:
            summary_parts.append(f"變價 {len(price_changed_properties)} 個")
        
        if not summary_parts:
            summary_parts.append("無變化")
        
        message = f"與昨天比較：{', '.join(summary_parts)}物件"
        
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
            'message': message
        }
    
    def _generate_property_key(self, prop: Dict[str, Any]) -> str:
        """生成物件的唯一識別鍵"""
        address = prop.get('address', '').strip()
        room_count = prop.get('room_count', 0)
        size = prop.get('size', 0) or prop.get('main_area', 0)
        
        # 使用地址、房數、坪數作為唯一識別
        return f"{address}_{room_count}_{size}"
    
    def upload_to_notion(self, properties: List[Dict[str, Any]], comparison_data: Dict = None) -> bool:
        """上傳到 Notion"""
        notion_token = os.getenv('NOTION_API_TOKEN', os.getenv('NOTION_TOKEN'))
        
        if not notion_token:
            print("⚠️  未設定 NOTION_API_TOKEN，跳過 Notion 上傳")
            print("💡 請設定環境變數或執行 setup_notion.py")
            return False
        
        # 調試：顯示比較資料的詳細資訊
        print(f"\n🔍 比較資料調試資訊:")
        if comparison_data:
            print(f"  • has_previous_data: {comparison_data.get('has_previous_data', False)}")
            print(f"  • 新增物件數量: {len(comparison_data.get('new_properties', []))}")
            print(f"  • 價格變動物件數量: {len(comparison_data.get('price_changed_properties', []))}")
            print(f"  • 下架物件數量: {len(comparison_data.get('removed_properties', []))}")
            print(f"  • 總計目前物件: {comparison_data.get('current_count', 0)}")
            print(f"  • 總計前一天物件: {comparison_data.get('previous_count', 0)}")
        else:
            print(f"  • comparison_data 為 None")
        
        try:
            # 嘗試匯入 Notion 功能
            from src.utils.full_notion import create_full_notion_client
            from src.models.property import Property
            
            print("🔄 正在上傳到 Notion...")
            
            client = create_full_notion_client(notion_token)
            
            if not client.test_connection():
                print("❌ Notion API 連接失敗")
                return False
            
            # 將字典資料轉換為 Property 對象
            property_objects = []
            for i, prop_dict in enumerate(properties):
                try:
                    # 生成唯一 ID
                    prop_id = f"sanchong_luzhou_{i+1}_{prop_dict.get('title', '')[:10]}"
                    
                    prop = Property(
                        id=prop_id,
                        title=prop_dict.get('title', ''),
                        address=prop_dict.get('address', ''),
                        district=self.district_name,
                        region=self.region_name,
                        price=int(prop_dict.get('price', 0)),
                        room_count=prop_dict.get('room_count', 3),
                        living_room_count=prop_dict.get('living_room_count', 2),
                        bathroom_count=prop_dict.get('bathroom_count', 2),
                        size=prop_dict.get('size', 0),
                        floor=str(prop_dict.get('floor', '')),
                        source_site="信義房屋",
                        source_url=prop_dict.get('source_url', ''),
                        property_type='sale'  # 買屋
                    )
                    
                    # 設定買屋專用欄位
                    prop.total_price = int(prop_dict.get('price', 0))  # 總價
                    
                    # 設定其他屬性（如果有的話）
                    if 'main_area' in prop_dict:
                        prop.main_area = prop_dict['main_area']
                    if 'unit_price' in prop_dict:
                        prop.unit_price = prop_dict['unit_price']
                    if 'total_floors' in prop_dict:
                        prop.total_floors = prop_dict['total_floors']
                    if 'age' in prop_dict:
                        prop.age = prop_dict['age']
                    if 'building_type' in prop_dict:
                        prop.building_type = prop_dict['building_type']
                    
                    property_objects.append(prop)
                except Exception as e:
                    print(f"⚠️  轉換物件失敗: {e}")
                    continue
            
            # 使用新的層級結構上傳
            today = datetime.now()
            district_name = 'sanchong_luzhou'  # 英文區域名稱
            
            # 使用新的區域物件清單創建方法，傳入比較資料
            success = client.create_district_house_list(
                properties=property_objects,
                search_date=today,
                district_name=district_name,
                comparison=comparison_data  # 傳入比較資料
            )
            
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


def main():
    """主程式"""
    print("🏠 信義房屋三重蘆洲華廈大樓整合爬蟲")
    print("🔗 搜尋網址: https://www.sinyi.com.tw/buy/list/3000-down-price/dalou-huaxia-type/20-up-balconyarea/3-5-roomtotal/NewTaipei-city/241-247-zip/default-desc")
    print("=" * 80)
    
    try:
        crawler = SanchongLuzhouCrawler()
        
        # 1. 載入前一天的資料
        print("📂 載入前一天的資料...")
        previous_data = crawler.load_previous_data()
        
        # 2. 爬取今天的資料
        properties = crawler.crawl_all_pages()
        
        if not properties:
            print("❌ 沒有爬取到任何資料")
            return
        
        # 3. 與前一天比較
        comparison = crawler.compare_with_previous(properties, previous_data)
        print(f"\n📈 {comparison['message']}")
        
        # 4. 顯示詳細比較結果
        print(f"\n📊 三重蘆洲區比較詳情:")
        print(f"  • 前一天物件數: {comparison.get('previous_count', 0)}")
        print(f"  • 今天物件數: {comparison.get('current_count', 0)}")
        print(f"  • 🆕 新增物件數: {comparison.get('total_new', 0)}")
        print(f"  • 📤 下架物件數: {comparison.get('total_removed', 0)}")
        print(f"  • 💰 變價物件數: {comparison.get('total_price_changed', 0)}")
        
        # 5. 顯示重點物件預覽
        if comparison.get('new_properties'):
            print(f"\n💡 🆕 新增物件預覽 (共 {len(comparison['new_properties'])} 個):")
            for i, prop in enumerate(comparison['new_properties'][:3], 1):
                print(f"  {i}. {prop['title'][:30]}...")
                print(f"     💰 價格: {prop['price']:,} 萬元")
                print(f"     📍 地址: {prop['address']}")
                print(f"     🏢 房型: {prop['room_count']}房{prop['living_room_count']}廳{prop['bathroom_count']}衛")
                print(f"     📐 坪數: {prop['size']} 坪")
                print(f"     🏗️ 樓層: {prop['floor']}")
                print(f"     🔗 查看詳情: {prop['source_url']}")
                print()
            
            if len(comparison['new_properties']) > 3:
                print(f"     ... 及其他 {len(comparison['new_properties']) - 3} 個新增物件")
        
        if comparison.get('price_changed_properties'):
            print(f"\n💰 變價物件預覽 (共 {len(comparison['price_changed_properties'])} 個):")
            for i, change_info in enumerate(comparison['price_changed_properties'][:2], 1):
                prop = change_info['property']
                old_price = change_info['old_price']
                new_price = change_info['new_price']
                change_amount = change_info['change']
                
                change_symbol = "📈" if change_amount > 0 else "📉"
                change_text = f"+{change_amount}" if change_amount > 0 else str(change_amount)
                
                print(f"  {i}. {prop['title'][:30]}...")
                print(f"     💰 價格異動: {old_price:,} → {new_price:,} 萬元 ({change_symbol} {change_text} 萬)")
                print(f"     📍 地址: {prop['address']}")
                print(f"     🏢 房型: {prop['room_count']}房{prop['living_room_count']}廳{prop['bathroom_count']}衛")
                print(f"     📐 坪數: {prop['size']} 坪")
                print(f"     🏗️ 樓層: {prop['floor']}")
                print(f"     🔗 查看詳情: {prop['source_url']}")
                print()
            
            if len(comparison['price_changed_properties']) > 2:
                print(f"     ... 及其他 {len(comparison['price_changed_properties']) - 2} 個變價物件")
        
        if comparison.get('removed_properties'):
            print(f"\n📤 下架物件數量: {len(comparison['removed_properties'])} 個")
        
        # 6. 儲存本地檔案
        json_file = crawler.save_to_local_file(properties)
        
        # 7. 嘗試上傳到 Notion
        success = crawler.upload_to_notion(properties, comparison)
        
        # 8. 總結
        print(f"\n📊 三重蘆洲區爬取總結:")
        print(f"  • 今天找到物件: {len(properties)} 個")
        
        if comparison['has_previous_data']:
            print(f"  • 昨天物件數量: {comparison['previous_count']} 個")
            print(f"  • 🆕 新增物件: {comparison['total_new']} 個")
            print(f"  • 📤 下架物件: {comparison['total_removed']} 個")
            print(f"  • 💰 變價物件: {comparison['total_price_changed']} 個")
            
            # 顯示淨變化
            net_change = comparison.get('change', 0)
            if net_change > 0:
                print(f"  • 📈 淨增加: +{net_change} 個")
            elif net_change < 0:
                print(f"  • 📉 淨減少: {abs(net_change)} 個")
            else:
                print(f"  • ➡️ 數量無變化")
        else:
            print(f"  • 🆕 新增物件: {comparison['total_new']} 個 (首次執行)")
        
        print(f"  • 📁 本地檔案: {json_file}")
        print(f"  • 🔗 Notion上傳: {'✅ 成功' if success else '❌ 失敗'}")
        
    except KeyboardInterrupt:
        print(f"\n⏹️  使用者中斷執行")
    except Exception as e:
        print(f"\n❌ 執行錯誤: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
