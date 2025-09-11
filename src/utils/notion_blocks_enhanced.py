"""
Notion 區塊生成優化版本 - 支援無變更情況的顯示
"""

from typing import List, Dict
from datetime import datetime
from src.models.property import Property

def generate_optimized_district_blocks(properties: List[Property], search_date: datetime, district_name: str, comparison: Dict = None) -> List[Dict]:
    """
    生成優化的區域物件 Notion 區塊（增強版：支援無變更情況顯示）
    """
    blocks = []
    
    # 標題
    blocks.append({
        "object": "block",
        "type": "heading_1",
        "heading_1": {
            "rich_text": [
                {
                    "type": "text",
                    "text": {"content": f"🏠 {district_name}區房屋搜尋結果"}
                }
            ]
        }
    })
    
    # 搜尋日期
    date_str = search_date.strftime('%Y年%m月%d日')
    blocks.append({
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [
                {
                    "type": "text",
                    "text": {"content": f"📅 搜尋日期：{date_str}"}
                }
            ]
        }
    })
    
    # 比較資訊區塊（增強版）
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
        
        # 檢查是否有任何變更
        has_changes = (
            comparison.get('new_properties', []) or 
            comparison.get('removed_properties', []) or 
            comparison.get('price_changed_properties', [])
        )
        
        if has_changes:
            if comparison.get('new_properties'):
                summary_text += f"\n🆕 新增物件：{len(comparison['new_properties'])} 筆"
            
            if comparison.get('removed_properties'):
                summary_text += f"\n📤 下架物件：{len(comparison['removed_properties'])} 筆"
            
            if comparison.get('price_changed_properties'):
                summary_text += f"\n💰 價格變動：{len(comparison['price_changed_properties'])} 筆"
        else:
            # 沒有任何變更的情況
            summary_text += f"\n✅ 無任何異動"
        
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
        
        # 如果沒有變更，顯示「無變更」說明區塊
        if not has_changes:
            blocks.append({
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "🔄 今日與昨日物件完全相同，無新增、下架或價格變動。"}
                        }
                    ],
                    "icon": {"emoji": "✅"},
                    "color": "green_background"
                }
            })
        else:
            # 有變更時，顯示詳細變更內容
            _add_change_details(blocks, comparison)
    
    # 搜尋摘要
    if properties:
        _add_search_summary(blocks, properties, district_name)
    
    # 物件列表（只顯示有變化的物件，如果沒有比較資料則顯示所有）
    if comparison and comparison.get('has_previous_data'):
        # 有比較資料時，只顯示有變化的物件
        properties_to_show = []
        
        if comparison.get('new_properties'):
            properties_to_show.extend(comparison['new_properties'])
        
        if comparison.get('price_changed_properties'):
            for change_info in comparison['price_changed_properties']:
                prop = change_info['property']
                # 標記價格變動
                prop['_price_change_info'] = change_info
                properties_to_show.append(prop)
        
        if properties_to_show:
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": f"🏠 有變化的物件清單 ({len(properties_to_show)} 筆)"}
                        }
                    ]
                }
            })
            
            _add_property_list(blocks, properties_to_show)
        else:
            # 沒有變化的物件時，顯示說明
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "🏠 物件清單"}
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
                            "text": {"content": "今日無新增或價格變動物件，所有物件與昨日相同。"}
                        }
                    ]
                }
            })
    else:
        # 沒有比較資料時，顯示所有物件
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": f"🏠 全部物件清單 ({len(properties)} 筆)"}
                    }
                ]
            }
        })
        
        _add_property_list(blocks, [prop.__dict__ for prop in properties])
    
    return blocks

def _add_change_details(blocks: List[Dict], comparison: Dict):
    """添加變更詳情"""
    
    if comparison.get('new_properties'):
        blocks.append({
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": f"🆕 新增物件 ({len(comparison['new_properties'])} 筆)"}
                    }
                ]
            }
        })
    
    if comparison.get('price_changed_properties'):
        blocks.append({
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": f"💰 價格變動 ({len(comparison['price_changed_properties'])} 筆)"}
                    }
                ]
            }
        })
        
        for change_info in comparison['price_changed_properties'][:5]:  # 只顯示前5個
            prop = change_info['property']
            old_price = change_info['old_price']
            new_price = change_info['new_price']
            change_amount = change_info['change']
            
            change_emoji = "📈" if change_amount > 0 else "📉"
            change_text = f"+{change_amount}" if change_amount > 0 else str(change_amount)
            
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": f"{change_emoji} {prop.get('title', 'Unknown')[:50]}..."}
                        }
                    ]
                }
            })
            
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": f"   💰 {old_price:,} → {new_price:,} 萬元 ({change_text:+}萬)"}
                        }
                    ]
                }
            })
    
    if comparison.get('removed_properties'):
        blocks.append({
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": f"📤 下架物件 ({len(comparison['removed_properties'])} 筆)"}
                    }
                ]
            }
        })
        
        for prop in comparison['removed_properties'][:5]:  # 只顯示前5個
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": f"📤 {prop.get('title', 'Unknown')[:50]}... - {prop.get('price', 'Unknown')}萬元"}
                        }
                    ]
                }
            })

def _add_search_summary(blocks: List[Dict], properties: List, district_name: str):
    """添加搜尋摘要"""
    
    # 計算統計資料
    prices = [prop.total_price for prop in properties if hasattr(prop, 'total_price') and prop.total_price > 0]
    sizes = [prop.size for prop in properties if hasattr(prop, 'size') and prop.size > 0]
    
    if prices:
        avg_price = sum(prices) / len(prices)
        min_price = min(prices)
        max_price = max(prices)
    else:
        avg_price = min_price = max_price = 0
    
    if sizes:
        avg_size = sum(sizes) / len(sizes)
    else:
        avg_size = 0
    
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
平均價格：{avg_price:,.0f} 萬元
平均坪數：{avg_size:.1f} 坪
價格區間：{min_price:,} - {max_price:,} 萬元"""
    
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

def _add_property_list(blocks: List[Dict], properties: List[Dict]):
    """添加物件列表（合併版本，避免超過 Notion 區塊限制）"""
    
    # 計算可安全顯示的物件數量（每個物件2個區塊：標題+內容）
    # 目前已有的區塊數量
    current_blocks = len(blocks)
    # 預留一些空間給其他區塊
    remaining_capacity = 100 - current_blocks - 5
    max_properties = min(remaining_capacity // 2, len(properties), 30)  # 每個物件最多2個區塊
    
    if max_properties <= 0:
        # 如果空間不足，使用摘要模式
        blocks.append({
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": f"⚠️ 因 Notion 區塊限制，無法顯示所有物件詳情。總共找到 {len(properties)} 個物件，請查看本地 JSON 檔案獲取完整資料。"}
                    }
                ],
                "icon": {"emoji": "⚠️"},
                "color": "yellow_background"
            }
        })
        return
    
    for i, prop in enumerate(properties[:max_properties], 1):
        title = prop.get('title', 'Unknown Property')
        price = prop.get('price', 0)
        address = prop.get('address', 'Unknown Address')
        source_url = prop.get('source_url', '#')
        room_count = prop.get('room_count', 0)
        living_room_count = prop.get('living_room_count', 0)
        bathroom_count = prop.get('bathroom_count', 0)
        size = prop.get('size', 0)
        
        # 檢查是否有價格變動資訊
        price_change_info = prop.get('_price_change_info')
        if price_change_info:
            old_price = price_change_info['old_price']
            new_price = price_change_info['new_price']
            change_amount = price_change_info['change']
            change_emoji = "📈" if change_amount > 0 else "📉"
            title = f"{title} {change_emoji} 價格變動: {old_price:,}→{new_price:,}萬"
        
        # 物件標題
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
        
        # 合併所有物件資訊到單一區塊中
        info_text = f"💰 價格：{price:,} 萬元\n📍 地址：{address}"
        
        if room_count and living_room_count and bathroom_count:
            info_text += f"\n🏢 房型：{room_count}房{living_room_count}廳{bathroom_count}衛"
        
        if size:
            info_text += f"\n📐 坪數：{size} 坪"
        
        # 創建富文本內容，包含連結
        rich_text_content = [
            {
                "type": "text",
                "text": {"content": info_text}
            }
        ]
        
        # 添加連結
        if source_url and source_url != '#':
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
    
    # 如果有更多物件未顯示，添加說明
    if len(properties) > max_properties:
        blocks.append({
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": f"📋 共找到 {len(properties)} 個物件，此處顯示前 {max_properties} 個。完整清單請查看本地 JSON 檔案。"}
                    }
                ],
                "icon": {"emoji": "📋"},
                "color": "blue_background"
            }
        })
