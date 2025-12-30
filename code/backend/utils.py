"""
工具函数模块

本模块提供了一系列工具函数，用于处理MongoDB数据类型转换、
日期时间解析、数据验证等通用功能。

主要功能：
1. ObjectId转字符串：将MongoDB的ObjectId转换为JSON可序列化的字符串
2. 日期时间解析：解析多种格式的日期时间字符串
3. 地理位置验证：验证经纬度数据的有效性
4. 查询过滤器构建：根据请求参数构建MongoDB查询过滤器

作者: 数据库系统课程项目小组
"""

from bson import ObjectId
from datetime import datetime
from typing import Dict, Any, Optional

def objectid_to_str(obj: Any) -> Any:
    """
    将MongoDB的ObjectId对象递归转换为字符串
    
    MongoDB文档中的_id字段是ObjectId类型，无法直接序列化为JSON。
    此函数递归遍历数据结构，将所有ObjectId对象转换为字符串。
    
    支持的数据类型：
    - ObjectId: 直接转换为字符串
    - dict: 递归处理字典中的所有值
    - list: 递归处理列表中的所有元素
    - 其他类型: 原样返回
    
    Args:
        obj: 需要转换的对象，可以是ObjectId、dict、list或其他类型
    
    Returns:
        Any: 转换后的对象，ObjectId被转换为字符串
    
    示例:
        >>> from bson import ObjectId
        >>> doc = {'_id': ObjectId('507f1f77bcf86cd799439011'), 'name': 'test'}
        >>> result = objectid_to_str(doc)
        >>> result['_id']  # '507f1f77bcf86cd799439011'
        
        >>> nested = {'items': [{'_id': ObjectId('507f1f77bcf86cd799439011')}]}
        >>> result = objectid_to_str(nested)
        >>> result['items'][0]['_id']  # '507f1f77bcf86cd799439011'
    """
    # ObjectId类型：转换为字符串
    if isinstance(obj, ObjectId):
        return str(obj)
    # 字典类型：递归处理所有值
    elif isinstance(obj, dict):
        return {k: objectid_to_str(v) for k, v in obj.items()}
    # 列表类型：递归处理所有元素
    elif isinstance(obj, list):
        return [objectid_to_str(item) for item in obj]
    # 其他类型：原样返回
    return obj

def parse_datetime(date_str: Optional[str]) -> Optional[datetime]:
    """
    解析日期时间字符串为datetime对象
    
    支持多种日期时间格式，按顺序尝试解析，直到成功或所有格式都失败。
    主要用于解析前端传递的日期时间参数和API请求中的时间范围参数。
    
    支持的格式：
    1. ISO 8601格式（带秒）: '2024-01-01T12:00:00'
    2. ISO 8601格式（带微秒）: '2024-01-01T12:00:00.123456'
    3. 标准格式（带秒）: '2024-01-01 12:00:00'
    4. 标准格式（不带秒）: '2024-01-01 12:00'
    5. ISO格式（不带秒）: '2024-01-01T12:00'
    6. 仅日期: '2024-01-01'
    
    Args:
        date_str: 日期时间字符串，可以是None或空字符串
    
    Returns:
        Optional[datetime]: 解析成功返回datetime对象，失败返回None
    
    示例:
        >>> parse_datetime('2024-01-01T12:00:00')
        datetime.datetime(2024, 1, 1, 12, 0, 0)
        
        >>> parse_datetime('2024-01-01 12:00')
        datetime.datetime(2024, 1, 1, 12, 0)
        
        >>> parse_datetime('invalid')  # None
        >>> parse_datetime(None)  # None
    """
    # 空字符串或None直接返回None
    if not date_str:
        return None
    try:
        # 按顺序尝试多种日期时间格式
        # 从最完整到最简单的格式，提高解析成功率
        formats = [
            '%Y-%m-%dT%H:%M:%S',  # ISO格式（带秒）
            '%Y-%m-%dT%H:%M:%S.%f',  # ISO格式（带微秒）
            '%Y-%m-%d %H:%M:%S',  # 标准格式（带秒）
            '%Y-%m-%d %H:%M',  # 标准格式（不带秒，datetime-local转换后）
            '%Y-%m-%dT%H:%M',  # ISO格式（不带秒，datetime-local原始格式）
            '%Y-%m-%d'  # 仅日期
        ]
        # 遍历所有格式，尝试解析
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                # 当前格式不匹配，尝试下一个格式
                continue
        # 所有格式都失败，返回None
        return None
    except Exception:
        # 发生其他异常（如类型错误），返回None
        return None

def validate_location(location: Dict[str, float]) -> bool:
    """
    验证地理位置数据的有效性
    
    检查地理位置数据是否符合以下要求：
    1. 必须是字典类型
    2. 必须包含longitude（经度）和latitude（纬度）字段
    3. 经纬度必须是有效的浮点数
    4. 经度范围：-180到180
    5. 纬度范围：-90到90
    
    Args:
        location: 地理位置字典，应包含：
            - longitude: 经度（float）
            - latitude: 纬度（float）
    
    Returns:
        bool: 如果地理位置数据有效返回True，否则返回False
    
    示例:
        >>> validate_location({'longitude': 113.2644, 'latitude': 23.1291})
        True
        
        >>> validate_location({'longitude': 200, 'latitude': 23.1291})  # 经度超出范围
        False
        
        >>> validate_location({'longitude': 113.2644})  # 缺少纬度
        False
    """
    # 检查是否为字典类型
    if not isinstance(location, dict):
        return False
    # 检查是否包含必需的字段
    if 'longitude' not in location or 'latitude' not in location:
        return False
    try:
        # 尝试转换为浮点数
        lon = float(location['longitude'])
        lat = float(location['latitude'])
        # 验证经纬度范围
        # 经度范围：-180（西经180度）到180（东经180度）
        # 纬度范围：-90（南纬90度）到90（北纬90度）
        if not (-180 <= lon <= 180) or not (-90 <= lat <= 90):
            return False
        return True
    except (ValueError, TypeError):
        # 转换失败或类型错误，返回False
        return False

def build_query_filters(request_args: Dict[str, Any]) -> Dict[str, Any]:
    """
    根据请求参数构建MongoDB查询过滤器
    
    从请求参数中提取查询条件，构建MongoDB查询过滤器字典。
    支持的查询条件：
    1. device_id: 设备ID（精确匹配）
    2. type: 设备类型（精确匹配）
    3. status: 设备状态（精确匹配）
    4. log_type: 日志类型（精确匹配）
    5. start_time/end_time: 时间范围（使用$gte和$lte操作符）
    
    Args:
        request_args: 请求参数字典，通常来自Flask的request.args.to_dict()
            可能包含的键：
            - device_id: 设备ID字符串
            - type: 设备类型字符串
            - status: 设备状态字符串
            - log_type: 日志类型字符串
            - start_time: 开始时间字符串（会被parse_datetime解析）
            - end_time: 结束时间字符串（会被parse_datetime解析）
    
    Returns:
        Dict[str, Any]: MongoDB查询过滤器字典
            格式示例：
            {
                'device_id': 'DEV0001',
                'log_type': 'error',
                'timestamp': {
                    '$gte': datetime(2024, 1, 1),
                    '$lte': datetime(2024, 1, 31)
                }
            }
    
    示例:
        >>> args = {
        ...     'device_id': 'DEV0001',
        ...     'log_type': 'error',
        ...     'start_time': '2024-01-01T00:00:00',
        ...     'end_time': '2024-01-31T23:59:59'
        ... }
        >>> filters = build_query_filters(args)
        >>> # filters = {
        >>> #     'device_id': 'DEV0001',
        >>> #     'log_type': 'error',
        >>> #     'timestamp': {
        >>> #         '$gte': datetime(2024, 1, 1),
        >>> #         '$lte': datetime(2024, 1, 31, 23, 59, 59)
        >>> #     }
        >>> # }
    """
    filters = {}
    
    # 设备ID过滤（精确匹配）
    if 'device_id' in request_args:
        filters['device_id'] = request_args['device_id']
    
    # 设备类型过滤（精确匹配）
    if 'type' in request_args:
        filters['type'] = request_args['type']
    
    # 状态过滤（精确匹配）
    if 'status' in request_args:
        filters['status'] = request_args['status']
    
    # 日志类型过滤（精确匹配）
    if 'log_type' in request_args:
        filters['log_type'] = request_args['log_type']
    
    # 时间范围过滤（使用MongoDB范围查询操作符）
    # 解析开始时间和结束时间
    start_time = parse_datetime(request_args.get('start_time'))
    end_time = parse_datetime(request_args.get('end_time'))
    
    # 如果提供了开始时间或结束时间，构建时间范围过滤器
    if start_time or end_time:
        time_filter = {}
        # $gte: 大于等于（Greater Than or Equal）
        if start_time:
            time_filter['$gte'] = start_time
        # $lte: 小于等于（Less Than or Equal）
        if end_time:
            time_filter['$lte'] = end_time
        filters['timestamp'] = time_filter
    
    return filters

