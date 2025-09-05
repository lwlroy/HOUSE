"""
超簡化版 Notion API 整合
使用內建的 urllib，不需要額外依賴
"""

import json
import urllib.request
import urllib.parse
from datetime import datetime
from typing import List, Dict, Any, Optional

from ..models.property import Property


class UltraSimpleNotionClient:
    """超簡化版 Notion API 客戶端"""
    
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
    
    def create_daily_house_note_simple(self, properties: List[Property], search_date: datetime = None) -> bool:
        """創建簡化版每日搜屋筆記 - 輸出到檔案而非Notion"""
        if search_date is None:
            search_date = datetime.now()
        
        title = search_date.strftime("%Y/%m/%d搜屋筆記")
        
        # 生成 Markdown 內容
        markdown_content = self._generate_markdown_content(properties, search_date)
        
        # 儲存為 Markdown 檔案
        filename = f"notion_ready_{search_date.strftime('%Y%m%d')}.md"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            print(f"✅ 已生成 Notion 格式檔案: {filename}")
            print("📝 你可以手動複製內容到 Notion，或設定 Integration 權限後自動上傳")
            return True
            
        except Exception as e:
            print(f"❌ 生成檔案失敗: {str(e)}")
            return False
    
    def _generate_markdown_content(self, properties: List[Property], search_date: datetime) -> str:
        """生成 Markdown 格式的內容"""
        content = f"# 🏠 {search_date.strftime('%Y年%m月%d日')} 台北市買屋搜尋\n\n"
        
        # 搜尋條件
        content += "> 🎯 **搜尋條件：** 台北市全區 | 主建物20坪+ | 1-3樓 | 3000萬內 | 3-5房\n\n"
        
        if not properties:
            content += "❌ 沒有找到符合條件的物件\n"
            return content
        
        # 統計摘要
        stats = self._calculate_stats(properties)
        content += f"## 📊 搜尋摘要\n\n"
        content += f"- **找到物件：** {len(properties)} 筆\n"
        content += f"- **平均價格：** {stats['avg_price']:,.0f} 萬元\n"
        content += f"- **平均坪數：** {stats['avg_size']:.1f} 坪\n"
        content += f"- **價格區間：** {stats['min_price']:,} - {stats['max_price']:,} 萬元\n\n"
        
        # 物件列表
        content += "## 🏘️ 物件詳情\n\n"
        
        for i, prop in enumerate(properties, 1):
            content += f"### 🏠 物件 {i}: {prop.title}\n\n"
            
            content += f"- **📍 地址：** {prop.address}\n"
            content += f"- **💰 總價：** {prop.total_price:,} 萬元"
            
            if prop.unit_price:
                content += f" (單價: {prop.unit_price:.1f} 萬/坪)"
            
            content += f"\n- **🏢 房型：** {prop.room_count}房{prop.living_room_count}廳{prop.bathroom_count}衛\n"
            content += f"- **📐 坪數：** {prop.size} 坪"
            
            if prop.main_area and prop.main_area != prop.size:
                content += f" (主建物: {prop.main_area} 坪)"
            
            content += f"\n- **🏗️ 樓層：** {prop.floor}"
            if prop.total_floors:
                content += f"/{prop.total_floors}樓"
            
            if prop.age:
                content += f"\n- **📅 屋齡：** {prop.age} 年"
            
            if prop.building_type:
                content += f"\n- **🏘️ 建物類型：** {prop.building_type}"
            
            content += f"\n- **🔗 來源：** {prop.source_site}"
            
            if prop.source_url and prop.source_url.startswith('http'):
                content += f"\n- **🔗 詳情連結：** [查看詳情]({prop.source_url})"
            
            content += "\n\n---\n\n"
        
        return content
    
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
    
    def show_notion_setup_guide(self):
        """顯示 Notion 設定指南"""
        print("\n📋 Notion Integration 設定指南:")
        print("="*50)
        print("1. 前往 https://www.notion.so/my-integrations")
        print("2. 點擊 'New integration' 創建新的整合")
        print("3. 設定 Integration 名稱 (例如: 'House Search Bot')")
        print("4. 選擇關聯的工作區")
        print("5. 確認權限包含:")
        print("   ✅ Read content")
        print("   ✅ Update content") 
        print("   ✅ Insert content")
        print("6. 複製 Integration Token (以 secret_ 開頭)")
        print("7. 在 Notion 中創建一個頁面作為筆記本")
        print("8. 在該頁面點擊 'Share' → 'Invite' → 選擇你的 Integration")
        print("9. 給予 'Edit' 權限")
        print()
        print("🔧 如果仍然失敗，可以:")
        print("- 手動複製生成的 Markdown 檔案內容到 Notion")
        print("- 或聯絡我協助除錯 API 設定")


def create_ultra_simple_notion_client(api_key: str) -> UltraSimpleNotionClient:
    """創建超簡化版 Notion 客戶端"""
    return UltraSimpleNotionClient(api_key=api_key)
