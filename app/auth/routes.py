"""
认证相关路由
"""

from flask import render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from app.auth import auth_bp
from app.models import User
from app.database import db
import re

def validate_email(email):
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """验证密码强度"""
    if len(password) < 6:
        return False, "密码至少需要6个字符"
    if len(password) > 128:
        return False, "密码不能超过128个字符"
    return True, ""

def validate_username(username):
    """验证用户名"""
    if len(username) < 3:
        return False, "用户名至少需要3个字符"
    if len(username) > 20:
        return False, "用户名不能超过20个字符"
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "用户名只能包含字母、数字和下划线"
    return True, ""

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        try:
            data = request.get_json() if request.is_json else request.form
            
            username_or_email = data.get('username', '').strip()
            password = data.get('password', '')
            remember_me = data.get('remember_me', False)
            
            if not username_or_email or not password:
                message = '请输入用户名/邮箱和密码'
                if request.is_json:
                    return jsonify({'success': False, 'message': message}), 400
                flash(message, 'error')
                return render_template('auth/login.html')
            
            # 查找用户（支持用户名或邮箱登录）
            user = None
            if validate_email(username_or_email):
                user = User.query.filter_by(email=username_or_email).first()
            else:
                user = User.query.filter_by(username=username_or_email).first()
            
            if user and user.check_password(password):
                # 检查用户是否被软删除
                if user.is_deleted():
                    message = '账号不存在或已被删除，请联系管理员'
                    if request.is_json:
                        return jsonify({'success': False, 'message': message}), 403
                    flash(message, 'error')
                    return render_template('auth/login.html')
                
                # 检查用户是否可以登录（删除用户不能登录，禁用用户可以登录但功能受限）
                if not user.can_login():
                    message = '账号无法登录，请联系管理员'
                    if request.is_json:
                        return jsonify({'success': False, 'message': message}), 403
                    flash(message, 'error')
                    return render_template('auth/login.html')
                
                # 登录用户
                login_user(user, remember=remember_me)
                user.update_last_login()
                
                # 获取下一页URL
                next_page = request.args.get('next')
                if not next_page or urlparse(next_page).netloc != '':
                    next_page = url_for('main.dashboard')
                
                if request.is_json:
                    return jsonify({
                        'success': True,
                        'message': '登录成功',
                        'redirect': next_page,
                        'user': user.to_dict()
                    })
                
                flash('登录成功！', 'success')
                return redirect(next_page)
            
            else:
                message = '用户名/邮箱或密码错误'
                if request.is_json:
                    return jsonify({'success': False, 'message': message}), 401
                flash(message, 'error')
        
        except Exception as e:
            message = f'登录时发生错误: {str(e)}'
            if request.is_json:
                return jsonify({'success': False, 'message': message}), 500
            flash(message, 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        try:
            data = request.get_json() if request.is_json else request.form
            
            username = data.get('username', '').strip()
            email = data.get('email', '').strip()
            password = data.get('password', '')
            confirm_password = data.get('confirm_password', '')
            nickname = data.get('nickname', '').strip()
            
            # 验证输入
            if not username or not email or not password:
                message = '请填写所有必填字段'
                if request.is_json:
                    return jsonify({'success': False, 'message': message}), 400
                flash(message, 'error')
                return render_template('auth/register.html')
            
            # 验证用户名
            valid, msg = validate_username(username)
            if not valid:
                if request.is_json:
                    return jsonify({'success': False, 'message': msg}), 400
                flash(msg, 'error')
                return render_template('auth/register.html')
            
            # 验证邮箱格式
            if not validate_email(email):
                message = '请输入有效的邮箱地址'
                if request.is_json:
                    return jsonify({'success': False, 'message': message}), 400
                flash(message, 'error')
                return render_template('auth/register.html')
            
            # 验证密码
            valid, msg = validate_password(password)
            if not valid:
                if request.is_json:
                    return jsonify({'success': False, 'message': msg}), 400
                flash(msg, 'error')
                return render_template('auth/register.html')
            
            # 验证密码确认
            if password != confirm_password:
                message = '两次输入的密码不一致'
                if request.is_json:
                    return jsonify({'success': False, 'message': message}), 400
                flash(message, 'error')
                return render_template('auth/register.html')
            
            # 检查用户名是否已存在
            if User.query.filter_by(username=username).first():
                message = '用户名已存在'
                if request.is_json:
                    return jsonify({'success': False, 'message': message}), 409
                flash(message, 'error')
                return render_template('auth/register.html')
            
            # 检查邮箱是否已存在
            if User.query.filter_by(email=email).first():
                message = '邮箱已被注册'
                if request.is_json:
                    return jsonify({'success': False, 'message': message}), 409
                flash(message, 'error')
                return render_template('auth/register.html')
            
            # 创建新用户
            user = User(username=username, email=email, password=password)
            if nickname:
                user.nickname = nickname
            else:
                user.nickname = username
            
            db.session.add(user)
            db.session.commit()
            
            # 处理头像上传（如果有）
            if 'avatar' in request.files:
                avatar_file = request.files['avatar']
                if avatar_file and avatar_file.filename != '':
                    try:
                        from app.utils.file_utils import save_avatar
                        avatar_url, avatar_message = save_avatar(avatar_file, user.id)
                        if avatar_url:
                            user.avatar_url = avatar_url
                            db.session.commit()
                    except Exception as e:
                        print(f"头像上传失败: {str(e)}")
                        # 头像上传失败不影响注册，继续流程
            
            # 设置默认角色（普通用户）
            try:
                user.set_role('user')
                print(f"✅ 为用户 {username} 设置了默认角色 'user'")
            except Exception as e:
                print(f"⚠️  为用户 {username} 设置默认角色失败: {str(e)}")
            
            # 自动登录
            login_user(user)
            user.update_last_login()
            
            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': '注册成功',
                    'redirect': url_for('main.dashboard'),
                    'user': user.to_dict()
                })
            
            flash('注册成功！欢迎使用SuperRAG！', 'success')
            return redirect(url_for('main.dashboard'))
        
        except Exception as e:
            db.session.rollback()
            message = f'注册时发生错误: {str(e)}'
            if request.is_json:
                return jsonify({'success': False, 'message': message}), 500
            flash(message, 'error')
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """用户登出"""
    logout_user()
    flash('您已成功登出', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/profile')
@login_required
def profile():
    """用户资料页面"""
    return render_template('auth/profile.html', user=current_user)

@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """编辑用户资料"""
    if request.method == 'POST':
        try:
            data = request.get_json() if request.is_json else request.form
            
            nickname = data.get('nickname', '').strip()
            bio = data.get('bio', '').strip()
            email = data.get('email', '').strip()
            
            # 验证邮箱
            if email and email != current_user.email:
                if not validate_email(email):
                    message = '请输入有效的邮箱地址'
                    if request.is_json:
                        return jsonify({'success': False, 'message': message}), 400
                    flash(message, 'error')
                    return render_template('auth/edit_profile.html')
                
                # 检查邮箱是否已被使用
                if User.query.filter_by(email=email).first():
                    message = '邮箱已被其他用户使用'
                    if request.is_json:
                        return jsonify({'success': False, 'message': message}), 409
                    flash(message, 'error')
                    return render_template('auth/edit_profile.html')
                
                current_user.email = email
                current_user.is_verified = False  # 需要重新验证邮箱
            
            # 更新其他字段
            if nickname:
                current_user.nickname = nickname
            if bio:
                current_user.bio = bio
            
            db.session.commit()
            
            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': '资料更新成功',
                    'user': current_user.to_dict(include_private=True)
                })
            
            flash('资料更新成功！', 'success')
            return redirect(url_for('auth.profile'))
        
        except Exception as e:
            db.session.rollback()
            message = f'更新资料时发生错误: {str(e)}'
            if request.is_json:
                return jsonify({'success': False, 'message': message}), 500
            flash(message, 'error')
    
    return render_template('auth/edit_profile.html')

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """修改密码"""
    try:
        data = request.get_json() if request.is_json else request.form
        
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        confirm_password = data.get('confirm_password', '')
        
        # 验证当前密码
        if not current_user.check_password(current_password):
            message = '当前密码错误'
            if request.is_json:
                return jsonify({'success': False, 'message': message}), 400
            flash(message, 'error')
            return redirect(url_for('auth.edit_profile'))
        
        # 验证新密码
        valid, msg = validate_password(new_password)
        if not valid:
            if request.is_json:
                return jsonify({'success': False, 'message': msg}), 400
            flash(msg, 'error')
            return redirect(url_for('auth.edit_profile'))
        
        # 验证密码确认
        if new_password != confirm_password:
            message = '两次输入的新密码不一致'
            if request.is_json:
                return jsonify({'success': False, 'message': message}), 400
            flash(message, 'error')
            return redirect(url_for('auth.edit_profile'))
        
        # 更新密码
        current_user.set_password(new_password)
        db.session.commit()
        
        if request.is_json:
            return jsonify({'success': True, 'message': '密码修改成功'})
        
        flash('密码修改成功！', 'success')
        return redirect(url_for('auth.profile'))
    
    except Exception as e:
        db.session.rollback()
        message = f'修改密码时发生错误: {str(e)}'
        if request.is_json:
            return jsonify({'success': False, 'message': message}), 500
        flash(message, 'error')
        return redirect(url_for('auth.edit_profile'))

@auth_bp.route('/api/current_user')
@login_required
def api_current_user():
    """获取当前用户信息API"""
    return jsonify({
        'success': True,
        'user': current_user.to_dict(include_private=True)
    })

@auth_bp.route('/api/check_username/<username>')
def api_check_username(username):
    """检查用户名是否可用"""
    valid, msg = validate_username(username)
    if not valid:
        return jsonify({'available': False, 'message': msg})
    
    user = User.query.filter_by(username=username).first()
    return jsonify({
        'available': user is None,
        'message': '用户名可用' if user is None else '用户名已存在'
    })

@auth_bp.route('/api/check_email/<email>')
def api_check_email(email):
    """检查邮箱是否可用"""
    if not validate_email(email):
        return jsonify({'available': False, 'message': '邮箱格式不正确'})
    
    user = User.query.filter_by(email=email).first()
    return jsonify({
        'available': user is None,
        'message': '邮箱可用' if user is None else '邮箱已被注册'
    })

@auth_bp.route('/upload_avatar', methods=['POST'])
@login_required
def upload_avatar():
    """上传用户头像"""
    try:
        if 'avatar' not in request.files:
            return jsonify({'success': False, 'message': '没有选择文件'})
        
        file = request.files['avatar']
        if file.filename == '':
            return jsonify({'success': False, 'message': '没有选择文件'})
        
        # 导入头像处理函数
        from app.utils.file_utils import save_avatar, delete_avatar
        
        # 删除旧头像
        if current_user.avatar_url:
            delete_avatar(current_user.avatar_url)
        
        # 保存新头像
        avatar_url, message = save_avatar(file, current_user.id)
        
        if avatar_url:
            current_user.avatar_url = avatar_url
            db.session.commit()
            return jsonify({'success': True, 'message': message, 'avatar_url': avatar_url})
        else:
            return jsonify({'success': False, 'message': message})
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'上传失败: {str(e)}'})

@auth_bp.route('/remove_avatar', methods=['POST'])
@login_required
def remove_avatar():
    """删除用户头像"""
    try:
        if current_user.avatar_url:
            from app.utils.file_utils import delete_avatar
            delete_avatar(current_user.avatar_url)
            current_user.avatar_url = None
            db.session.commit()
            return jsonify({'success': True, 'message': '头像删除成功'})
        else:
            return jsonify({'success': False, 'message': '没有头像可删除'})
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}) 