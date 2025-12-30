"""
数据模型定义模块

本模块定义了系统中使用的数据模型类，用于创建符合MongoDB文档结构的字典对象。
这些模型类遵循MongoDB文档数据库的设计模式，使用内嵌文档存储相关数据。

主要模型：
1. Device - 设备模型，包含地理位置信息（GeoJSON格式）
2. DeviceLog - 设备日志模型，包含日志内容和详细信息

作者: 数据库系统课程项目小组
"""

from datetime import datetime
from typing import Optional, Dict, Any

class Device:
    """
    设备数据模型类
    
    用于创建和表示智能家居设备的数据结构。
    设备文档包含以下字段：
    - device_id: 设备唯一标识符
    - name: 设备名称
    - type: 设备类型
    - location: 地理位置信息（GeoJSON Point格式，用于地理位置查询）
    - status: 设备状态
    - config: 设备配置信息（内嵌文档，不同设备类型有不同的配置项）
    - created_at: 创建时间
    - updated_at: 更新时间
    """
    
    @staticmethod
    def create(device_id: str, name: str, device_type: str, 
               location: Dict[str, float], status: str = 'online',
               config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        创建设备文档
        
        该方法创建一个符合MongoDB文档格式的设备对象。
        使用GeoJSON格式存储地理位置信息，支持MongoDB的2dsphere索引和地理位置查询。
        
        Args:
            device_id: 设备唯一标识（字符串，如：DEV0001）
            name: 设备名称（字符串，如：智能灯_0001）
            device_type: 设备类型（字符串，如：智能灯、温湿度传感器、摄像头等）
            location: 位置信息字典，包含：
                - longitude: 经度（float，范围：-180到180）
                - latitude: 纬度（float，范围：-90到90）
            status: 设备状态（字符串，可选值：online/offline/maintenance，默认：online）
            config: 设备配置信息字典（可选，内嵌文档）
                不同设备类型有不同的配置项，例如：
                - 智能灯: brightness（亮度）, color（颜色）, power_consumption（功耗）
                - 温湿度传感器: temperature_range（温度范围）, humidity_range（湿度范围）
                - 摄像头: resolution（分辨率）, night_vision（夜视功能）
        
        Returns:
            Dict[str, Any]: 设备文档字典，可直接插入MongoDB
        
        示例:
            >>> device = Device.create(
            ...     device_id='DEV0001',
            ...     name='客厅智能灯',
            ...     device_type='智能灯',
            ...     location={'longitude': 113.2644, 'latitude': 23.1291},
            ...     status='online',
            ...     config={'brightness': 80, 'color': 'white'}
            ... )
        """
        device = {
            'device_id': device_id,  # 设备唯一标识
            'name': name,  # 设备名称
            'type': device_type,  # 设备类型
            # 地理位置信息使用GeoJSON Point格式
            # MongoDB的2dsphere索引要求使用GeoJSON格式
            # coordinates数组格式：[经度, 纬度]（注意：顺序是经度在前，纬度在后）
            'location': {
                'type': 'Point',  # GeoJSON类型：点
                'coordinates': [location['longitude'], location['latitude']]
            },
            'status': status,  # 设备状态
            # 设备配置信息（内嵌文档）
            # 使用内嵌文档可以灵活存储不同设备类型的差异化配置
            # 无需为每种设备类型创建单独的表结构
            'config': config or {},  # 如果未提供配置，使用空字典
            'created_at': datetime.utcnow(),  # 创建时间（UTC时间）
            'updated_at': datetime.utcnow()  # 更新时间（UTC时间）
        }
        return device

class DeviceLog:
    """
    设备日志数据模型类
    
    用于创建和表示设备日志的数据结构。
    日志文档包含以下字段：
    - device_id: 关联的设备ID
    - log_type: 日志类型（info/warning/error/status_change）
    - timestamp: 日志时间戳（用于TTL索引自动清理过期日志）
    - content: 日志内容（内嵌文档，包含消息和详细信息）
    
    注意：timestamp字段上创建了TTL索引，90天前的日志会自动删除。
    """
    
    @staticmethod
    def create(device_id: str, log_type: str, 
               message: str, details: Optional[Dict[str, Any]] = None,
               timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        """
        创建日志文档
        
        该方法创建一个符合MongoDB文档格式的日志对象。
        使用内嵌文档存储日志内容，便于全文搜索和灵活的数据结构。
        
        Args:
            device_id: 设备ID（字符串，关联到devices集合中的设备）
            log_type: 日志类型（字符串，可选值：
                - info: 信息日志（正常操作记录）
                - warning: 警告日志（需要注意但不影响运行）
                - error: 错误日志（需要处理的错误）
                - status_change: 状态变更日志（设备状态变化记录）
            message: 日志消息（字符串，日志的主要内容描述）
            details: 日志详细信息字典（可选，内嵌文档）
                可以包含任意键值对，例如：
                - error_code: 错误代码
                - temperature: 温度值
                - old_status/new_status: 状态变更前后的状态
            timestamp: 时间戳（datetime对象，可选，默认使用当前UTC时间）
                如果未提供，则使用当前时间
        
        Returns:
            Dict[str, Any]: 日志文档字典，可直接插入MongoDB
        
        示例:
            >>> log = DeviceLog.create(
            ...     device_id='DEV0001',
            ...     log_type='info',
            ...     message='设备正常运行',
            ...     details={'cpu_usage': 45.2, 'memory_usage': 60.5}
            ... )
        """
        log = {
            'device_id': device_id,  # 关联的设备ID
            'log_type': log_type,  # 日志类型
            # 时间戳：用于TTL索引自动清理过期日志
            # 如果未提供时间戳，使用当前UTC时间
            'timestamp': timestamp or datetime.utcnow(),
            # 日志内容（内嵌文档）
            # 使用内嵌文档可以：
            # 1. 将相关数据组织在一起，提高查询效率
            # 2. 支持全文搜索（在content.message和content.details上创建文本索引）
            'content': {
                'message': message,  # 日志消息
                'details': details or {}  # 详细信息（如果未提供，使用空字典）
            }
        }
        return log


