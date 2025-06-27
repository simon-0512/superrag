#!/usr/bin/env python3
"""
SuperRAG - 智能问答与知识管理平台
启动文件
"""

import os
from app import create_app

# 创建应用实例
app = create_app()

if __name__ == '__main__':
    # 开发环境配置
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    
    # 运行应用
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 2727)),
        debug=debug_mode
    ) 