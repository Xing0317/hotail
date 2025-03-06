from flask import Blueprint, render_template, request, jsonify
from database.db_manager import DatabaseManager
from datetime import datetime, timedelta

check_in_bp = Blueprint('check_in', __name__, url_prefix='')

@check_in_bp.route('/check-in', methods=['GET'])
def check_in_page():
    """显示入住登记页面"""
    try:
        db = DatabaseManager()
        # 获取可用房间列表
        available_rooms = db.get_available_rooms()
        db.close()
        return render_template('check_in.html', rooms=available_rooms)
    except Exception as e:
        print(f"Error: {str(e)}")
        return str(e), 500

@check_in_bp.route('/api/check-in', methods=['POST'])
def create_check_in():
    """创建入住记录"""
    db = DatabaseManager()
    try:
        # 获取并验证请求数据
        try:
            data = request.get_json()
        except Exception:
            return jsonify({"success": False, "error": "无效的请求数据格式"})
        
        if not data:
            return jsonify({"success": False, "error": "缺少请求数据"})
        
        # 检查必要字段
        required_fields = ['guest_name', 'phone', 'id_card', 'room_number', 'room_type', 'price', 'duration']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"success": False, "error": f"缺少必要字段: {field}"})
        
        # 验证房间是否可用
        room_status = db.get_room_status(data['room_number'])
        if not room_status:
            return jsonify({"success": False, "error": "房间不存在"})
        if room_status != 'available':
            return jsonify({"success": False, "error": "该房间已被占用"})
        
        # 计算退房时间
        check_in_time = datetime.now()
        duration = int(data['duration'])
        check_out_time = check_in_time + timedelta(
            days=duration if data['room_type'] == 'daily' else 0,
            hours=duration if data['room_type'] == 'hourly' else 0
        )
        
        # 计算总价
        total_price = float(data['price']) * duration
        
        # 创建入住记录
        check_in_id = db.create_check_in(
            guest_name=data['guest_name'],
            phone=data['phone'],
            id_card=data['id_card'],
            room_number=data['room_number'],
            room_type=data['room_type'],
            price_per_unit=data['price'],
            duration=duration,
            total_price=total_price,
            check_out_time=check_out_time
        )
        
        # 提交事务
        db.conn.commit()
        return jsonify({"success": True, "check_in_id": check_in_id})
    except ValueError as e:
        db.conn.rollback()
        return jsonify({"success": False, "error": str(e)})
    except Exception as e:
        db.conn.rollback()
        import traceback
        print(f"入住登记错误: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"success": False, "error": "系统错误，请联系管理员"})
    finally:
        db.close()

@check_in_bp.route('/api/check-in/search', methods=['GET'])
def search_check_ins():
    """搜索入住记录"""
    name = request.args.get('name', '')
    phone = request.args.get('phone', '')
    room = request.args.get('room', '')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('size', 10))
    
    db = DatabaseManager()
    try:
        result = db.search_check_ins(name, phone, room, page, page_size)
        return jsonify({"success": True, "data": result})
    finally:
        db.close()

@check_in_bp.route('/api/check-in/<int:check_in_id>/check-out', methods=['POST'])
def check_out(check_in_id):
    """办理退房"""
    db = DatabaseManager()
    try:
        db.process_check_out(check_in_id)
        db.conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.conn.rollback()
        return jsonify({"success": False, "error": str(e)})
    finally:
        db.close() 