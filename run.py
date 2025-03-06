import os
import sys

# 将项目根目录添加到 Python 路径
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.append(project_root)

from scripts.init_db import init_test_data

if __name__ == "__main__":
    init_test_data() 