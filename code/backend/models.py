"""
数据模型定义
"""
from datetime import datetime
from typing import Optional, Dict, Any

class Device:
    """设备模型"""
    
    @staticmethod
    def create(device_id: str, name: str, device_type: str, 
               location: Dict[str, float], status: str = 'online',
               config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        创建设备文档
        
        Args:
            device_id: 设备唯一标识
            name: 设备名称
            device_type: 设备类型（如：智能灯、温湿度传感器等）
            location: 位置信息 {'longitude': float, 'latitude': float}
            status: 设备状态（online/offline/maintenance）
            config: 设备配置信息（内嵌文档）
        
        Returns:
            设备文档字典
        """
        device = {
            'device_id': device_id,
            'name': name,
            'type': device_type,
            'location': {
                'type': 'Point',
                'coordinates': [location['longitude'], location['latitude']]
            },
            'status': status,
            'config': config or {},
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        return device

class DeviceLog:
    """设备日志模型"""
    
    @staticmethod
    def create(device_id: str, log_type: str, 
               message: str, details: Optional[Dict[str, Any]] = None,
               timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        """
        创建日志文档
        
        Args:
            device_id: 设备ID
            log_type: 日志类型（info/warning/error/status_change）
            message: 日志消息
            details: 日志详细信息（内嵌文档）
            timestamp: 时间戳（默认为当前时间）
        
        Returns:
            日志文档字典
        """
        log = {
            'device_id': device_id,
            'log_type': log_type,
            'timestamp': timestamp or datetime.utcnow(),
            'content': {
                'message': message,
                'details': details or {}
            }
        }
        return log


