"""
数据导入脚本
用于将示例数据导入MongoDB数据库
"""
import json
import random
from datetime import datetime, timedelta
from pymongo import MongoClient
import os
import sys

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# MongoDB连接配置
MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))
MONGO_USERNAME = os.getenv('MONGO_USERNAME', 'admin')
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', 'admin123')
MONGO_DATABASE = os.getenv('MONGO_DATABASE', 'smart_home')

if MONGO_USERNAME and MONGO_PASSWORD:
    MONGO_URI = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DATABASE}?authSource=admin"
else:
    MONGO_URI = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/{MONGO_DATABASE}"

# 设备类型列表
DEVICE_TYPES = [
    '智能灯',
    '温湿度传感器',
    '摄像头',
    '智能门锁',
    '烟雾报警器',
    '智能插座',
    '运动传感器'
]

# 设备状态列表
DEVICE_STATUSES = ['online', 'offline', 'maintenance']

# 日志类型列表
LOG_TYPES = ['info', 'warning', 'error', 'status_change']

# 广州市大致经纬度范围（用于生成地理位置数据）
GUANGZHOU_LAT_RANGE = (23.0, 23.3)
GUANGZHOU_LON_RANGE = (113.2, 113.5)


def generate_device(device_id, device_type):
    """生成单个设备数据"""
    # 生成随机位置（广州市范围内）
    latitude = random.uniform(*GUANGZHOU_LAT_RANGE)
    longitude = random.uniform(*GUANGZHOU_LON_RANGE)
    
    # 根据设备类型生成配置
    config = {}
    if device_type == '智能灯':
        config = {
            'brightness': random.randint(10, 100),
            'color': random.choice(['white', 'warm', 'cool', 'rgb']),
            'power_consumption': round(random.uniform(5.0, 15.0), 2)
        }
    elif device_type == '温湿度传感器':
        config = {
            'temperature_range': {'min': -10, 'max': 50},
            'humidity_range': {'min': 0, 'max': 100},
            'update_interval': random.choice([30, 60, 120])  # 秒
        }
    elif device_type == '摄像头':
        config = {
            'resolution': random.choice(['720p', '1080p', '4K']),
            'night_vision': random.choice([True, False]),
            'motion_detection': True
        }
    elif device_type == '智能门锁':
        config = {
            'lock_type': random.choice(['fingerprint', 'password', 'card', 'bluetooth']),
            'battery_level': random.randint(20, 100),
            'auto_lock': True
        }
    elif device_type == '烟雾报警器':
        config = {
            'sensitivity': random.choice(['low', 'medium', 'high']),
            'battery_level': random.randint(50, 100),
            'test_date': (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat()
        }
    elif device_type == '智能插座':
        config = {
            'max_power': random.choice([2000, 3000, 4000]),  # 瓦
            'energy_monitoring': True,
            'scheduling': False
        }
    elif device_type == '运动传感器':
        config = {
            'detection_range': random.choice([5, 10, 15]),  # 米
            'sensitivity': random.choice(['low', 'medium', 'high']),
            'battery_level': random.randint(30, 100)
        }
    
    # 生成创建时间（最近30天内）
    created_at = datetime.now() - timedelta(days=random.randint(0, 30))
    
    return {
        'device_id': device_id,
        'name': f'{device_type}_{device_id[-4:]}',
        'type': device_type,
        'location': {
            'type': 'Point',
            'coordinates': [longitude, latitude]
        },
        'status': random.choice(DEVICE_STATUSES),
        'config': config,
        'created_at': created_at,
        'updated_at': created_at
    }


def generate_log(device_id, log_type=None):
    """生成单个日志数据"""
    if log_type is None:
        log_type = random.choice(LOG_TYPES)
    
    # 生成时间戳（最近30天内）
    timestamp = datetime.now() - timedelta(
        days=random.randint(0, 30),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59)
    )
    
    # 根据日志类型生成消息和详情
    if log_type == 'info':
        messages = [
            '设备正常运行',
            '数据采集完成',
            '定时任务执行成功',
            '配置更新完成',
            '设备自检通过'
        ]
        details = {
            'cpu_usage': round(random.uniform(10, 50), 2),
            'memory_usage': round(random.uniform(20, 60), 2)
        }
    elif log_type == 'warning':
        messages = [
            '电池电量低于30%',
            '网络连接不稳定',
            '传感器数据异常',
            '存储空间不足',
            '温度超出正常范围'
        ]
        details = {
            'warning_level': random.choice(['low', 'medium']),
            'value': round(random.uniform(0, 100), 2)
        }
    elif log_type == 'error':
        messages = [
            '设备连接失败',
            '传感器读取错误',
            '网络超时',
            '配置加载失败',
            '系统错误'
        ]
        details = {
            'error_code': random.randint(1000, 9999),
            'error_message': '系统内部错误'
        }
    else:  # status_change
        messages = [
            '设备状态变更',
            '设备上线',
            '设备离线',
            '进入维护模式',
            '恢复正常运行'
        ]
        details = {
            'old_status': random.choice(DEVICE_STATUSES),
            'new_status': random.choice(DEVICE_STATUSES),
            'reason': random.choice(['manual', 'automatic', 'scheduled'])
        }
    
    return {
        'device_id': device_id,
        'log_type': log_type,
        'timestamp': timestamp,
        'content': {
            'message': random.choice(messages),
            'details': details
        }
    }


def import_devices(client, num_devices=80):
    """导入设备数据"""
    db = client[MONGO_DATABASE]
    devices_collection = db.devices
    
    print(f'开始生成 {num_devices} 个设备...')
    
    devices = []
    for i in range(1, num_devices + 1):
        device_id = f'DEV{str(i).zfill(4)}'
        device_type = random.choice(DEVICE_TYPES)
        device = generate_device(device_id, device_type)
        devices.append(device)
    
    # 批量插入
    result = devices_collection.insert_many(devices)
    print(f'成功导入 {len(result.inserted_ids)} 个设备')
    
    return [d['device_id'] for d in devices]


def import_logs(client, device_ids, num_logs_per_device=150):
    """导入日志数据"""
    db = client[MONGO_DATABASE]
    logs_collection = db.device_logs
    
    total_logs = len(device_ids) * num_logs_per_device
    print(f'开始生成约 {total_logs} 条日志...')
    
    logs = []
    batch_size = 1000
    
    for device_id in device_ids:
        # 为每个设备生成日志
        for _ in range(num_logs_per_device):
            log = generate_log(device_id)
            logs.append(log)
            
            # 批量插入
            if len(logs) >= batch_size:
                logs_collection.insert_many(logs)
                print(f'已导入 {len(logs)} 条日志...')
                logs = []
    
    # 插入剩余日志
    if logs:
        logs_collection.insert_many(logs)
        print(f'已导入剩余 {len(logs)} 条日志')
    
    total_count = logs_collection.count_documents({})
    print(f'日志导入完成，共 {total_count} 条日志')


def main():
    """主函数"""
    print('=' * 50)
    print('MongoDB 数据导入脚本')
    print('=' * 50)
    
    try:
        # 连接MongoDB
        print(f'正在连接MongoDB: {MONGO_HOST}:{MONGO_PORT}')
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print('MongoDB连接成功！')
        
        # 清空现有数据（可选）
        db = client[MONGO_DATABASE]
        # 支持命令行参数跳过交互
        import sys
        if len(sys.argv) > 1 and sys.argv[1] == '--clear':
            db.devices.delete_many({})
            db.device_logs.delete_many({})
            print('已清空现有数据')
        else:
            print('\n是否清空现有数据？(y/n): ', end='')
            try:
                choice = input().strip().lower()
                if choice == 'y':
                    db.devices.delete_many({})
                    db.device_logs.delete_many({})
                    print('已清空现有数据')
            except EOFError:
                # 非交互式环境，不清空数据
                print('非交互式环境，保留现有数据')
        
        # 导入设备
        print('\n开始导入设备数据...')
        device_ids = import_devices(client, num_devices=80)
        
        # 导入日志
        print('\n开始导入日志数据...')
        import_logs(client, device_ids, num_logs_per_device=150)
        
        # 显示统计信息
        print('\n' + '=' * 50)
        print('导入完成！统计信息：')
        print('=' * 50)
        print(f'设备总数: {db.devices.count_documents({})}')
        print(f'日志总数: {db.device_logs.count_documents({})}')
        
        # 按类型统计设备
        print('\n设备类型统计:')
        type_stats = db.devices.aggregate([
            {'$group': {'_id': '$type', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ])
        for stat in type_stats:
            print(f'  {stat["_id"]}: {stat["count"]} 个')
        
        # 按类型统计日志
        print('\n日志类型统计:')
        log_stats = db.device_logs.aggregate([
            {'$group': {'_id': '$log_type', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ])
        for stat in log_stats:
            print(f'  {stat["_id"]}: {stat["count"]} 条')
        
        print('\n数据导入完成！')
        
    except Exception as e:
        print(f'错误: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if 'client' in locals():
            client.close()


if __name__ == '__main__':
    main()

