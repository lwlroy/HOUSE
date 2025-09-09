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
    """添加物件列表"""
    
    for i, prop in enumerate(properties[:20], 1):  # 限制顯示前20個
        title = prop.get('title', 'Unknown Property')
        price = prop.get('price', 0)
        address = prop.get('address', 'Unknown Address')
        source_url = prop.get('source_url', '#')
        
        # 檢查是否有價格變動資訊
        price_change_info = prop.get('_price_change_info')
        if price_change_info:
            old_price = price_change_info['old_price']
            new_price = price_change_info['new_price']
            change_amount = price_change_info['change']
            change_emoji = "📈" if change_amount > 0 else "📉"
            title = f"{title} {change_emoji} 價格變動: {old_price:,}→{new_price:,}萬"
        
        blocks.append({
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": f"{i}. {title[:60]}..."}
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
                        "text": {"content": f"💰 價格：{price:,} 萬元"}
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
                        "text": {"content": f"📍 地址：{address}"}
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
                        "text": {"content": "🔗 查看詳情："},
                        "annotations": {"bold": True}
                    },
                    {
                        "type": "text",
                        "text": {"content": source_url, "link": {"url": source_url}}
                    }
                ]
            }
        })
        
        # 分隔線
        blocks.append({
            "object": "block",
            "type": "divider",
            "divider": {}
        })
