"""
Notion 區塊數量限制修復補丁
解決 "body.child                    "text": {"content": f"🏠 {district_display}區{property_type}搜尋結果"}en.length should be ≤ 100" 錯誤
"""

from typing import List, Dict
from datetime import datetime
from ..models.property import Property

def generate_optimized_district_blocks(properties: List[Property], search_date: datetime, district_name: str, comparison: Dict = None) -> List[Dict]:
    """
    生成優化的 Notion 區塊，確保不超過 100 個區塊限制
    """
    blocks = []
    
    # 1. 標題和基本資訊 (3個區塊)
    if district_name in ['sanchong_luzhou', 'sanchongluzhou']:
        district_display = "三重蘆洲"
        property_type = "華廈大樓"
        search_url = "https://www.sinyi.com.tw/buy/list/3000-down-price/dalou-huaxia-type/20-up-balconyarea/3-5-roomtotal/NewTaipei-city/241-247-zip/default-desc/1"
    elif district_name == '台北':
        district_display = "台北"
        property_type = "公寓"
        search_url = "https://www.sinyi.com.tw/buy/list/3000-down-price/apartment-type/20-up-balconyarea/3-5-roomtotal/1-3-floor/Taipei-city/100-103-104-105-106-108-110-115-zip/default-desc/1"
    else:
        district_display = district_name
        property_type = "華廈大樓"
        search_url = "https://www.sinyi.com.tw"
    
    blocks.append({
        "object": "block",
        "type": "heading_1",
        "heading_1": {
            "rich_text": [
                {
                    "type": "text",
                    "text": {"content": f"� {district_name}區{property_type}搜尋結果"}
                }
            ]
        }
    })
    
    blocks.append({
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [
                {
                    "type": "text",
                    "text": {"content": f"📅 搜尋日期：{search_date.strftime('%Y年%m月%d日')}"}
                }
            ]
        }
    })
    
    blocks.append({
        "object": "block",
        "type": "callout",
        "callout": {
            "rich_text": [
                {
                    "type": "text",
                    "text": {"content": f"🎯 搜尋條件：{district_display}區 | {property_type} | 20坪+ | 3-5房 | 3000萬內 "},
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
    
    # 2. 搜尋摘要 (1個區塊)
    if properties:
        stats = _calculate_stats(properties)
        summary_text = f"""📊 搜尋摘要
找到物件：{len(properties)} 筆
平均價格：{stats.get('avg_price', 0):,.0f} 萬元
平均坪數：{stats.get('avg_size', 0):.1f} 坪
價格區間：{stats.get('min_price', 0):,} - {stats.get('max_price', 0):,} 萬元"""
        
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
    
    # 3. 比較資訊 (如有需要，1-2個區塊)
    if comparison and comparison.get('has_previous_data'):
        change = comparison['current_count'] - comparison['previous_count']
        change_text = ""
        if change > 0:
            change_text = f"📈 淨增加 +{change} 筆"
        elif change < 0:
            change_text = f"📉 淨減少 {abs(change)} 筆"
        else:
            change_text = "➡️ 數量相同"
        
        comparison_text = f"""📊 與昨日比較
昨日物件：{comparison['previous_count']} 筆
今日物件：{comparison['current_count']} 筆
{change_text}"""
        
        # 檢查是否有變更
        has_changes = (
            comparison.get('new_properties', []) or 
            comparison.get('removed_properties', []) or 
            comparison.get('price_changed_properties', [])
        )
        
        if has_changes:
            if comparison.get('new_properties'):
                comparison_text += f"\n🆕 新增物件：{len(comparison['new_properties'])} 筆"
            if comparison.get('removed_properties'):
                comparison_text += f"\n� 下架物件：{len(comparison['removed_properties'])} 筆"
            if comparison.get('price_changed_properties'):
                comparison_text += f"\n💰 價格變動：{len(comparison['price_changed_properties'])} 筆"
        else:
            comparison_text += f"\n✅ 無任何異動"
        
        blocks.append({
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": comparison_text}
                    }
                ],
                "icon": {"emoji": "📊"},
                "color": "blue_background"
            }
        })
    
    # 4. 計算還能容納多少個物件 (每個物件 2 個區塊：標題 + 內容)
    current_block_count = len(blocks)
    remaining_capacity = 100 - current_block_count - 2  # 預留2個區塊給標題和說明
    max_properties = min(remaining_capacity // 2, len(properties), 40)
    
    # 5. 決定顯示哪些物件
    properties_to_show = []
    
    if comparison and comparison.get('has_previous_data'):
        # 優先顯示新增和變動的物件
        if comparison.get('new_properties'):
            properties_to_show.extend([prop.__dict__ if hasattr(prop, '__dict__') else prop for prop in comparison['new_properties']])
        
        if comparison.get('price_changed_properties'):
            for change_info in comparison['price_changed_properties']:
                prop_dict = change_info['property'].__dict__ if hasattr(change_info['property'], '__dict__') else change_info['property']
                prop_dict['_price_change_info'] = change_info
                properties_to_show.append(prop_dict)
        
        # 如果還有空間，添加其他物件
        if len(properties_to_show) < max_properties:
            remaining_slots = max_properties - len(properties_to_show)
            other_properties = [prop for prop in properties if not _is_in_changes(prop, comparison)]
            properties_to_show.extend([prop.__dict__ if hasattr(prop, '__dict__') else prop for prop in other_properties[:remaining_slots]])
    else:
        # 沒有比較資料，顯示所有物件（受限於容量）
        properties_to_show = [prop.__dict__ if hasattr(prop, '__dict__') else prop for prop in properties[:max_properties]]
    
    # 6. 物件清單標題
    if properties_to_show:
        title_text = f"🏠 物件清單 (顯示 {len(properties_to_show)} / {len(properties)} 筆)"
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": title_text}
                    }
                ]
            }
        })
        
        # 7. 物件詳情
        for i, prop in enumerate(properties_to_show, 1):
            # 物件標題
            title = prop.get('title', 'Unknown Property')
            price = prop.get('total_price', prop.get('price', 0))
            
            # 檢查價格變動
            price_change_info = prop.get('_price_change_info')
            if price_change_info:
                old_price = price_change_info['old_price']
                new_price = price_change_info['new_price']
                change_emoji = "📈" if price_change_info['change'] > 0 else "📉"
                title += f" {change_emoji} {old_price:,}→{new_price:,}萬"
            
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": f"{i}. {title[:50]}{'...' if len(title) > 50 else ''}"}
                        }
                    ]
                }
            })
            
            # 物件詳細資訊 (合併到單一區塊)
            info_lines = []
            info_lines.append(f"💰 價格：{price:,} 萬元")
            
            if prop.get('address'):
                info_lines.append(f"📍 地址：{prop.get('address')}")
            
            room_count = prop.get('room_count', 0)
            living_room_count = prop.get('living_room_count', 0)
            bathroom_count = prop.get('bathroom_count', 0)
            if room_count and living_room_count and bathroom_count:
                info_lines.append(f"🏢 房型：{room_count}房{living_room_count}廳{bathroom_count}衛")
            
            size = prop.get('size', 0) or prop.get('main_area', 0)
            if size:
                info_lines.append(f"📐 坪數：{size} 坪")
            
            if prop.get('floor'):
                info_lines.append(f"🏗️ 樓層：{prop.get('floor')}")
            
            info_text = "\n".join(info_lines)
            
            # 構建富文本
            rich_text_content = [
                {
                    "type": "text",
                    "text": {"content": info_text}
                }
            ]
            
            # 添加連結
            source_url = prop.get('source_url')
            if source_url:
                rich_text_content.extend([
                    {
                        "type": "text",
                        "text": {"content": "\n🔗 查看詳情："}
                    },
                    {
                        "type": "text",
                        "text": {
                            "content": "點擊前往",
                            "link": {"url": source_url}
                        },
                        "annotations": {
                            "color": "blue",
                            "underline": True
                        }
                    }
                ])
            
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": rich_text_content
                }
            })
    
    # 8. 如果有物件被省略，添加說明
    if len(properties) > len(properties_to_show):
        omitted_count = len(properties) - len(properties_to_show)
        blocks.append({
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": f"⚠️ 因 Notion 區塊限制，省略了 {omitted_count} 個物件。完整清單請查看本地 JSON 檔案。"}
                    }
                ],
                "icon": {"emoji": "⚠️"},
                "color": "yellow_background"
            }
        })
    
    print(f"🔢 生成的 Notion 區塊數量: {len(blocks)} (限制: 100)")
    return blocks

def _calculate_stats(properties: List[Property]) -> Dict[str, float]:
    """計算統計資訊"""
    if not properties:
        return {}
    
    prices = []
    sizes = []
    
    for prop in properties:
        # 處理價格
        if hasattr(prop, 'total_price') and prop.total_price and prop.total_price > 0:
            prices.append(prop.total_price)
        elif hasattr(prop, 'price') and prop.price and prop.price > 0:
            prices.append(prop.price)
        
        # 處理坪數
        if hasattr(prop, 'main_area') and prop.main_area and prop.main_area > 0:
            sizes.append(prop.main_area)
        elif hasattr(prop, 'size') and prop.size and prop.size > 0:
            sizes.append(prop.size)
    
    stats = {}
    
    if prices:
        stats['avg_price'] = sum(prices) / len(prices)
        stats['min_price'] = min(prices)
        stats['max_price'] = max(prices)
    
    if sizes:
        stats['avg_size'] = sum(sizes) / len(sizes)
    
    return stats

def _is_in_changes(prop: Property, comparison: Dict) -> bool:
    """檢查物件是否在變更清單中"""
    if not comparison:
        return False
    
    prop_dict = prop.__dict__ if hasattr(prop, '__dict__') else prop
    
    # 檢查新增物件
    for new_prop in comparison.get('new_properties', []):
        if _properties_match(prop_dict, new_prop):
            return True
    
    # 檢查價格變動物件
    for change_info in comparison.get('price_changed_properties', []):
        if _properties_match(prop_dict, change_info['property']):
            return True
    
    return False

def _properties_match(prop1, prop2) -> bool:
    """檢查兩個物件是否相同"""
    if hasattr(prop1, 'get') and hasattr(prop2, 'get'):
        # 字典模式
        return (prop1.get('address') == prop2.get('address') and 
                prop1.get('room_count') == prop2.get('room_count') and
                (prop1.get('main_area') or prop1.get('size')) == (prop2.get('main_area') or prop2.get('size')))
    else:
        # 物件模式
        return (getattr(prop1, 'address', '') == getattr(prop2, 'address', '') and 
                getattr(prop1, 'room_count', 0) == getattr(prop2, 'room_count', 0) and
                (getattr(prop1, 'main_area', 0) or getattr(prop1, 'size', 0)) == 
                (getattr(prop2, 'main_area', 0) or getattr(prop2, 'size', 0)))
