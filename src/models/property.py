from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class Property:
    """房屋資料模型（支援租屋和買屋）"""
    
    # 必填欄位
    id: str
    title: str
    address: str
    district: str
    region: str
    price: int  # 月租金或售價（萬元）
    room_count: int
    living_room_count: int
    bathroom_count: int
    size: float  # 坪數
    floor: str
    source_site: str
    source_url: str
    
    # 選填欄位 - 物件類型
    property_type: str = 'rent'  # 'rent' 或 'sale'
    
    # 選填欄位 - 價格資訊
    price_per_ping: Optional[float] = None
    deposit: Optional[int] = None
    management_fee: Optional[int] = None
    
    # 買屋專用欄位
    total_price: Optional[int] = None  # 總價（萬元）
    unit_price: Optional[float] = None  # 單價（萬/坪）
    main_area: Optional[float] = None  # 主建物坪數
    subsidiary_area: Optional[float] = None  # 附屬建物坪數
    public_area: Optional[float] = None  # 公設坪數
    land_area: Optional[float] = None  # 土地坪數
    building_type: Optional[str] = None  # 建物類型（華廈、公寓、透天等）
    
    # 選填欄位 - 房屋規格
    total_floors: Optional[int] = None
    house_type: Optional[str] = None  # 公寓、電梯大樓等
    age: Optional[int] = None  # 屋齡
    direction: Optional[str] = None  # 座向
    parking: Optional[bool] = None  # 是否有停車位
    parking_space: Optional[int] = None  # 車位數量
    
    # 選填欄位 - 設備與特色
    features: List[str] = None
    equipment: List[str] = None
    
    # 選填欄位 - 聯絡資訊
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    agent_name: Optional[str] = None  # 仲介姓名
    
    # 選填欄位 - 其他
    image_urls: List[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        """初始化後處理"""
        if self.features is None:
            self.features = []
        if self.equipment is None:
            self.equipment = []
        if self.image_urls is None:
            self.image_urls = []
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'id': self.id,
            'title': self.title,
            'address': self.address,
            'district': self.district,
            'region': self.region,
            'price': self.price,
            'property_type': self.property_type,
            'price_per_ping': self.price_per_ping,
            'deposit': self.deposit,
            'management_fee': self.management_fee,
            'total_price': self.total_price,
            'unit_price': self.unit_price,
            'main_area': self.main_area,
            'subsidiary_area': self.subsidiary_area,
            'public_area': self.public_area,
            'land_area': self.land_area,
            'building_type': self.building_type,
            'room_count': self.room_count,
            'living_room_count': self.living_room_count,
            'bathroom_count': self.bathroom_count,
            'size': self.size,
            'floor': self.floor,
            'total_floors': self.total_floors,
            'house_type': self.house_type,
            'age': self.age,
            'direction': self.direction,
            'parking': self.parking,
            'parking_space': self.parking_space,
            'features': self.features,
            'equipment': self.equipment,
            'contact_name': self.contact_name,
            'contact_phone': self.contact_phone,
            'agent_name': self.agent_name,
            'source_site': self.source_site,
            'source_url': self.source_url,
            'image_urls': self.image_urls,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_fingerprint(self) -> str:
        """生成用於去重的指紋"""
        # 使用地址、價格、坪數、房數來生成指紋
        fingerprint_data = f"{self.address}_{self.price}_{self.size}_{self.room_count}_{self.property_type}"
        return fingerprint_data.lower().replace(' ', '')


@dataclass
class SearchParams:
    """搜尋參數模型（支援租屋和買屋）"""
    
    # 物件類型
    property_type: str = 'rent'  # 'rent' 或 'sale'
    
    # 地區條件
    region: Optional[str] = None
    district: Optional[str] = None
    
    # 價格條件（租屋：月租金，買屋：總價萬元）
    price_min: Optional[int] = None
    price_max: Optional[int] = None
    
    # 房屋條件
    room_count_min: Optional[int] = None
    room_count_max: Optional[int] = None
    size_min: Optional[float] = None
    size_max: Optional[float] = None
    
    # 買屋專用條件
    main_area_min: Optional[float] = None  # 主建物最小坪數
    main_area_max: Optional[float] = None  # 主建物最大坪數
    unit_price_min: Optional[float] = None  # 單價最低（萬/坪）
    unit_price_max: Optional[float] = None  # 單價最高（萬/坪）
    building_types: List[str] = None  # 建物類型列表
    
    # 樓層條件
    floor_min: Optional[int] = None
    floor_max: Optional[int] = None
    exclude_top_floor: bool = False
    exclude_ground_floor: bool = False
    
    # 其他條件
    house_types: List[str] = None
    has_parking: Optional[bool] = None
    parking_space_min: Optional[int] = None
    age_max: Optional[int] = None
    
    # 搜尋設定
    max_results: int = 100
    sort_by: str = 'price'
    sort_order: str = 'asc'
    
    def __post_init__(self):
        if self.house_types is None:
            self.house_types = []
        if self.building_types is None:
            self.building_types = []
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {k: v for k, v in self.__dict__.items() if v is not None}
    
    def is_sale_search(self) -> bool:
        """是否為買屋搜尋"""
        return self.property_type == 'sale'
    
    def is_rent_search(self) -> bool:
        """是否為租屋搜尋"""
        return self.property_type == 'rent'
