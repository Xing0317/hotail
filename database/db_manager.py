import sqlite3
import os
import sys
from datetime import datetime

class DatabaseManager:
    def __init__(self):
        # 获取应用程序的根目录
        if getattr(sys, 'frozen', False):
            # 如果是打包后的应用
            application_path = os.path.dirname(sys.executable)
        else:
            # 如果是开发环境
            application_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
        # 确保数据目录存在
        data_dir = os.path.join(application_path, 'data')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            
        # 设置数据库文件路径
        self.db_path = os.path.join(data_dir, 'hotel.db')
        
        # 连接数据库
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        
        # 初始化数据库表
        self.init_db()

    def init_db(self):
        cursor = self.conn.cursor()
        
        # 创建房间表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            room_number TEXT PRIMARY KEY,
            room_type TEXT NOT NULL,
            price REAL NOT NULL,
            status TEXT DEFAULT 'available'
        )
        ''')
        
        # 创建入住记录表
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
        
        self.conn.commit()

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()

    def get_available_rooms(self):
        """获取所有可用房间"""
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT room_number, room_type, price 
        FROM rooms 
        WHERE status = 'available'
        ''')
        # 将结果转换为字典列表
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def create_check_in(self, **kwargs):
        """创建入住记录"""
        try:
            cursor = self.conn.cursor()
            # 创建入住记录
            sql = '''
            INSERT INTO check_ins (
                guest_name, phone, id_card, room_number, 
                room_type, price_per_unit, duration,
                total_price, check_in_time, check_out_time
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            
            # 确保所有必要字段都存在
            required_fields = [
                'guest_name', 'phone', 'id_card', 'room_number',
                'room_type', 'price_per_unit', 'duration', 'total_price',
                'check_out_time'
            ]
            
            for field in required_fields:
                if field not in kwargs:
                    raise ValueError(f"缺少必要字段: {field}")
            
            cursor.execute(sql, (
                kwargs['guest_name'],
                kwargs['phone'],
                kwargs['id_card'],
                kwargs['room_number'],
                kwargs['room_type'],
                float(kwargs['price_per_unit']),
                int(kwargs['duration']),
                float(kwargs['total_price']),
                datetime.now(),
                kwargs['check_out_time']
            ))
            
            check_in_id = cursor.lastrowid
            
            # 更新房间状态
            self.update_room_status(kwargs['room_number'], 'occupied')
            
            # 注意：这里不进行提交，由调用方负责提交或回滚
            return check_in_id
        except Exception as e:
            # 不在这里回滚，让调用方处理
            raise Exception(f"创建入住记录失败: {str(e)}")

    def update_room_status(self, room_number, status):
        """更新房间状态"""
        cursor = self.conn.cursor()
        cursor.execute('''
        UPDATE rooms 
        SET status = ? 
        WHERE room_number = ?
        ''', (status, room_number))

    def get_revenue_statistics(self, start_date, end_date):
        """获取收入统计"""
        cursor = self.conn.cursor()
        sql = '''
        WITH RECURSIVE dates(date) AS (
            SELECT date(?)
            UNION ALL
            SELECT date(date, '+1 day')
            FROM dates
            WHERE date < date(?)
        )
        SELECT 
            dates.date as check_in_date,
            SUM(c.total_price) as total_revenue,
            COUNT(c.check_in_id) as total_check_ins
        FROM dates
        LEFT JOIN check_ins c 
            ON date(c.check_in_time) = dates.date
        GROUP BY dates.date
        ORDER BY dates.date
        '''
        cursor.execute(sql, (start_date, end_date))
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_occupancy_rate(self, start_date, end_date):
        """计算入住率"""
        cursor = self.conn.cursor()
        sql = '''
        WITH RECURSIVE dates(date) AS (
            SELECT date(?)
            UNION ALL
            SELECT date(date, '+1 day')
            FROM dates
            WHERE date < date(?)
        )
        SELECT 
            d.date,
            COUNT(DISTINCT c.room_number) as occupied_rooms,
            (SELECT COUNT(*) FROM rooms) as total_rooms,
            ROUND(CAST(COUNT(DISTINCT c.room_number) * 100.0 / 
                (SELECT COUNT(*) FROM rooms) as DECIMAL(5,2)), 2) as occupancy_rate
        FROM dates d
        LEFT JOIN check_ins c ON date(c.check_in_time) = d.date
        GROUP BY d.date
        ORDER BY d.date
        '''
        cursor.execute(sql, (start_date, end_date))
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def search_check_ins(self, name='', phone='', room='', page=1, page_size=10):
        """搜索入住记录"""
        cursor = self.conn.cursor()
        conditions = []
        params = []
        
        if name:
            conditions.append("guest_name LIKE ?")
            params.append(f"%{name}%")
        if phone:
            conditions.append("phone LIKE ?")
            params.append(f"%{phone}%")
        if room:
            conditions.append("room_number LIKE ?")
            params.append(f"%{room}%")
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # 计算总记录数
        count_sql = f"SELECT COUNT(*) FROM check_ins WHERE {where_clause}"
        cursor.execute(count_sql, params)
        total = cursor.fetchone()[0]
        
        # 获取分页数据
        offset = (page - 1) * page_size
        sql = f"""
        SELECT 
            check_in_id,
            room_number,
            guest_name,
            phone,
            id_card,
            strftime('%Y-%m-%d %H:%M:%S', check_in_time) as check_in_time,
            strftime('%Y-%m-%d %H:%M:%S', check_out_time) as check_out_time,
            strftime('%Y-%m-%d %H:%M:%S', actual_check_out_time) as actual_check_out_time,
            total_price
        FROM check_ins
        WHERE {where_clause}
        ORDER BY check_in_time DESC
        LIMIT ? OFFSET ?
        """
        
        cursor.execute(sql, params + [page_size, offset])
        columns = [desc[0] for desc in cursor.description]
        records = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        return {
            'total': total,
            'records': records
        }

    def get_room_status(self, room_number):
        """获取房间状态"""
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT status 
        FROM rooms 
        WHERE room_number = ?
        ''', (room_number,))
        result = cursor.fetchone()
        return result[0] if result else None

    def get_all_rooms(self):
        """获取所有房间"""
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT room_number, room_type, price, status
        FROM rooms
        ORDER BY room_number
        ''')
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def process_check_out(self, check_in_id):
        """处理退房"""
        cursor = self.conn.cursor()
        # 获取入住记录
        cursor.execute('''
        SELECT room_number 
        FROM check_ins 
        WHERE check_in_id = ?
        ''', (check_in_id,))
        result = cursor.fetchone()
        if not result:
            raise ValueError("找不到入住记录")
        
        room_number = result[0]
        
        # 更新退房时间
        cursor.execute('''
        UPDATE check_ins 
        SET actual_check_out_time = ? 
        WHERE check_in_id = ?
        ''', (datetime.now(), check_in_id))
        
        # 更新房间状态为可用
        self.update_room_status(room_number, 'available')

    def create_room(self, room_number, room_type, price):
        """添加新房间"""
        try:
            cursor = self.conn.cursor()
            sql = '''
            INSERT INTO rooms (room_number, room_type, price)
            VALUES (?, ?, ?)
            '''
            cursor.execute(sql, (room_number, room_type, float(price)))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            raise ValueError("房间号已存在")
        except Exception as e:
            raise Exception(f"创建房间失败: {str(e)}")

    def update_room(self, room_number, room_type, price):
        """更新房间信息"""
        try:
            cursor = self.conn.cursor()
            sql = '''
            UPDATE rooms
            SET room_type = ?, price = ?
            WHERE room_number = ?
            '''
            cursor.execute(sql, (room_type, float(price), room_number))
            if cursor.rowcount == 0:
                raise ValueError("房间不存在")
            self.conn.commit()
            return True
        except Exception as e:
            raise Exception(f"更新房间失败: {str(e)}")

    def get_room(self, room_number):
        """获取单个房间信息"""
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT room_number, room_type, price, status
        FROM rooms
        WHERE room_number = ?
        ''', (room_number,))
        columns = [desc[0] for desc in cursor.description]
        result = cursor.fetchone()
        return dict(zip(columns, result)) if result else None 