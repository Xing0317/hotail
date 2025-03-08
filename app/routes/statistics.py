from flask import Blueprint, render_template, request, jsonify
from database.db_manager import DatabaseManager
from datetime import datetime, timedelta

statistics_bp = Blueprint('statistics', __name__)

@statistics_bp.route('/statistics', methods=['GET'])
def statistics_page():
    """显示统计页面"""
    return render_template('statistics.html')

@statistics_bp.route('/api/statistics/revenue', methods=['GET'])
def get_revenue():
    """获取收入统计"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    db = DatabaseManager()
    try:
        revenue = db.get_revenue_statistics(start_date, end_date)
        # 计算押金总额
        for record in revenue:
            record['deposit'] = db.get_deposit_by_date(record['check_in_date'])  # 假设有此方法
        return jsonify({"success": True, "data": revenue})
    finally:
        db.close()

@statistics_bp.route('/api/statistics/occupancy', methods=['GET'])
def get_occupancy():
    """获取入住率统计"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    db = DatabaseManager()
    try:
        occupancy = db.get_occupancy_rate(start_date, end_date)
        return jsonify({"success": True, "data": occupancy})
    finally:
        db.close()

@statistics_bp.route('/api/statistics/deposit', methods=['GET'])
def get_deposit():
    """获取押金统计"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    db = DatabaseManager()
    try:
        deposit_data = db.get_deposit_statistics(start_date, end_date)
        return jsonify({"success": True, "data": deposit_data})
    finally:
        db.close()

@statistics_bp.route('/api/check-in/<int:check_in_id>/refund', methods=['POST'])
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