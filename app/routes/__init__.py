"""
路由包
"""

from .main import main_bp
from .api import api_bp
from .mindmap import mindmap_bp

__all__ = ['main_bp', 'api_bp', 'mindmap_bp'] 