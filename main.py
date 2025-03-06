from flask import Flask, render_template, session, redirect, url_for, request, flash
from database.db_manager import DatabaseManager
from app.routes.check_in import check_in_bp
from app.routes.statistics import statistics_bp
from app.routes.rooms import rooms_bp
from app.routes.dashboard import dashboard_bp
from app.middleware import login_required
import os

def create_app():
    # 获取当前文件所在目录的绝对路径
    base_dir = os.path.abspath(os.path.dirname(__file__))
    
    app = Flask(__name__,
                template_folder=os.path.join(base_dir, 'app', 'templates'),
                static_folder=os.path.join(base_dir, 'app', 'static'))
    
    # 设置session密钥
    app.secret_key = 'your-secret-key'
    
    # 注册蓝图
    app.register_blueprint(check_in_bp)
    app.register_blueprint(statistics_bp)
    app.register_blueprint(rooms_bp)
    app.register_blueprint(dashboard_bp)
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        # 如果已经登录，直接跳转到首页
        if 'logged_in' in session:
            return redirect(url_for('index'))
            
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            if username == 'admin' and password == '123456':
                session['logged_in'] = True
                session.permanent = True  # 设置session持久化
                return redirect(url_for('index'))
            return render_template('login.html', error=True)
        return render_template('login.html')

    @app.route('/logout')
    def logout():
        session.clear()  # 清除所有session数据
        return redirect(url_for('login'))
    
    @app.route('/')
    @login_required
    def index():
        return render_template('base.html')
    
    @app.before_request
    def check_login():
        # 不需要登录验证的路由
        public_endpoints = ['login', 'static']
        
        if request.endpoint in public_endpoints:
            return None
            
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        
        return None

    # 添加错误处理
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True) 