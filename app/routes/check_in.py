from flask import Blueprint, render_template, request, jsonify, send_file
from database.db_manager import DatabaseManager
from datetime import datetime, timedelta
import os
from openpyxl import Workbook
from io import BytesIO

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
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "缺少请求数据"})
        
        # 检查必要字段
        required_fields = ['guest_name', 'phone', 'id_card', 'room_number', 
                         'room_type', 'price', 'duration', 'deposit']
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
            deposit=data['deposit'],
            total_price=total_price,
            check_out_time=check_out_time
        )
        
        db.conn.commit()
        return jsonify({"success": True, "check_in_id": check_in_id})
    except Exception as e:
        db.conn.rollback()
        return jsonify({"success": False, "error": str(e)})
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

@check_in_bp.route('/api/check-in/<int:check_in_id>/refund', methods=['POST'])
def refund_check_in(check_in_id):
    """处理押金退款"""
    db = DatabaseManager()
    try:
        cursor = db.conn.cursor()
        cursor.execute('''
        UPDATE check_ins 
        SET deposit_returned = 1 
        WHERE check_in_id = ?
        ''', (check_in_id,))
        db.conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.conn.rollback()
        return jsonify({"success": False, "error": str(e)})
    finally:
        db.close()

@check_in_bp.route('/api/check-in/export', methods=['GET'])
def export_check_ins():
    """导出入住记录"""
    name = request.args.get('name', '')
    phone = request.args.get('phone', '')
    room = request.args.get('room', '')
    
    db = DatabaseManager()
    try:
        # 获取所有符合条件的记录（不分页）
        result = db.search_check_ins(name, phone, room, page=1, page_size=10000)
        records = result['records']
        
        # 创建工作簿和工作表
        wb = Workbook()
        ws = wb.active
        ws.title = "入住记录"
        
        # 写入表头
        headers = [
            '房间号', '客人姓名', '手机号', '身份证号',
            '入住时间', '预计退房时间', '实际退房时间',
            '房费', '押金', '押金状态', '状态'
        ]
        ws.append(headers)
        
        # 写入数据
        for record in records:
            ws.append([
                record['room_number'],
                record['guest_name'],
                record['phone'],
                record['id_card'],
                record['check_in_time'],
                record['check_out_time'],
                record['actual_check_out_time'] or '',
                record['total_price'],
                record['deposit'],
                '已退还' if record['deposit_returned'] else '未退还',
                '已退房' if record['actual_check_out_time'] else '在住'
            ])
        
        # 调整列宽
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'酒店数据_{timestamp}.xlsx'
        
        # 保存到内存
        excel_file = BytesIO()
        wb.save(excel_file)
        excel_file.seek(0)
        
        return send_file(
            excel_file,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    finally:
        db.close() 