import os
import sys
import sqlite3

# 获取项目根目录路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from database.db_manager import DatabaseManager

def init_database():
    # 获取应用程序根目录
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 创建数据目录
    data_dir = os.path.join(application_path, 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    # 设置数据库文件路径
    db_path = os.path.join(data_dir, 'hotel.db')
    
    # 如果数据库不存在，创建并初始化
    if not os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 创建表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            room_number TEXT PRIMARY KEY,
            room_type TEXT NOT NULL,
            price REAL NOT NULL,
            status TEXT DEFAULT 'available'
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS check_ins (
            check_in_id INTEGER PRIMARY KEY,
            guest_name TEXT,
            phone TEXT,
            id_card TEXT,
            room_number TEXT,
            room_type TEXT,
            price_per_unit REAL,
            duration INTEGER,
            total_price REAL,
            check_in_time TIMESTAMP,
            check_out_time TIMESTAMP,
            actual_check_out_time TIMESTAMP,
            deposit_returned BOOLEAN DEFAULT 0,
            FOREIGN KEY (room_number) REFERENCES rooms (room_number)
        )
        ''')
        
        conn.commit()
        conn.close()

def init_test_data():
    db = DatabaseManager()
    try:
        # 添加测试房间
        rooms = [
            ('101', 'daily', 199),
            ('102', 'daily', 199),
            ('201', 'hourly', 35),
            ('202', 'hourly', 35),
        ]
        
        for room in rooms:
            db.cursor.execute('''
            INSERT INTO rooms (room_number, room_type, price)
            VALUES (?, ?, ?)
            ''', room)
        
        db.conn.commit()
        print("测试数据初始化成功！")
    finally:
        db.close()

if __name__ == "__main__":
    init_database()
    init_test_data() 