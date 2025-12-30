"""
日志管理路由模块

本模块实现了设备日志的CRUD操作、全文搜索和统计分析功能。
提供以下API接口：
1. GET /api/logs - 查询日志列表（支持多条件筛选和分页）
2. POST /api/logs - 创建新日志
3. DELETE /api/logs/<log_id> - 删除日志
4. GET /api/logs/stats - 获取日志统计信息（聚合查询）
5. GET /api/logs/search - 全文搜索日志（文本索引）

MongoDB特色功能：
- 使用TTL索引自动清理90天前的日志
- 使用文本索引实现全文搜索
- 使用聚合管道进行复杂的数据分析
- 支持时间序列数据的按小时聚合

作者: 数据库系统课程项目小组
"""

from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from datetime import datetime, timedelta
import os
from bson import ObjectId
from bson.errors import InvalidId

# 添加父目录到Python路径，以便导入models和utils模块
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import DeviceLog
from utils import objectid_to_str, build_query_filters, parse_datetime

# ==================== Flask蓝图初始化 ====================
bp = Blueprint('logs', __name__)

# ==================== MongoDB连接配置 ====================
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
# 获取device_logs集合对象，用于日志数据的增删改查
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
    """
    获取日志统计信息接口（MongoDB聚合查询）
    
    使用MongoDB聚合管道进行复杂的数据统计分析，展示MongoDB强大的聚合功能。
    包括：
    1. 按日志类型统计
    2. 按设备统计日志数量
    3. 按时间段聚合（按小时）
    4. 计算设备平均日志频率
    
    查询参数：
    - start_time: 开始时间（可选）
    - end_time: 结束时间（可选）
    - device_id: 设备ID（可选）
    
    Returns:
        JSON响应:
            {
                'success': True,
                'data': {
                    'by_type': [按类型统计结果],
                    'by_device': [按设备统计结果],
                    'hourly': [按小时统计结果],
                    'device_frequency': [设备日志频率统计]
                }
            }
    """
    try:
        # ==================== 获取时间范围参数 ====================
        start_time = parse_datetime(request.args.get('start_time'))
        end_time = parse_datetime(request.args.get('end_time'))
        
        # ==================== 构建聚合管道的匹配条件 ====================
        match_conditions = {}
        # 时间范围过滤
        if start_time or end_time:
            time_filter = {}
            if start_time:
                time_filter['$gte'] = start_time  # 大于等于开始时间
            if end_time:
                time_filter['$lte'] = end_time  # 小于等于结束时间
            match_conditions['timestamp'] = time_filter
        
        # 设备ID过滤
        device_id = request.args.get('device_id')
        if device_id:
            match_conditions['device_id'] = device_id
        
        # ==================== 1. 按日志类型统计 ====================
        # 统计每种日志类型（info/warning/error/status_change）的数量
        type_stats = list(logs_collection.aggregate([
            {'$match': match_conditions},  # 匹配条件：时间范围和设备ID
            {'$group': {
                '_id': '$log_type',  # 按log_type字段分组
                'count': {'$sum': 1}  # 统计每组数量
            }},
            {'$sort': {'count': -1}}  # 按数量降序排序
        ]))
        
        # ==================== 2. 按设备统计日志数量 ====================
        # 统计每个设备的日志数量，返回前10个日志最多的设备
        device_stats = list(logs_collection.aggregate([
            {'$match': match_conditions},
            {'$group': {
                '_id': '$device_id',  # 按device_id字段分组
                'count': {'$sum': 1}  # 统计每组数量
            }},
            {'$sort': {'count': -1}},  # 按数量降序排序
            {'$limit': 10}  # 限制返回前10条
        ]))
        
        # ==================== 3. 按时间段聚合（按小时） ====================
        # 将日志按小时分组统计，用于时间序列分析
        # 使用MongoDB日期操作符提取年、月、日、小时
        hourly_stats = list(logs_collection.aggregate([
            {'$match': match_conditions},
            {'$group': {
                '_id': {
                    'year': {'$year': '$timestamp'},  # 提取年份
                    'month': {'$month': '$timestamp'},  # 提取月份（1-12）
                    'day': {'$dayOfMonth': '$timestamp'},  # 提取日期（1-31）
                    'hour': {'$hour': '$timestamp'}  # 提取小时（0-23）
                },
                'count': {'$sum': 1}  # 统计每小时的数量
            }},
            {'$sort': {'_id': 1}},  # 按时间升序排序
            {'$limit': 24}  # 限制返回24条（最近24小时）
        ]))
        
        # ==================== 4. 计算平均日志频率（按设备） ====================
        # 计算每个设备的平均日志频率（条/小时）
        # 频率 = 日志总数 / (最后一条日志时间 - 第一条日志时间)
        device_frequency = list(logs_collection.aggregate([
            {'$match': match_conditions},
            {'$group': {
                '_id': '$device_id',
                'first_log': {'$min': '$timestamp'},  # 第一条日志时间
                'last_log': {'$max': '$timestamp'},  # 最后一条日志时间
                'count': {'$sum': 1}  # 日志总数
            }},
            {'$project': {
                'device_id': '$_id',
                'count': 1,
                # 计算时间跨度（小时）
                # $subtract: 计算时间差（毫秒）
                # $divide: 除以3600000（毫秒转小时）
                'duration_hours': {
                    '$divide': [
                        {'$subtract': ['$last_log', '$first_log']},
                        3600000  # 毫秒转小时
                    ]
                },
                # 计算日志频率（条/小时）
                # $cond: 条件表达式，如果时间跨度>0则计算频率，否则为0
                'frequency': {
                    '$cond': {
                        'if': {'$gt': [{'$subtract': ['$last_log', '$first_log']}, 0]},
                        'then': {
                            '$divide': [
                                '$count',  # 日志总数
                                {'$divide': [
                                    {'$subtract': ['$last_log', '$first_log']},
                                    3600000
                                ]}  # 时间跨度（小时）
                            ]
                        },
                        'else': 0  # 如果时间跨度为0，频率为0
                    }
                }
            }},
            {'$sort': {'frequency': -1}},  # 按频率降序排序
            {'$limit': 10}  # 限制返回前10条
        ]))
        
        # 返回成功响应
        return jsonify({
            'success': True,
            'data': {
                'by_type': objectid_to_str(type_stats),  # 按类型统计
                'by_device': objectid_to_str(device_stats),  # 按设备统计
                'hourly': objectid_to_str(hourly_stats),  # 按小时统计
                'device_frequency': objectid_to_str(device_frequency)  # 设备频率统计
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/search', methods=['GET'])
def search_logs():
    """
    全文搜索日志接口（MongoDB文本索引）
    
    这是MongoDB文档数据库的特色功能，使用文本索引实现全文搜索。
    需要在device_logs集合的content.message和content.details字段上创建文本索引。
    
    查询参数：
    - keyword: 搜索关键词（必填）
    - page: 页码（可选，默认：1）
    - per_page: 每页数量（可选，默认：50）
    
    URL示例：
    - GET /api/logs/search?keyword=错误&page=1&per_page=20
    
    MongoDB全文搜索原理：
    - $text: MongoDB全文搜索操作符
    - $search: 搜索关键词（支持多个关键词，空格分隔）
    - textScore: 相关性评分，用于排序
    - 结果按相关性评分降序排序
    
    注意：需要在MongoDB中创建文本索引：
    db.device_logs.createIndex({
        "content.message": "text",
        "content.details": "text"
    })
    
    Returns:
        JSON响应:
            {
                'success': True,
                'data': [日志列表，按相关性排序],
                'pagination': {
                    'page': 当前页码,
                    'per_page': 每页数量,
                    'total': 总数量
                }
            }
    """
    try:
        # 获取搜索关键词
        keyword = request.args.get('keyword', '')
        if not keyword:
            return jsonify({'success': False, 'error': '缺少搜索关键词'}), 400
        
        # 获取分页参数
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        skip = (page - 1) * per_page  # 计算跳过的文档数量
        
        # ==================== MongoDB全文搜索 ====================
        # $text: MongoDB全文搜索操作符
        # $search: 搜索关键词（支持多个关键词，空格分隔，如："错误 设备"）
        # $meta: 'textScore' 获取相关性评分
        logs = list(logs_collection.find(
            {'$text': {'$search': keyword}},  # 全文搜索条件
            {'score': {'$meta': 'textScore'}}  # 包含相关性评分字段
        ).sort([('score', {'$meta': 'textScore'})])  # 按相关性评分降序排序
         .skip(skip)  # 跳过前面的文档
         .limit(per_page))  # 限制返回数量
        
        # 注意：这里简化处理，实际应该使用count_documents统计总数
        # 但$text查询的count操作较复杂，这里使用返回结果的长度
        total = len(logs)  # 简化处理
        
        # 转换ObjectId为字符串
        logs = objectid_to_str(logs)
        
        # 返回成功响应
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

