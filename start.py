from main import create_app
import os
import sys
from scripts.init_db import init_database

if __name__ == "__main__":
    # 初始化数据库
    init_database()
    
    # 创建应用
    app = create_app()
    
    # 获取端口，如果环境变量没有设置，默认使用5000
    port = int(os.environ.get('PORT', 8088))
    
    # 启动应用
    app.run(host='0.0.0.0', port=port, debug=False) 