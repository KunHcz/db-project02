"""
设备管理路由
"""
from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from datetime import datetime
import os
from bson import ObjectId
from bson.errors import InvalidId

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Device
from utils import objectid_to_str, validate_location

bp = Blueprint('devices', __name__)

# 获取MongoDB连接
MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))
MONGO_USERNAME = os.getenv('MONGO_USERNAME', 'admin')
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', 'admin123')
MONGO_DATABASE = os.getenv('MONGO_DATABASE', 'smart_home')

if MONGO_USERNAME and MONGO_PASSWORD:
    MONGO_URI = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DATABASE}?authSource=admin"
else:
    MONGO_URI = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/{MONGO_DATABASE}"

client = MongoClient(MONGO_URI)
db = client[MONGO_DATABASE]
devices_collection = db.devices

@bp.route('', methods=['GET'])
def get_devices():
    """获取所有设备"""
    try:
        # 获取查询参数
        device_type = request.args.get('type')
        status = request.args.get('status')
        search = request.args.get('search', '').strip()
        
        # 构建查询条件
        query = {}
        if device_type:
            query['type'] = device_type
        if status:
            query['status'] = status
        
        # 搜索功能：按设备ID或名称搜索
        if search:
            query['$or'] = [
                {'device_id': {'$regex': search, '$options': 'i'}},
                {'name': {'$regex': search, '$options': 'i'}}
            ]
        
        # 查询设备
        devices = list(devices_collection.find(query))
        
        # 转换ObjectId为字符串
        devices = objectid_to_str(devices)
        
        return jsonify({
            'success': True,
            'count': len(devices),
            'data': devices
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/<device_id>', methods=['GET'])
def get_device(device_id):
    """获取单个设备信息"""
    try:
        device = devices_collection.find_one({'device_id': device_id})
        if not device:
            return jsonify({'success': False, 'error': '设备不存在'}), 404
        
        device = objectid_to_str(device)
        return jsonify({'success': True, 'data': device})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('', methods=['POST'])
def create_device():
    """创建设备"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['device_id', 'name', 'type', 'location']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'缺少必填字段: {field}'}), 400
        
        # 验证地理位置
        if not validate_location(data['location']):
            return jsonify({'success': False, 'error': '地理位置数据格式错误'}), 400
        
        # 创建设备文档
        device = Device.create(
            device_id=data['device_id'],
            name=data['name'],
            device_type=data['type'],
            location=data['location'],
            status=data.get('status', 'online'),
            config=data.get('config', {})
        )
        
        # 插入数据库
        result = devices_collection.insert_one(device)
        
        return jsonify({
            'success': True,
            'message': '设备创建成功',
            'id': str(result.inserted_id)
        }), 201
        
    except DuplicateKeyError:
        return jsonify({'success': False, 'error': '设备ID已存在'}), 400
    except Exception as e:
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
    """查询附近设备（地理位置查询）"""
    try:
        # 获取查询参数
        longitude = float(request.args.get('longitude', 0))
        latitude = float(request.args.get('latitude', 0))
        max_distance = float(request.args.get('max_distance', 1000))  # 默认1000米
        limit = int(request.args.get('limit', 10))
        
        # 验证经纬度
        if not (-180 <= longitude <= 180) or not (-90 <= latitude <= 90):
            return jsonify({'success': False, 'error': '经纬度范围错误'}), 400
        
        # 地理位置查询
        query = {
            'location': {
                '$near': {
                    '$geometry': {
                        'type': 'Point',
                        'coordinates': [longitude, latitude]
                    },
                    '$maxDistance': max_distance
                }
            }
        }
        
        # 可选的状态过滤
        status = request.args.get('status')
        if status:
            query['status'] = status
        
        # 执行查询
        devices = list(devices_collection.find(query).limit(limit))
        devices = objectid_to_str(devices)
        
        return jsonify({
            'success': True,
            'count': len(devices),
            'data': devices
        })
        
    except ValueError as e:
        return jsonify({'success': False, 'error': f'参数格式错误: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/stats', methods=['GET'])
def get_device_stats():
    """获取设备统计信息"""
    try:
        # 按类型统计
        type_stats = list(devices_collection.aggregate([
            {'$group': {
                '_id': '$type',
                'count': {'$sum': 1}
            }},
            {'$sort': {'count': -1}}
        ]))
        
        # 按状态统计
        status_stats = list(devices_collection.aggregate([
            {'$group': {
                '_id': '$status',
                'count': {'$sum': 1}
            }},
            {'$sort': {'count': -1}}
        ]))
        
        # 总设备数
        total_devices = devices_collection.count_documents({})
        
        return jsonify({
            'success': True,
            'data': {
                'total': total_devices,
                'by_type': objectid_to_str(type_stats),
                'by_status': objectid_to_str(status_stats)
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

