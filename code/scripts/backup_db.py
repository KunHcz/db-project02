"""
MongoDB数据库备份脚本
使用mongodump进行数据库备份
"""
import os
import subprocess
import datetime
import sys
from pathlib import Path

# MongoDB连接配置
MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))
MONGO_USERNAME = os.getenv('MONGO_USERNAME', 'admin')
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', 'admin123')
MONGO_DATABASE = os.getenv('MONGO_DATABASE', 'smart_home')

# 备份目录
BACKUP_DIR = Path(__file__).parent.parent.parent / 'data' / 'backup'


def create_backup():
    """创建数据库备份"""
    # 创建备份目录
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    # 生成备份文件名（带时间戳）
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
    
    # 构建mongodump命令
    cmd = [
        'mongodump',
        '--host', f'{MONGO_HOST}:{MONGO_PORT}',
        '--db', MONGO_DATABASE,
        '--out', str(backup_path)
    ]
    
    # 如果使用认证，添加用户名和密码
    if MONGO_USERNAME and MONGO_PASSWORD:
        cmd.extend([
            '--username', MONGO_USERNAME,
            '--password', MONGO_PASSWORD,
            '--authenticationDatabase', 'admin'
        ])
    
    try:
        print('开始备份...')
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        print('备份成功！')
        print(f'备份文件保存在: {backup_path}')
        
        # 显示备份文件大小
        total_size = 0
        for file_path in backup_path.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        
        print(f'备份总大小: {total_size / 1024 / 1024:.2f} MB')
        
        return backup_path
        
    except subprocess.CalledProcessError as e:
        print(f'备份失败: {e}')
        print(f'错误输出: {e.stderr}')
        return None
    except FileNotFoundError:
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
    """恢复数据库备份"""
    backup_path = BACKUP_DIR / backup_name
    
    if not backup_path.exists():
        print(f'错误: 备份文件不存在: {backup_name}')
        return False
    
    print('=' * 50)
    print('恢复数据库备份')
    print('=' * 50)
    print(f'备份文件: {backup_path}')
    print(f'目标数据库: {MONGO_DATABASE}')
    print('=' * 50)
    
    # 确认操作
    print('警告: 此操作将覆盖现有数据库！')
    confirm = input('确认恢复？(yes/no): ').strip().lower()
    if confirm != 'yes':
        print('操作已取消')
        return False
    
    # 构建mongorestore命令
    cmd = [
        'mongorestore',
        '--host', f'{MONGO_HOST}:{MONGO_PORT}',
        '--db', MONGO_DATABASE,
        '--drop',  # 删除现有数据
        str(backup_path / MONGO_DATABASE)
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
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        print('恢复成功！')
        return True
        
    except subprocess.CalledProcessError as e:
        print(f'恢复失败: {e}')
        print(f'错误输出: {e.stderr}')
        return False
    except FileNotFoundError:
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


