"""
工具函数
"""
from bson import ObjectId
from datetime import datetime
from typing import Dict, Any, Optional

def objectid_to_str(obj: Any) -> Any:
    """将ObjectId转换为字符串"""
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: objectid_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [objectid_to_str(item) for item in obj]
    return obj

def parse_datetime(date_str: Optional[str]) -> Optional[datetime]:
    """解析日期时间字符串"""
    if not date_str:
        return None
    try:
        # 支持多种格式
        formats = [
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',  # 添加支持 HH:MM 格式（datetime-local格式转换后）
            '%Y-%m-%dT%H:%M',  # 支持datetime-local原始格式
            '%Y-%m-%d'
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None
    except Exception:
        return None

def validate_location(location: Dict[str, float]) -> bool:
    """验证地理位置数据"""
    if not isinstance(location, dict):
        return False
    if 'longitude' not in location or 'latitude' not in location:
        return False
    try:
        lon = float(location['longitude'])
        lat = float(location['latitude'])
        # 验证经纬度范围
        if not (-180 <= lon <= 180) or not (-90 <= lat <= 90):
            return False
        return True
    except (ValueError, TypeError):
        return False

def build_query_filters(request_args: Dict[str, Any]) -> Dict[str, Any]:
    """构建查询过滤器"""
    filters = {}
    
    # 设备ID过滤
    if 'device_id' in request_args:
        filters['device_id'] = request_args['device_id']
    
    # 设备类型过滤
    if 'type' in request_args:
        filters['type'] = request_args['type']
    
    # 状态过滤
    if 'status' in request_args:
        filters['status'] = request_args['status']
    
    # 日志类型过滤
    if 'log_type' in request_args:
        filters['log_type'] = request_args['log_type']
    
    # 时间范围过滤
    start_time = parse_datetime(request_args.get('start_time'))
    end_time = parse_datetime(request_args.get('end_time'))
    
    if start_time or end_time:
        time_filter = {}
        if start_time:
            time_filter['$gte'] = start_time
        if end_time:
            time_filter['$lte'] = end_time
        filters['timestamp'] = time_filter
    
    return filters

