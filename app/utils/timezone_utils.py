"""
时区处理工具
统一处理时间为东八区时间
"""

from datetime import datetime, timezone, timedelta
import pytz

# 东八区时区对象
BEIJING_TZ = pytz.timezone('Asia/Shanghai')
UTC_TZ = pytz.UTC

def get_beijing_now():
    """获取当前东八区时间"""
    return datetime.now(BEIJING_TZ)

def get_beijing_time_for_db():
    """获取用于数据库存储的东八区时间（naive datetime）"""
    # 数据库存储时我们统一存储东八区的naive time
    return get_beijing_now().replace(tzinfo=None)

def utc_to_beijing(utc_dt):
    """将UTC时间转换为东八区时间"""
    if utc_dt is None:
        return None
    
    # 如果是naive datetime，假设它是UTC时间
    if utc_dt.tzinfo is None:
        utc_dt = UTC_TZ.localize(utc_dt)
    
    # 转换为东八区时间
    beijing_dt = utc_dt.astimezone(BEIJING_TZ)
    return beijing_dt.replace(tzinfo=None)  # 返回naive datetime

def beijing_to_utc(beijing_dt):
    """将东八区时间转换为UTC时间"""
    if beijing_dt is None:
        return None
    
    # 如果是naive datetime，假设它是东八区时间
    if beijing_dt.tzinfo is None:
        beijing_dt = BEIJING_TZ.localize(beijing_dt)
    
    # 转换为UTC时间
    utc_dt = beijing_dt.astimezone(UTC_TZ)
    return utc_dt.replace(tzinfo=None)  # 返回naive datetime

def format_beijing_time(dt, format_str='%Y-%m-%d %H:%M:%S'):
    """格式化东八区时间显示"""
    if dt is None:
        return None
    
    # 如果是naive datetime，假设它已经是东八区时间
    if dt.tzinfo is None:
        return dt.strftime(format_str)
    
    # 如果有时区信息，转换为东八区后格式化
    if dt.tzinfo != BEIJING_TZ:
        dt = dt.astimezone(BEIJING_TZ)
    
    return dt.strftime(format_str) 