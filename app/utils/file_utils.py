"""
文件上传工具模块
"""

import os
import uuid
from PIL import Image, ImageOps
from werkzeug.utils import secure_filename
from flask import current_app

# 允许的图片格式
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
# 最大文件大小（1MB）
MAX_FILE_SIZE = 1 * 1024 * 1024

def allowed_file(filename):
    """检查文件是否允许上传"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_size(file):
    """获取文件大小"""
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    return size

def generate_unique_filename(filename):
    """生成唯一的文件名"""
    ext = filename.rsplit('.', 1)[1].lower()
    unique_id = str(uuid.uuid4())
    return f"{unique_id}.{ext}"

def create_circular_avatar(image_path, output_path, size=(200, 200)):
    """创建圆形头像"""
    try:
        with Image.open(image_path) as img:
            # 转换为RGB模式
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 裁剪为正方形（取较小的边长）
            width, height = img.size
            min_size = min(width, height)
            
            # 计算裁剪区域（居中）
            left = (width - min_size) // 2
            top = (height - min_size) // 2
            right = left + min_size
            bottom = top + min_size
            
            # 裁剪为正方形
            img = img.crop((left, top, right, bottom))
            
            # 调整大小
            img = img.resize(size, Image.Resampling.LANCZOS)
            
            # 创建圆形遮罩
            mask = Image.new('L', size, 0)
            from PIL import ImageDraw
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0) + size, fill=255)
            
            # 应用圆形遮罩
            output = ImageOps.fit(img, mask.size, centering=(0.5, 0.5))
            output.putalpha(mask)
            
            # 保存为PNG格式以支持透明度
            output.save(output_path, 'PNG')
            return True
            
    except Exception as e:
        current_app.logger.error(f"创建圆形头像失败: {e}")
        return False

def save_avatar(file, user_id):
    """保存用户头像"""
    try:
        # 检查文件格式
        if not allowed_file(file.filename):
            return None, "不支持的文件格式"
        
        # 检查文件大小
        if get_file_size(file) > MAX_FILE_SIZE:
            return None, "文件大小超过1MB限制"
        
        # 创建上传目录
        upload_dir = os.path.join(current_app.static_folder, 'uploads', 'avatars')
        os.makedirs(upload_dir, exist_ok=True)
        
        # 生成文件名
        filename = generate_unique_filename(file.filename)
        temp_path = os.path.join(upload_dir, f"temp_{filename}")
        final_path = os.path.join(upload_dir, filename)
        
        # 保存临时文件
        file.save(temp_path)
        
        # 创建圆形头像
        if create_circular_avatar(temp_path, final_path):
            # 删除临时文件
            os.remove(temp_path)
            
            # 返回相对URL路径
            avatar_url = f"/static/uploads/avatars/{filename}"
            return avatar_url, "头像上传成功"
        else:
            # 清理文件
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return None, "头像处理失败"
            
    except Exception as e:
        current_app.logger.error(f"头像上传失败: {e}")
        return None, f"上传失败: {str(e)}"

def delete_avatar(avatar_url):
    """删除头像文件"""
    try:
        if avatar_url and avatar_url.startswith('/static/uploads/avatars/'):
            file_path = os.path.join(current_app.static_folder, avatar_url[1:])  # 去掉开头的/
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
    except Exception as e:
        current_app.logger.error(f"删除头像失败: {e}")
    return False 