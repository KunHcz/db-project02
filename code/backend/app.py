"""
智能家居设备日志管理系统 - Flask主应用

本模块是系统的核心入口，负责：
1. 初始化Flask应用和MongoDB连接
2. 配置静态文件服务和CORS
3. 注册API路由蓝图
4. 提供健康检查接口
5. 处理全局异常和错误响应

作者: 数据库系统课程项目小组
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, OperationFailure
from datetime import datetime, timedelta
import os
from bson import ObjectId
import json

from routes import device_routes, log_routes

# ==================== 静态文件路径配置 ====================
# 优先使用相对路径（开发环境）
# 在开发环境中，前端文件位于 code/frontend 目录
FRONTEND_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
# Docker容器中的路径
# 在Docker容器中，前端文件可能位于 backend/frontend 目录
if not os.path.exists(FRONTEND_PATH):
    FRONTEND_PATH = os.path.join(os.path.dirname(__file__), 'frontend')

# ==================== Flask应用初始化 ====================
# 创建Flask应用实例，配置静态文件目录
# static_folder: 静态文件所在目录
# static_url_path: 静态文件的URL路径前缀（空字符串表示根路径）
app = Flask(__name__, static_folder=FRONTEND_PATH, static_url_path='')
# 启用CORS（跨域资源共享），允许前端从不同端口访问API
CORS(app)

# ==================== MongoDB连接配置 ====================
# 从环境变量读取MongoDB连接配置，如果没有设置则使用默认值
# 这样可以在不同环境（开发/生产/Docker）中灵活配置
MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')  # MongoDB主机地址
MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))  # MongoDB端口号
MONGO_USERNAME = os.getenv('MONGO_USERNAME', 'admin')  # 数据库用户名
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', 'admin123')  # 数据库密码
MONGO_DATABASE = os.getenv('MONGO_DATABASE', 'smart_home')  # 数据库名称

# 构建MongoDB连接字符串
# 如果配置了用户名和密码，使用认证连接
# authSource=admin 表示使用admin数据库进行身份验证
if MONGO_USERNAME and MONGO_PASSWORD:
    MONGO_URI = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DATABASE}?authSource=admin"
else:
    # 无认证连接（仅用于开发环境）
    MONGO_URI = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/{MONGO_DATABASE}"

# ==================== 连接MongoDB ====================
# 创建MongoDB客户端连接
# serverSelectionTimeoutMS: 服务器选择超时时间（5秒）
# 如果5秒内无法连接到MongoDB，将抛出异常
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client[MONGO_DATABASE]  # 获取数据库对象
    # 测试连接：执行ping命令验证连接是否正常
    client.admin.command('ping')
    print(f"成功连接到MongoDB: {MONGO_HOST}:{MONGO_PORT}")
except Exception as e:
    # 连接失败时记录错误，但不中断应用启动
    # 应用仍可启动，但API调用会返回错误
    print(f"MongoDB连接失败: {e}")
    db = None

# ==================== 注册路由蓝图 ====================
# 将设备管理和日志管理的路由蓝图注册到Flask应用
# url_prefix: URL前缀，所有该蓝图下的路由都会添加此前缀
app.register_blueprint(device_routes.bp, url_prefix='/api/devices')
app.register_blueprint(log_routes.bp, url_prefix='/api/logs')

# ==================== 自定义JSON编码器 ====================
# MongoDB的ObjectId和Python的datetime对象无法直接序列化为JSON
# 需要自定义编码器进行转换
class JSONEncoder(json.JSONEncoder):
    """
    自定义JSON编码器，用于处理MongoDB特殊数据类型
    
    功能：
    1. 将ObjectId转换为字符串
    2. 将datetime对象转换为ISO格式字符串
    """
    def default(self, obj):
        # ObjectId是MongoDB文档的唯一标识符，需要转换为字符串
        if isinstance(obj, ObjectId):
            return str(obj)
        # datetime对象转换为ISO 8601格式字符串（如：2024-01-01T12:00:00）
        if isinstance(obj, datetime):
            return obj.isoformat()
        # 其他类型使用默认编码器处理
        return super().default(obj)

# 将自定义编码器设置为Flask应用的JSON编码器
app.json_encoder = JSONEncoder

# ==================== 前端页面路由 ====================
@app.route('/')
def index():
    """
    首页路由 - 返回设备管理页面
    
    Returns:
        HTML文件: 设备管理页面的静态HTML文件
    """
    return app.send_static_file('index.html')

@app.route('/logs')
def logs_page():
    """
    日志查询页面路由
    
    Returns:
        HTML文件: 日志查询页面的静态HTML文件
    """
    return app.send_static_file('logs.html')

# ==================== API健康检查接口 ====================
@app.route('/api/health')
def health_check():
    """
    健康检查接口
    
    用于检查应用和数据库的连接状态，常用于：
    1. 容器健康检查（Docker healthcheck）
    2. 负载均衡器健康检查
    3. 监控系统状态检查
    
    Returns:
        JSON响应:
            - status: 'ok' 或 'error'
            - database: 数据库名称
            - mongodb_host: MongoDB主机地址
            - mongodb_port: MongoDB端口号
            - message: 错误信息（如果status为error）
    """
    # 检查数据库连接对象是否存在
    if db is None:
        return jsonify({'status': 'error', 'message': 'MongoDB未连接'}), 500
    
    try:
        # 执行ping命令测试数据库连接是否正常
        # ping命令是最轻量的数据库操作，适合用于健康检查
        db.command('ping')
        return jsonify({
            'status': 'ok',
            'database': MONGO_DATABASE,
            'mongodb_host': MONGO_HOST,
            'mongodb_port': MONGO_PORT
        })
    except Exception as e:
        # 连接失败时返回错误信息
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ==================== 全局错误处理 ====================
@app.errorhandler(404)
def not_found(error):
    """
    404错误处理器 - 处理未找到的路由
    
    Args:
        error: Flask错误对象
    
    Returns:
        JSON响应: 错误信息
    """
    return jsonify({'error': '接口不存在'}), 404

@app.errorhandler(500)
def internal_error(error):
    """
    500错误处理器 - 处理服务器内部错误
    
    Args:
        error: Flask错误对象
    
    Returns:
        JSON响应: 错误信息
    """
    return jsonify({'error': '服务器内部错误'}), 500

# ==================== 应用启动 ====================
if __name__ == '__main__':
    # 开发环境启动配置
    # host='0.0.0.0': 监听所有网络接口，允许外部访问
    # port=5000: 监听5000端口
    # debug=True: 启用调试模式，代码修改后自动重载，显示详细错误信息
    app.run(host='0.0.0.0', port=5000, debug=True)

