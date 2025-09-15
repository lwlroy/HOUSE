#!/usr/bin/env python3
"""
信義房屋台北公寓簡化版爬蟲
只支援台北區域的公寓物件爬取
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
except ImportError as e:
    print(f"⚠️  無法載入專案模組: {e}")
    print("將使用簡化模式運行...")
    Property = None


class TaipeiApartmentCrawler:
    """信義房屋台北公寓爬蟲（簡化版）"""
    
    def __init__(self):
        self.base_url = "https://www.sinyi.com.tw"
        self.search_url = "https://www.sinyi.com.tw/buy/list/3000-down-price/apartment-type/20-up-balconyarea/3-5-roomtotal/1-3-floor/Taipei-city/100-103-104-105-106-108-110-115-zip/default-desc"
        self.district_name = "台北"
        self.region_name = "台北市"
        
        print(f"🎯 設定爬蟲區域: {self.district_name}區公寓")
        print(f"🔗 搜尋網址: {self.search_url}")
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
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
    
    def get_total_pages(self) -> int:
        """確定總頁數"""
        print(f"📄 嘗試通過檢查頁面存在性來確定總頁數...")
        
        for page in range(1, 20):  # 最多檢查20頁
            print(f"   檢查第 {page} 頁...")
            
            page_url = f"{self.search_url}/{page}"
            try:
                response = self.session.get(page_url, timeout=10)
                print(f"✅ 成功獲取頁面，內容長度: {len(response.content)}")
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # 檢查是否有物件
                items = soup.find_all('div', class_='buy-list-item')
                
                if len(items) == 0:
                    print(f"   ❌ 第 {page} 頁無資料，停止檢查")
                    return page - 1
                else:
                    print(f"   ✅ 第 {page} 頁有資料")
                
                time.sleep(2)  # 避免請求過快
                
            except Exception as e:
                print(f"   ❌ 第 {page} 頁檢查失敗: {str(e)}")
                return page - 1
        
        return 15  # 默認最大頁數
    
    def crawl_page(self, page: int = 1) -> List[Dict[str, Any]]:
        """爬取指定頁面的物件"""
        properties = []
        
        page_url = f"{self.search_url}/{page}"
        print(f"🔍 正在獲取: {page_url}")
        
        try:
            response = self.session.get(page_url, timeout=15)
            print(f"✅ 成功獲取頁面，內容長度: {len(response.content)}")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 尋找物件連結
            items = soup.find_all('div', class_='buy-list-item')
            
            property_links = []
            for item in items:
                link_element = item.find('a', href=True)
                if link_element:
                    href = link_element['href']
                    if href.startswith('/buy/house/'):
                        full_url = urljoin(self.base_url, href)
                        property_links.append(full_url)
            
            print(f"🏠 找到 {len(property_links)} 個物件連結")
            
            # 爬取每個物件的詳細資訊
            for i, link in enumerate(property_links, 1):
                try:
                    prop = self.parse_property_detail(link)
                    if prop:
                        properties.append(prop)
                        print(f"✅ 解析物件: {prop['title'][:20]}...")
                    
                    # 避免請求過快
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"❌ 解析物件失敗: {str(e)}")
                    continue
            
        except Exception as e:
            print(f"❌ 爬取第 {page} 頁失敗: {str(e)}")
        
        return properties
    
    def parse_property_detail(self, url: str) -> Optional[Dict[str, Any]]:
        """解析物件詳細資訊"""
        try:
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 提取基本資訊
            title = self._extract_title(soup)
            price = self._extract_price(soup)
            address = self._extract_address(soup)
            room_info = self._extract_room_info(soup)
            size_info = self._extract_size_info(soup)
            floor_info = self._extract_floor_info(soup)
            
            # 生成物件ID
            object_id = url.split('/')[-1].split('?')[0] if '/' in url else 'unknown'
            
            property_data = {
                'id': f"taipei_{object_id}",
                'object_id': object_id,
                'title': title,
                'address': address,
                'price': price,
                'room_count': room_info.get('room_count', 3),
                'living_room_count': room_info.get('living_room_count', 2),
                'bathroom_count': room_info.get('bathroom_count', 2),
                'size': size_info.get('total_size', 0),
                'main_area': size_info.get('main_area', size_info.get('total_size', 0)),
                'floor': floor_info,
                'source_url': url,
                'crawl_time': datetime.now().isoformat(),
                'region': self.region_name,
                'district': self.district_name
            }
            
            return property_data
            
        except Exception as e:
            print(f"❌ 解析物件詳情失敗: {str(e)}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取標題"""
        title_selectors = [
            'h1.object-title',
            'h1',
            '.object-title',
            '.title'
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return "未知物件"
    
    def _extract_price(self, soup: BeautifulSoup) -> int:
        """提取價格（萬元）"""
        price_selectors = [
            '.object-price .price-total',
            '.price-total',
            '.object-price'
        ]
        
        for selector in price_selectors:
            element = soup.select_one(selector)
            if element:
                price_text = element.get_text(strip=True)
                # 提取數字
                price_match = re.search(r'[\d,]+', price_text.replace(',', ''))
                if price_match:
                    try:
                        return int(price_match.group())
                    except ValueError:
                        continue
        
        return 0
    
    def _extract_address(self, soup: BeautifulSoup) -> str:
        """提取地址"""
        address_selectors = [
            '.object-address',
            '.address',
            '.location'
        ]
        
        for selector in address_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return "未知地址"
    
    def _extract_room_info(self, soup: BeautifulSoup) -> Dict[str, int]:
        """提取房間資訊"""
        room_info = {'room_count': 3, 'living_room_count': 2, 'bathroom_count': 2}
        
        # 尋找房型資訊
        room_elements = soup.find_all(text=re.compile(r'\d+房\d+廳\d+衛'))
        for element in room_elements:
            room_match = re.search(r'(\d+)房(\d+)廳(\d+)衛', element)
            if room_match:
                room_info['room_count'] = int(room_match.group(1))
                room_info['living_room_count'] = int(room_match.group(2))
                room_info['bathroom_count'] = int(room_match.group(3))
                break
        
        return room_info
    
    def _extract_size_info(self, soup: BeautifulSoup) -> Dict[str, float]:
        """提取坪數資訊"""
        size_info = {'total_size': 0, 'main_area': 0}
        
        # 尋找坪數資訊
        size_elements = soup.find_all(text=re.compile(r'\d+\.?\d*坪'))
        for element in size_elements:
            size_match = re.search(r'(\d+\.?\d*)坪', element)
            if size_match:
                size_value = float(size_match.group(1))
                if size_value > size_info['total_size']:
                    size_info['total_size'] = size_value
                    size_info['main_area'] = size_value
        
        return size_info
    
    def _extract_floor_info(self, soup: BeautifulSoup) -> str:
        """提取樓層資訊"""
        floor_patterns = [
            r'(\d+)樓/(\d+)樓',
            r'(\d+)F/(\d+)F',
            r'(\d+)樓',
            r'(\d+)F'
        ]
        
        # 在所有文本中搜尋樓層資訊
        all_text = soup.get_text()
        for pattern in floor_patterns:
            floor_match = re.search(pattern, all_text)
            if floor_match:
                if len(floor_match.groups()) >= 2 and floor_match.group(2):
                    return f"{floor_match.group(1)}樓/{floor_match.group(2)}樓"
                else:
                    return f"{floor_match.group(1)}樓"
        
        return "未知樓層"
    
    def crawl_all_pages(self) -> List[Dict[str, Any]]:
        """爬取所有頁面"""
        print("🔍 開始爬取信義房屋台北公寓物件...")
        
        total_pages = self.get_total_pages()
        print(f"📄 確定總頁數: {total_pages}")
        print(f"📄 將爬取所有 {total_pages} 頁")
        
        all_properties = []
        
        for page in range(1, total_pages + 1):
            print(f"📄 正在爬取第 {page}/{total_pages} 頁...")
            
            try:
                properties = self.crawl_page(page)
                all_properties.extend(properties)
                print(f"✅ 第 {page} 頁找到 {len(properties)} 個物件")
                
                # 避免請求過快
                time.sleep(3)
                
            except Exception as e:
                print(f"❌ 第 {page} 頁爬取失敗: {str(e)}")
                continue
        
        # 去重
        unique_properties = []
        seen_ids = set()
        
        for prop in all_properties:
            prop_id = prop.get('object_id', '')
            if prop_id and prop_id not in seen_ids:
                seen_ids.add(prop_id)
                unique_properties.append(prop)
        
        print(f"🎉 爬取完成！總共找到 {len(unique_properties)} 個唯一物件")
        
        return unique_properties
    
    def save_to_local_file(self, properties: List[Dict[str, Any]]) -> str:
        """儲存到本地JSON檔案"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/taipei_houses_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(properties, f, ensure_ascii=False, indent=2)
        
        return filename
    
    def load_previous_data(self) -> List[Dict[str, Any]]:
        """載入前一天的資料"""
        print("🔍 正在搜尋前一天的資料...")
        print(f"  • 目標區域: taipei")
        
        data_dirs = ["./previous_data", "data"]
        print(f"  • 搜尋目錄: {data_dirs}")
        
        for data_dir in data_dirs:
            if not os.path.exists(data_dir):
                print(f"  ❌ {data_dir} 目錄不存在")
                continue
            
            print(f"  🔍 在 {data_dir} 目錄中搜尋前一天的資料...")
            
            try:
                files = os.listdir(data_dir)
                print(f"     📄 找到 {len(files)} 個檔案: {files}")
                
                # 搜尋昨天的檔案
                yesterday = datetime.now() - timedelta(days=1)
                yesterday_pattern = f"taipei_houses_{yesterday.strftime('%Y%m%d')}"
                print(f"     🎯 搜尋昨天日期檔案模式: {yesterday_pattern}*.json")
                
                matching_files = [f for f in files if f.startswith(yesterday_pattern) and f.endswith('.json')]
                
                if matching_files:
                    # 取最新的檔案
                    latest_file = sorted(matching_files)[-1]
                    filepath = os.path.join(data_dir, latest_file)
                    
                    print(f"  ✅ 找到前一天資料: {latest_file}")
                    
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        print(f"  📊 載入 {len(data)} 個前一天物件")
                        return data
                else:
                    # 如果找不到昨天的檔案，尋找最新的台北檔案
                    taipei_files = [f for f in files if f.startswith("taipei_houses_") and f.endswith('.json')]
                    if taipei_files:
                        # 按檔名排序，取最新的
                        taipei_files.sort(reverse=True)
                        latest_file = taipei_files[0]
                        filepath = os.path.join(data_dir, latest_file)
                        print(f"  ✅ 找到最新的台北檔案: {latest_file}")
                        
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            print(f"  📊 載入最新資料: {len(data)} 個物件")
                            return data
                
            except Exception as e:
                print(f"  ❌ 讀取 {data_dir} 失敗: {str(e)}")
                continue
        
        print("📂 未找到前一天的資料")
        return []
    
    def compare_with_previous(self, current_properties: List[Dict[str, Any]], previous_data: List[Dict[str, Any]]) -> Dict:
        """與前一天資料比較"""
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
                'change': len(current_properties),
                'message': '首次爬取，所有物件都是新的'
            }
        
        # 使用地址、房數、坪數作為唯一識別
        def generate_key(prop):
            address = prop.get('address', '').strip()
            room_count = prop.get('room_count', 0)
            size = prop.get('size', 0)
            main_area = prop.get('main_area', size)
            return f"{address}_{room_count}_{main_area}"
        
        # 建立前一天的物件映射
        previous_map = {}
        for prop in previous_data:
            key = generate_key(prop)
            previous_map[key] = prop
        
        # 建立今天的物件映射
        current_map = {}
        for prop in current_properties:
            key = generate_key(prop)
            current_map[key] = prop
        
        # 分析變化
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
    
    def upload_to_notion(self, properties: List[Dict[str, Any]], comparison: Dict = None) -> bool:
        """上傳到 Notion"""
        notion_token = os.getenv('NOTION_API_TOKEN')
        
        if not notion_token:
            print("⚠️  未設定 NOTION_API_TOKEN，跳過 Notion 上傳")
            return False
        
        if not Property:
            print("⚠️  無法載入 Property 模型，跳過 Notion 上傳")
            return False
        
        try:
            # 只上傳有變化的物件（如果有前一天資料）
            properties_to_upload = []
            
            if comparison and comparison.get('has_previous_data'):
                # 新增物件
                if comparison.get('new_properties'):
                    properties_to_upload.extend(comparison['new_properties'])
                
                # 價格變動物件
                if comparison.get('price_changed_properties'):
                    for change_info in comparison['price_changed_properties']:
                        prop = change_info['property'].copy()
                        change_amount = change_info['change']
                        change_emoji = "📈" if change_amount > 0 else "📉"
                        prop['title'] = f"{prop['title']} {change_emoji} 價格變動: {change_info['old_price']:,}→{change_info['new_price']:,}萬"
                        properties_to_upload.append(prop)
                
                if not properties_to_upload:
                    print("✅ 沒有新增或變動的物件，Notion 筆記保持不變")
                    return True
            else:
                # 首次執行，上傳所有物件
                properties_to_upload = properties
            
            print(f"📝 準備上傳 {len(properties_to_upload)} 個物件到 Notion")
            
            # 轉換為 Property 物件
            property_objects = []
            for i, prop_dict in enumerate(properties_to_upload):
                prop_id = f"taipei_{i+1}_{prop_dict.get('title', '')[:10]}"
                
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
                    property_type='sale'
                )
                
                prop.total_price = int(prop_dict.get('price', 0))
                
                if 'main_area' in prop_dict:
                    prop.main_area = prop_dict['main_area']
                
                property_objects.append(prop)
            
            # 建立 Notion 客戶端並上傳
            client = create_full_notion_client(notion_token)
            
            if not client.test_connection():
                print("❌ Notion API 連接失敗")
                return False
            
            success = client.create_district_house_list(
                properties=property_objects,
                search_date=datetime.now(),
                district_name="台北",
                comparison=comparison
            )
            
            if success:
                print("✅ 成功上傳到 Notion！")
                return True
            else:
                print("❌ Notion 上傳失敗")
                return False
        
        except Exception as e:
            print(f"❌ Notion 上傳錯誤: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """主程式"""
    import argparse
    
    parser = argparse.ArgumentParser(description='信義房屋台北公寓物件爬蟲')
    parser.add_argument('district', 
                       nargs='?',
                       default='taipei',
                       help='只支援台北區域')
    
    args = parser.parse_args()
    
    if args.district not in ['taipei']:
        print("❌ 此爬蟲只支援台北區域")
        print("💡 如需蘆洲或三重，請使用: python sanchong_luzhou_crawler.py")
        return
    
    print("🏠 信義房屋台北公寓物件爬蟲")
    print("=" * 50)
    
    try:
        crawler = TaipeiApartmentCrawler()
        
        # 1. 載入前一天的資料
        print("📂 載入前一天的資料...")
        previous_data = crawler.load_previous_data()
        
        # 2. 爬取今天的資料
        properties = crawler.crawl_all_pages()
        
        if not properties:
            print("❌ 沒有爬取到任何資料")
            return
        
        print(f"📈 首次爬取，所有物件都是新的")
        
        # 3. 與前一天比較
        comparison = crawler.compare_with_previous(properties, previous_data)
        print(f"📈 {comparison['message']}")
        
        # 顯示詳細比較資訊
        print(f"\n🔍 台北區域詳細比較資訊:")
        print(f"  • has_previous_data: {comparison.get('has_previous_data', False)}")
        print(f"  • 前一天物件數: {comparison.get('previous_count', 0)}")
        print(f"  • 今天物件數: {comparison.get('current_count', 0)}")
        print(f"  • 新增物件數: {comparison.get('total_new', 0)}")
        print(f"  • 下架物件數: {comparison.get('total_removed', 0)}")
        print(f"  • 變價物件數: {comparison.get('total_price_changed', 0)}")
        
        if comparison.get('new_properties'):
            print(f"  🆕 新增物件範例:")
            for i, prop in enumerate(comparison['new_properties'][:3], 1):
                print(f"    {i}. {prop['title'][:30]}... - {prop['price']}萬")
        
        if comparison.get('price_changed_properties'):
            print(f"  💰 變價物件範例:")
            for i, change in enumerate(comparison['price_changed_properties'][:2], 1):
                prop = change['property']
                print(f"    {i}. {prop['title'][:30]}... : {change['old_price']} → {change['new_price']}萬")
        
        if not comparison.get('new_properties') and not comparison.get('price_changed_properties'):
            print(f"  ✅ 台北區域今天沒有新增或變價物件")
        
        # 4. 儲存本地檔案
        json_file = crawler.save_to_local_file(properties)
        print(f"📁 已儲存到: {json_file}")
        
        # 5. 上傳到 Notion
        print("🔄 正在上傳到 Notion...")
        notion_success = crawler.upload_to_notion(properties, comparison)
        
        if notion_success:
            print("✅ 成功上傳到 Notion！")
        else:
            print("⚠️  Notion 上傳失敗或跳過")
        
        print(f"🎉 台北區域爬取完成！")
        
    except Exception as e:
        print(f"\n❌ 台北區域執行錯誤: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
