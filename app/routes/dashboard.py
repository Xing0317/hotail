from flask import Blueprint, render_template
from database.db_manager import DatabaseManager
import math

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='')

@dashboard_bp.route('/', methods=['GET'])
@dashboard_bp.route('/dashboard', methods=['GET'])
def dashboard():
    """显示酒店房态总览页面"""
    try:
        db = DatabaseManager()
        all_rooms = db.get_all_rooms()
        
        # 计算统计数据
        total_rooms = len(all_rooms)
        available_rooms = sum(1 for room in all_rooms if room['status'] == 'available')
        occupied_rooms = sum(1 for room in all_rooms if room['status'] == 'occupied')
        occupancy_rate = math.floor((occupied_rooms / total_rooms) * 100) if total_rooms > 0 else 0
        
        room_stats = {
            'total': total_rooms,
            'available': available_rooms,
            'occupied': occupied_rooms,
            'rate': occupancy_rate
        }
        
        # 按楼层组织房间数据
        floors = {}
        for room in all_rooms:
            # 假设房号的第一位数字是楼层
            floor_number = room['room_number'][0] if len(room['room_number']) > 0 else '1'
            
            # 添加显示文本
            room['room_type_display'] = '按天' if room['room_type'] == 'daily' else '按小时'
            room['status_display'] = '可用' if room['status'] == 'available' else '已入住' if room['status'] == 'occupied' else '清洁中'
            
            if floor_number not in floors:
                floors[floor_number] = {
                    'floor_number': floor_number,
                    'rooms': []
                }
            floors[floor_number]['rooms'].append(room)
        
        # 转换为排序后的列表
        floors_list = [floors[floor] for floor in sorted(floors.keys())]
        
        db.close()
        return render_template('dashboard.html', floors=floors_list, room_stats=room_stats)
    except Exception as e:
        print(f"Error: {str(e)}")
        return str(e), 500 