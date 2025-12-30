"""
MongoDB数据库备份脚本

本脚本使用MongoDB官方工具mongodump和mongorestore进行数据库备份和恢复。
支持以下功能：
1. 创建数据库备份（使用mongodump）
2. 列出所有备份
3. 恢复数据库备份（使用mongorestore）

备份文件存储位置：data/backup/
备份文件命名格式：smart_home_backup_YYYYMMDD_HHMMSS

使用方法：
    python backup_db.py backup                    # 创建备份
    python backup_db.py list                      # 列出所有备份
    python backup_db.py restore <备份名称>        # 恢复备份

前置要求：
    - 已安装MongoDB工具（mongodump和mongorestore）
    - 工具在系统PATH中可用

作者: 数据库系统课程项目小组
"""

import os
import subprocess
import datetime
import sys
from pathlib import Path

# ==================== MongoDB连接配置 ====================
MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))
MONGO_USERNAME = os.getenv('MONGO_USERNAME', 'admin')
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', 'admin123')
MONGO_DATABASE = os.getenv('MONGO_DATABASE', 'smart_home')

# ==================== 备份目录配置 ====================
# 备份文件存储目录：项目根目录/data/backup/
BACKUP_DIR = Path(__file__).parent.parent.parent / 'data' / 'backup'


def create_backup():
    """
    创建数据库备份
    
    使用mongodump工具导出MongoDB数据库到指定目录。
    备份文件包含数据库的所有集合和索引信息。
    
    @return: 备份路径（Path对象），如果失败返回None
    """
    # 创建备份目录（如果不存在）
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    # 生成备份文件名（带时间戳）
    # 格式：smart_home_backup_YYYYMMDD_HHMMSS
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f'smart_home_backup_{timestamp}'
    backup_path = BACKUP_DIR / backup_name
    
    print('=' * 50)
    print('MongoDB 数据库备份脚本')
    print('=' * 50)
    print(f'数据库: {MONGO_DATABASE}')
    print(f'主机: {MONGO_HOST}:{MONGO_PORT}')
    print(f'备份路径: {backup_path}')
    print('=' * 50)
    
    # ==================== 构建mongodump命令 ====================
    # mongodump是MongoDB官方提供的数据库导出工具
    cmd = [
        'mongodump',
        '--host', f'{MONGO_HOST}:{MONGO_PORT}',  # MongoDB主机和端口
        '--db', MONGO_DATABASE,  # 要备份的数据库名称
        '--out', str(backup_path)  # 备份输出目录
    ]
    
    # 如果使用认证，添加用户名和密码
    if MONGO_USERNAME and MONGO_PASSWORD:
        cmd.extend([
            '--username', MONGO_USERNAME,  # 用户名
            '--password', MONGO_PASSWORD,  # 密码
            '--authenticationDatabase', 'admin'  # 认证数据库
        ])
    
    try:
        print('开始备份...')
        # 执行mongodump命令
        # capture_output=True: 捕获标准输出和错误输出
        # text=True: 以文本模式返回输出
        # check=True: 如果命令返回非零退出码，抛出CalledProcessError异常
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        print('备份成功！')
        print(f'备份文件保存在: {backup_path}')
        
        # 计算并显示备份文件大小
        total_size = 0
        for file_path in backup_path.rglob('*'):  # 递归遍历所有文件
            if file_path.is_file():
                total_size += file_path.stat().st_size
        
        print(f'备份总大小: {total_size / 1024 / 1024:.2f} MB')
        
        return backup_path
        
    except subprocess.CalledProcessError as e:
        # mongodump命令执行失败
        print(f'备份失败: {e}')
        print(f'错误输出: {e.stderr}')
        return None
    except FileNotFoundError:
        # 未找到mongodump命令
        print('错误: 未找到mongodump命令')
        print('请确保MongoDB工具已安装并在PATH中')
        return None


def list_backups():
    """列出所有备份"""
    if not BACKUP_DIR.exists():
        print('备份目录不存在')
        return
    
    backups = [d for d in BACKUP_DIR.iterdir() if d.is_dir()]
    
    if not backups:
        print('没有找到备份文件')
        return
    
    print('=' * 50)
    print('现有备份列表:')
    print('=' * 50)
    
    backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    for backup in backups:
        size = sum(f.stat().st_size for f in backup.rglob('*') if f.is_file())
        mtime = datetime.datetime.fromtimestamp(backup.stat().st_mtime)
        print(f'{backup.name}')
        print(f'  大小: {size / 1024 / 1024:.2f} MB')
        print(f'  时间: {mtime.strftime("%Y-%m-%d %H:%M:%S")}')
        print()


def restore_backup(backup_name):
    """
    恢复数据库备份
    
    使用mongorestore工具从备份文件恢复MongoDB数据库。
    警告：此操作会删除现有数据库中的所有数据！
    
    @param backup_name: 备份目录名称（如：smart_home_backup_20240101_120000）
    @return: 恢复成功返回True，失败返回False
    """
    backup_path = BACKUP_DIR / backup_name
    
    # 检查备份文件是否存在
    if not backup_path.exists():
        print(f'错误: 备份文件不存在: {backup_name}')
        return False
    
    print('=' * 50)
    print('恢复数据库备份')
    print('=' * 50)
    print(f'备份文件: {backup_path}')
    print(f'目标数据库: {MONGO_DATABASE}')
    print('=' * 50)
    
    # ==================== 确认操作 ====================
    # 恢复操作会覆盖现有数据，需要用户确认
    print('警告: 此操作将覆盖现有数据库！')
    confirm = input('确认恢复？(yes/no): ').strip().lower()
    if confirm != 'yes':
        print('操作已取消')
        return False
    
    # ==================== 构建mongorestore命令 ====================
    # mongorestore是MongoDB官方提供的数据库恢复工具
    cmd = [
        'mongorestore',
        '--host', f'{MONGO_HOST}:{MONGO_PORT}',  # MongoDB主机和端口
        '--db', MONGO_DATABASE,  # 目标数据库名称
        '--drop',  # 删除现有数据（重要：会清空目标数据库）
        str(backup_path / MONGO_DATABASE)  # 备份文件路径
        # mongodump导出的目录结构：backup_path/database_name/
    ]
    
    # 如果使用认证，添加用户名和密码
    if MONGO_USERNAME and MONGO_PASSWORD:
        cmd.extend([
            '--username', MONGO_USERNAME,
            '--password', MONGO_PASSWORD,
            '--authenticationDatabase', 'admin'
        ])
    
    try:
        print('开始恢复...')
        # 执行mongorestore命令
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        print('恢复成功！')
        return True
        
    except subprocess.CalledProcessError as e:
        # mongorestore命令执行失败
        print(f'恢复失败: {e}')
        print(f'错误输出: {e.stderr}')
        return False
    except FileNotFoundError:
        # 未找到mongorestore命令
        print('错误: 未找到mongorestore命令')
        print('请确保MongoDB工具已安装并在PATH中')
        return False


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print('用法:')
        print('  python backup_db.py backup      - 创建备份')
        print('  python backup_db.py list        - 列出所有备份')
        print('  python backup_db.py restore <备份名称>  - 恢复备份')
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'backup':
        create_backup()
    elif command == 'list':
        list_backups()
    elif command == 'restore':
        if len(sys.argv) < 3:
            print('错误: 请指定备份名称')
            sys.exit(1)
        restore_backup(sys.argv[2])
    else:
        print(f'错误: 未知命令: {command}')
        sys.exit(1)


if __name__ == '__main__':
    main()


