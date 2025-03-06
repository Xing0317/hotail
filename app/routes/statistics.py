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