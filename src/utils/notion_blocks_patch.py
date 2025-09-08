"""
Notion blocks 生成的補丁函數
用於改進 _generate_district_blocks 函數，使其只顯示有變化的物件
"""

from typing import List, Dict
from datetime import datetime
from ..models.property import Property


def generate_optimized_district_blocks(properties: List[Property], search_date: datetime, district_name: str, comparison: Dict = None) -> List[Dict]:
    """生成優化的區域物件清單 Notion 頁面內容塊（只顯示有變化的物件）"""
    blocks = []
    
    # 區域標題和搜尋條件
    property_type = "公寓" if district_name == '台北' else "華廈大樓"
    search_url = _get_search_url(district_name)
    
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
        
        # 如果沒有任何變化
        if not comparison['new_properties'] and not comparison['removed_properties'] and not comparison['price_changed_properties']:
            summary_text += f"\n✅ 物件狀況無變化"
        
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
        
        # 如果沒有變化，直接返回摘要即可
        if not comparison['new_properties'] and not comparison['price_changed_properties']:
            blocks.append({
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": f"✅ {district_name}區今日無新增或價格變動物件，物件狀況與昨日相同。"}
                        }
                    ],
                    "icon": {"emoji": "✅"}
                }
            })
            return blocks
    
    # 如果有物件要顯示，添加物件詳情
    if properties:
        # 搜尋摘要（只針對要顯示的物件）
        stats = _calculate_stats(properties)
        
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": f"📋 {district_name}區變化物件詳情"}
                    }
                ]
            }
        })
        
        if comparison and comparison.get('has_previous_data'):
            # 如果有比較資料，說明只顯示有變化的物件
            summary_text = f"""本次顯示：{len(properties)} 筆（僅新增和價格變動）
平均價格：{stats.get('avg_price', 0):,.0f} 萬元
平均坪數：{stats.get('avg_size', 0):.1f} 坪"""
        else:
            # 如果沒有比較資料，顯示完整統計
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
        
        # 物件詳情 - 限制顯示數量避免超過 Notion 限制
        max_properties_per_page = 15  
        displayed_properties = properties[:max_properties_per_page]
        
        if len(properties) > max_properties_per_page:
            blocks.append({
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": f"⚠️ 因頁面限制，此處僅顯示前 {max_properties_per_page} 個物件。總共有 {len(properties)} 個變化物件，其餘物件請參考本地 JSON 檔案。"}
                        }
                    ],
                    "icon": {"emoji": "⚠️"}
                }
            })
        
        for i, prop in enumerate(displayed_properties, 1):
            # 物件標題
            title_text = f"🏠 {i}. {prop.title}"
            
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
    
    return blocks


def _get_search_url(district_name: str) -> str:
    """獲取對應區域的搜尋 URL"""
    urls = {
        '蘆洲': 'https://www.sinyi.com.tw/buy/list/3000-down-price/huaxia-dalou-type/20-up-balconyarea/3-5-roomtotal/NewTaipei-city/247-zip/default-desc',
        '三重': 'https://www.sinyi.com.tw/buy/list/3000-down-price/huaxia-dalou-type/20-up-balconyarea/3-5-roomtotal/NewTaipei-city/241-zip/default-desc',
        '台北': 'https://www.sinyi.com.tw/buy/list/3000-down-price/apartment-type/20-up-balconyarea/3-5-roomtotal/1-3-floor/Taipei-city/100-103-104-105-106-108-110-115-zip/default-desc'
    }
    return urls.get(district_name, 'https://www.sinyi.com.tw')


def _calculate_stats(properties: List[Property]) -> Dict[str, float]:
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
