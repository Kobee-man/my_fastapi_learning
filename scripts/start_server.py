"""
FastAPI 启动脚本 - 配置热重载排除目录

使用方法:
    python start_server.py
    
功能特点:
    - 排除不必要的监控目录，避免死循环
    - 优化开发体验
"""

import uvicorn
import os

if __name__ == "__main__":
    # 获取项目根目录
    project_dir = os.path.dirname(os.path.abspath(__file__))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        # 排除监控目录 - 防止热重载死循环
        reload_excludes=[
            "node_modules",
            "frontend",
            "dist",
            "__pycache__",
            "*.pyc",
            "*.pyo",
            ".git",
            "*.log",
            "*.db",
            "logs"
        ],
        # 只监控必要的Python文件目录
        reload_dirs=[
            ".",
            "api",
            "core",
            "models"
        ],
        # 日志级别
        log_level="info"
    )
