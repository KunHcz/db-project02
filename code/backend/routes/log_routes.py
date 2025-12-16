"""
日志管理路由
"""
from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from datetime import datetime, timedelta
import os
from bson import ObjectId
from bson.errors import InvalidId

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import DeviceLog
from utils import objectid_to_str, build_query_filters, parse_datetime

bp = Blueprint('logs', __name__)

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
logs_collection = db.device_logs

@bp.route('', methods=['GET'])
def get_logs():
    """查询日志"""
    try:
        # 获取查询参数
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        skip = (page - 1) * per_page
        
        # 构建查询过滤器
        filters = build_query_filters(request.args.to_dict())
        
        # 查询日志
        logs = list(logs_collection.find(filters)
                   .sort('timestamp', -1)
                   .skip(skip)
                   .limit(per_page))
        
        # 获取总数
        total = logs_collection.count_documents(filters)
        
        # 转换ObjectId为字符串
        logs = objectid_to_str(logs)
        
        return jsonify({
            'success': True,
            'data': logs,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('', methods=['POST'])
def create_log():
    """创建日志"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        if 'device_id' not in data:
            return jsonify({'success': False, 'error': '缺少必填字段: device_id'}), 400
        if 'log_type' not in data:
            return jsonify({'success': False, 'error': '缺少必填字段: log_type'}), 400
        if 'message' not in data:
            return jsonify({'success': False, 'error': '缺少必填字段: message'}), 400
        
        # 解析时间戳
        timestamp = parse_datetime(data.get('timestamp'))
        
        # 创建日志文档
        log = DeviceLog.create(
            device_id=data['device_id'],
            log_type=data['log_type'],
            message=data['message'],
            details=data.get('details', {}),
            timestamp=timestamp
        )
        
        # 插入数据库
        result = logs_collection.insert_one(log)
        
        return jsonify({
            'success': True,
            'message': '日志创建成功',
            'id': str(result.inserted_id)
        }), 201
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/<log_id>', methods=['DELETE'])
def delete_log(log_id):
    """删除日志"""
    try:
        # 验证ObjectId格式
        try:
            object_id = ObjectId(log_id)
        except InvalidId:
            return jsonify({'success': False, 'error': '日志ID格式错误'}), 400
        
        result = logs_collection.delete_one({'_id': object_id})
        
        if result.deleted_count == 0:
            return jsonify({'success': False, 'error': '日志不存在'}), 404
        
        return jsonify({'success': True, 'message': '日志删除成功'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/stats', methods=['GET'])
def get_log_stats():
    """获取日志统计信息（聚合查询）"""
    try:
        # 获取时间范围
        start_time = parse_datetime(request.args.get('start_time'))
        end_time = parse_datetime(request.args.get('end_time'))
        
        # 构建匹配条件
        match_conditions = {}
        if start_time or end_time:
            time_filter = {}
            if start_time:
                time_filter['$gte'] = start_time
            if end_time:
                time_filter['$lte'] = end_time
            match_conditions['timestamp'] = time_filter
        
        device_id = request.args.get('device_id')
        if device_id:
            match_conditions['device_id'] = device_id
        
        # 1. 按日志类型统计
        type_stats = list(logs_collection.aggregate([
            {'$match': match_conditions},
            {'$group': {
                '_id': '$log_type',
                'count': {'$sum': 1}
            }},
            {'$sort': {'count': -1}}
        ]))
        
        # 2. 按设备统计日志数量
        device_stats = list(logs_collection.aggregate([
            {'$match': match_conditions},
            {'$group': {
                '_id': '$device_id',
                'count': {'$sum': 1}
            }},
            {'$sort': {'count': -1}},
            {'$limit': 10}
        ]))
        
        # 3. 按时间段聚合（按小时）
        hourly_stats = list(logs_collection.aggregate([
            {'$match': match_conditions},
            {'$group': {
                '_id': {
                    'year': {'$year': '$timestamp'},
                    'month': {'$month': '$timestamp'},
                    'day': {'$dayOfMonth': '$timestamp'},
                    'hour': {'$hour': '$timestamp'}
                },
                'count': {'$sum': 1}
            }},
            {'$sort': {'_id': 1}},
            {'$limit': 24}
        ]))
        
        # 4. 计算平均日志频率（按设备）
        device_frequency = list(logs_collection.aggregate([
            {'$match': match_conditions},
            {'$group': {
                '_id': '$device_id',
                'first_log': {'$min': '$timestamp'},
                'last_log': {'$max': '$timestamp'},
                'count': {'$sum': 1}
            }},
            {'$project': {
                'device_id': '$_id',
                'count': 1,
                'duration_hours': {
                    '$divide': [
                        {'$subtract': ['$last_log', '$first_log']},
                        3600000  # 毫秒转小时
                    ]
                },
                'frequency': {
                    '$cond': {
                        'if': {'$gt': [{'$subtract': ['$last_log', '$first_log']}, 0]},
                        'then': {
                            '$divide': [
                                '$count',
                                {'$divide': [
                                    {'$subtract': ['$last_log', '$first_log']},
                                    3600000
                                ]}
                            ]
                        },
                        'else': 0
                    }
                }
            }},
            {'$sort': {'frequency': -1}},
            {'$limit': 10}
        ]))
        
        return jsonify({
            'success': True,
            'data': {
                'by_type': objectid_to_str(type_stats),
                'by_device': objectid_to_str(device_stats),
                'hourly': objectid_to_str(hourly_stats),
                'device_frequency': objectid_to_str(device_frequency)
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/search', methods=['GET'])
def search_logs():
    """全文搜索日志"""
    try:
        keyword = request.args.get('keyword', '')
        if not keyword:
            return jsonify({'success': False, 'error': '缺少搜索关键词'}), 400
        
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        skip = (page - 1) * per_page
        
        # 全文搜索
        logs = list(logs_collection.find(
            {'$text': {'$search': keyword}},
            {'score': {'$meta': 'textScore'}}
        ).sort([('score', {'$meta': 'textScore'})])
         .skip(skip)
         .limit(per_page))
        
        total = len(logs)  # 简化处理
        
        logs = objectid_to_str(logs)
        
        return jsonify({
            'success': True,
            'data': logs,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

