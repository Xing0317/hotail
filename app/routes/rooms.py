from flask import Blueprint, render_template, request, jsonify
from database.db_manager import DatabaseManager

rooms_bp = Blueprint('rooms', __name__)

@rooms_bp.route('/rooms', methods=['GET'])
def rooms_page():
    """显示房间管理页面"""
    db = DatabaseManager()
    try:
        rooms = db.get_all_rooms()
        return render_template('room_manage.html', rooms=rooms)
    finally:
        db.close()

@rooms_bp.route('/api/rooms', methods=['POST'])
def create_room():
    """创建新房间"""
    data = request.json
    if not all(key in data for key in ['room_number', 'room_type', 'price']):
        return jsonify({"success": False, "error": "缺少必要字段"})
    
    db = DatabaseManager()
    try:
        db.create_room(
            room_number=data['room_number'],
            room_type=data['room_type'],
            price=data['price']
        )
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    finally:
        db.close()

@rooms_bp.route('/api/rooms/<room_number>', methods=['GET'])
def get_room(room_number):
    """获取房间信息"""
    db = DatabaseManager()
    try:
        room = db.get_room(room_number)
        if room:
            return jsonify({"success": True, "data": room})
        return jsonify({"success": False, "error": "房间不存在"})
    finally:
        db.close()

@rooms_bp.route('/api/rooms/<room_number>', methods=['PUT'])
def update_room(room_number):
    """更新房间信息"""
    data = request.json
    if not all(key in data for key in ['room_type', 'price']):
        return jsonify({"success": False, "error": "缺少必要字段"})
    
    db = DatabaseManager()
    try:
        db.update_room(
            room_number=room_number,
            room_type=data['room_type'],
            price=data['price']
        )
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    finally:
        db.close() 