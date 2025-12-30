"""
设备管理路由模块

本模块实现了智能家居设备的CRUD操作和地理位置查询功能。
提供以下API接口：
1. GET /api/devices - 获取设备列表（支持类型、状态筛选和搜索）
2. GET /api/devices/<device_id> - 获取单个设备详情
3. POST /api/devices - 创建新设备
4. PUT /api/devices/<device_id> - 更新设备信息
5. DELETE /api/devices/<device_id> - 删除设备
6. GET /api/devices/nearby - 查询附近设备（地理位置查询）
7. GET /api/devices/stats - 获取设备统计信息（聚合查询）

MongoDB特色功能：
- 使用GeoJSON格式存储地理位置，支持2dsphere索引
- 使用$near操作符实现附近设备查询
- 使用聚合管道进行统计分析

作者: 数据库系统课程项目小组
"""

from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from datetime import datetime
import os
from bson import ObjectId
from bson.errors import InvalidId

# 添加父目录到Python路径，以便导入models和utils模块
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Device
from utils import objectid_to_str, validate_location

# ==================== Flask蓝图初始化 ====================
# 创建蓝图对象，用于组织路由
# 蓝图名称：devices，用于URL前缀和路由命名
bp = Blueprint('devices', __name__)

# ==================== MongoDB连接配置 ====================
# 从环境变量读取MongoDB连接配置
MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))
MONGO_USERNAME = os.getenv('MONGO_USERNAME', 'admin')
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', 'admin123')
MONGO_DATABASE = os.getenv('MONGO_DATABASE', 'smart_home')

# 构建MongoDB连接URI
if MONGO_USERNAME and MONGO_PASSWORD:
    MONGO_URI = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DATABASE}?authSource=admin"
else:
    MONGO_URI = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/{MONGO_DATABASE}"

# 创建MongoDB客户端和数据库连接
client = MongoClient(MONGO_URI)
db = client[MONGO_DATABASE]
# 获取devices集合对象，用于设备数据的增删改查
devices_collection = db.devices

@bp.route('', methods=['GET'])
def get_devices():
    """
    获取设备列表接口
    
    支持以下查询参数：
    - type: 设备类型筛选（精确匹配）
    - status: 设备状态筛选（精确匹配）
    - search: 搜索关键词（在设备ID和名称中模糊搜索，不区分大小写）
    
    URL示例：
    - GET /api/devices
    - GET /api/devices?type=智能灯&status=online
    - GET /api/devices?search=客厅
    
    Returns:
        JSON响应:
            {
                'success': True,
                'count': 设备数量,
                'data': [设备列表]
            }
            或错误响应:
            {
                'success': False,
                'error': '错误信息'
            }
    """
    try:
        # 从请求参数中获取筛选条件
        device_type = request.args.get('type')  # 设备类型筛选
        status = request.args.get('status')  # 设备状态筛选
        search = request.args.get('search', '').strip()  # 搜索关键词
        
        # 构建MongoDB查询条件
        query = {}
        # 设备类型筛选（精确匹配）
        if device_type:
            query['type'] = device_type
        # 设备状态筛选（精确匹配）
        if status:
            query['status'] = status
        
        # 搜索功能：按设备ID或名称模糊搜索
        # 使用$or操作符实现多字段搜索
        # $regex: 正则表达式匹配
        # $options: 'i' 表示不区分大小写
        if search:
            query['$or'] = [
                {'device_id': {'$regex': search, '$options': 'i'}},
                {'name': {'$regex': search, '$options': 'i'}}
            ]
        
        # 执行MongoDB查询
        # find()返回游标对象，使用list()转换为列表
        devices = list(devices_collection.find(query))
        
        # 转换ObjectId为字符串，以便JSON序列化
        devices = objectid_to_str(devices)
        
        # 返回成功响应
        return jsonify({
            'success': True,
            'count': len(devices),  # 设备数量
            'data': devices  # 设备列表
        })
    except Exception as e:
        # 捕获所有异常，返回错误响应
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/<device_id>', methods=['GET'])
def get_device(device_id):
    """
    获取单个设备详情接口
    
    URL示例：
    - GET /api/devices/DEV0001
    
    Args:
        device_id: 设备ID（URL路径参数）
    
    Returns:
        JSON响应:
            {
                'success': True,
                'data': 设备对象
            }
            或错误响应:
            {
                'success': False,
                'error': '错误信息'
            }
    """
    try:
        # 根据device_id查询设备（device_id字段上有唯一索引）
        device = devices_collection.find_one({'device_id': device_id})
        
        # 如果设备不存在，返回404错误
        if not device:
            return jsonify({'success': False, 'error': '设备不存在'}), 404
        
        # 转换ObjectId为字符串
        device = objectid_to_str(device)
        
        # 返回成功响应
        return jsonify({'success': True, 'data': device})
    except Exception as e:
        # 捕获所有异常，返回错误响应
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('', methods=['POST'])
def create_device():
    """
    创建设备接口
    
    请求体（JSON格式）：
    {
        "device_id": "DEV0001",  // 必填：设备ID（唯一）
        "name": "客厅智能灯",      // 必填：设备名称
        "type": "智能灯",          // 必填：设备类型
        "location": {             // 必填：地理位置
            "longitude": 113.2644,
            "latitude": 23.1291
        },
        "status": "online",       // 可选：设备状态（默认：online）
        "config": {}             // 可选：设备配置（内嵌文档）
    }
    
    Returns:
        JSON响应:
            {
                'success': True,
                'message': '设备创建成功',
                'id': MongoDB插入的_id
            }
            或错误响应:
            {
                'success': False,
                'error': '错误信息'
            }
    """
    try:
        # 获取请求体中的JSON数据
        data = request.get_json()
        
        # 验证必填字段
        # 检查所有必填字段是否都存在
        required_fields = ['device_id', 'name', 'type', 'location']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'缺少必填字段: {field}'}), 400
        
        # 验证地理位置数据格式和有效性
        # 检查经纬度范围是否正确
        if not validate_location(data['location']):
            return jsonify({'success': False, 'error': '地理位置数据格式错误'}), 400
        
        # 使用Device模型类创建设备文档
        # 这会自动设置created_at和updated_at时间戳
        # 并将location转换为GeoJSON格式
        device = Device.create(
            device_id=data['device_id'],
            name=data['name'],
            device_type=data['type'],
            location=data['location'],
            status=data.get('status', 'online'),  # 默认状态为online
            config=data.get('config', {})  # 默认配置为空字典
        )
        
        # 插入数据库
        # insert_one()返回InsertOneResult对象，包含inserted_id
        result = devices_collection.insert_one(device)
        
        # 返回成功响应，状态码201（Created）
        return jsonify({
            'success': True,
            'message': '设备创建成功',
            'id': str(result.inserted_id)  # MongoDB自动生成的_id
        }), 201
        
    except DuplicateKeyError:
        # 捕获重复键错误（device_id已存在）
        # device_id字段上有唯一索引，插入重复值会抛出此异常
        return jsonify({'success': False, 'error': '设备ID已存在'}), 400
    except Exception as e:
        # 捕获其他所有异常
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/<device_id>', methods=['PUT'])
def update_device(device_id):
    """更新设备信息"""
    try:
        data = request.get_json()
        
        # 构建更新文档
        update_doc = {'updated_at': datetime.utcnow()}
        
        if 'name' in data:
            update_doc['name'] = data['name']
        if 'type' in data:
            update_doc['type'] = data['type']
        if 'status' in data:
            update_doc['status'] = data['status']
        if 'location' in data:
            if not validate_location(data['location']):
                return jsonify({'success': False, 'error': '地理位置数据格式错误'}), 400
            update_doc['location'] = {
                'type': 'Point',
                'coordinates': [data['location']['longitude'], data['location']['latitude']]
            }
        if 'config' in data:
            update_doc['config'] = data['config']
        
        # 更新设备
        result = devices_collection.update_one(
            {'device_id': device_id},
            {'$set': update_doc}
        )
        
        if result.matched_count == 0:
            return jsonify({'success': False, 'error': '设备不存在'}), 404
        
        return jsonify({'success': True, 'message': '设备更新成功'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/<device_id>', methods=['DELETE'])
def delete_device(device_id):
    """删除设备"""
    try:
        result = devices_collection.delete_one({'device_id': device_id})
        
        if result.deleted_count == 0:
            return jsonify({'success': False, 'error': '设备不存在'}), 404
        
        return jsonify({'success': True, 'message': '设备删除成功'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/nearby', methods=['GET'])
def get_nearby_devices():
    """
    查询附近设备接口（MongoDB地理位置查询）
    
    这是MongoDB文档数据库的特色功能，使用2dsphere索引和$near操作符实现。
    需要确保devices集合的location字段上已创建2dsphere索引。
    
    查询参数：
    - longitude: 经度（必填，范围：-180到180）
    - latitude: 纬度（必填，范围：-90到90）
    - max_distance: 最大距离（可选，单位：米，默认：1000）
    - limit: 返回结果数量限制（可选，默认：10）
    - status: 设备状态筛选（可选）
    
    URL示例：
    - GET /api/devices/nearby?longitude=113.2644&latitude=23.1291&max_distance=500
    
    MongoDB查询原理：
    - 使用$near操作符进行地理位置查询
    - $geometry: 指定查询中心点（GeoJSON Point格式）
    - $maxDistance: 指定最大搜索距离（米）
    - 结果按距离从近到远排序
    
    Returns:
        JSON响应:
            {
                'success': True,
                'count': 设备数量,
                'data': [设备列表，按距离排序]
            }
    """
    try:
        # 获取查询参数并转换为数值类型
        longitude = float(request.args.get('longitude', 0))  # 经度
        latitude = float(request.args.get('latitude', 0))  # 纬度
        max_distance = float(request.args.get('max_distance', 1000))  # 最大距离（米），默认1000米
        limit = int(request.args.get('limit', 10))  # 结果数量限制，默认10个
        
        # 验证经纬度范围
        # 经度范围：-180（西经180度）到180（东经180度）
        # 纬度范围：-90（南纬90度）到90（北纬90度）
        if not (-180 <= longitude <= 180) or not (-90 <= latitude <= 90):
            return jsonify({'success': False, 'error': '经纬度范围错误'}), 400
        
        # 构建MongoDB地理位置查询
        # $near: MongoDB地理位置查询操作符
        # 需要location字段上有2dsphere索引才能使用
        query = {
            'location': {
                '$near': {
                    '$geometry': {
                        'type': 'Point',  # GeoJSON类型：点
                        'coordinates': [longitude, latitude]  # [经度, 纬度]
                    },
                    '$maxDistance': max_distance  # 最大距离（米）
                }
            }
        }
        
        # 可选的状态过滤
        # 可以同时使用地理位置查询和状态筛选
        status = request.args.get('status')
        if status:
            query['status'] = status
        
        # 执行查询
        # find()查询后使用limit()限制结果数量
        # $near查询的结果默认按距离从近到远排序
        devices = list(devices_collection.find(query).limit(limit))
        
        # 转换ObjectId为字符串
        devices = objectid_to_str(devices)
        
        # 返回成功响应
        return jsonify({
            'success': True,
            'count': len(devices),
            'data': devices
        })
        
    except ValueError as e:
        # 参数类型转换错误（如无法转换为float或int）
        return jsonify({'success': False, 'error': f'参数格式错误: {str(e)}'}), 400
    except Exception as e:
        # 捕获其他所有异常
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/stats', methods=['GET'])
def get_device_stats():
    """
    获取设备统计信息接口（MongoDB聚合查询）
    
    使用MongoDB聚合管道进行数据统计分析，展示MongoDB强大的聚合功能。
    
    Returns:
        JSON响应:
            {
                'success': True,
                'data': {
                    'total': 总设备数,
                    'by_type': [
                        {'_id': '设备类型', 'count': 数量},
                        ...
                    ],
                    'by_status': [
                        {'_id': '设备状态', 'count': 数量},
                        ...
                    ]
                }
            }
    
    MongoDB聚合管道说明：
    1. $group: 按指定字段分组，统计每组数量
    2. $sum: 求和操作，$sum: 1 表示计数
    3. $sort: 排序，-1表示降序
    """
    try:
        # ==================== 按设备类型统计 ====================
        # 使用聚合管道按type字段分组，统计每种类型的设备数量
        type_stats = list(devices_collection.aggregate([
            {
                '$group': {
                    '_id': '$type',  # 按type字段分组
                    'count': {'$sum': 1}  # 统计每组数量（$sum: 1表示计数）
                }
            },
            {
                '$sort': {'count': -1}  # 按数量降序排序
            }
        ]))
        
        # ==================== 按设备状态统计 ====================
        # 使用聚合管道按status字段分组，统计每种状态的设备数量
        status_stats = list(devices_collection.aggregate([
            {
                '$group': {
                    '_id': '$status',  # 按status字段分组
                    'count': {'$sum': 1}  # 统计每组数量
                }
            },
            {
                '$sort': {'count': -1}  # 按数量降序排序
            }
        ]))
        
        # ==================== 总设备数 ====================
        # 统计集合中的文档总数
        total_devices = devices_collection.count_documents({})
        
        # 返回成功响应
        return jsonify({
            'success': True,
            'data': {
                'total': total_devices,  # 总设备数
                'by_type': objectid_to_str(type_stats),  # 按类型统计结果
                'by_status': objectid_to_str(status_stats)  # 按状态统计结果
            }
        })
        
    except Exception as e:
        # 捕获所有异常，返回错误响应
        return jsonify({'success': False, 'error': str(e)}), 500

