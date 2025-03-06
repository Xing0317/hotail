import os
import sys

# 获取项目根目录路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from database.db_manager import DatabaseManager

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
    init_test_data() 