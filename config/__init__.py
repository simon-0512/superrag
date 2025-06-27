"""
配置包
"""

from .settings import Config
from .database import get_database_config

__all__ = ['Config', 'get_database_config'] 