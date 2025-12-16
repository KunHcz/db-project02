"""
智能家居设备日志管理系统 - Flask主应用
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

# 静态文件路径配置
import os
# 优先使用相对路径（开发环境）
FRONTEND_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
# Docker容器中的路径
if not os.path.exists(FRONTEND_PATH):
    FRONTEND_PATH = os.path.join(os.path.dirname(__file__), 'frontend')

app = Flask(__name__, static_folder=FRONTEND_PATH, static_url_path='')
CORS(app)

# MongoDB连接配置
MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))
MONGO_USERNAME = os.getenv('MONGO_USERNAME', 'admin')
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', 'admin123')
MONGO_DATABASE = os.getenv('MONGO_DATABASE', 'smart_home')

# 构建MongoDB连接字符串
if MONGO_USERNAME and MONGO_PASSWORD:
    MONGO_URI = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DATABASE}?authSource=admin"
else:
    MONGO_URI = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/{MONGO_DATABASE}"

# 连接MongoDB
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client[MONGO_DATABASE]
    # 测试连接
    client.admin.command('ping')
    print(f"成功连接到MongoDB: {MONGO_HOST}:{MONGO_PORT}")
except Exception as e:
    print(f"MongoDB连接失败: {e}")
    db = None

# 注册路由
app.register_blueprint(device_routes.bp, url_prefix='/api/devices')
app.register_blueprint(log_routes.bp, url_prefix='/api/logs')

# JSON编码器 - 处理ObjectId和datetime
class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

app.json_encoder = JSONEncoder

@app.route('/')
def index():
    """首页重定向到设备管理页面"""
    return app.send_static_file('index.html')

@app.route('/logs')
def logs_page():
    """日志查询页面"""
    return app.send_static_file('logs.html')

@app.route('/api/health')
def health_check():
    """健康检查接口"""
    if db is None:
        return jsonify({'status': 'error', 'message': 'MongoDB未连接'}), 500
    
    try:
        # 测试数据库连接
        db.command('ping')
        return jsonify({
            'status': 'ok',
            'database': MONGO_DATABASE,
            'mongodb_host': MONGO_HOST,
            'mongodb_port': MONGO_PORT
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': '接口不存在'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': '服务器内部错误'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

