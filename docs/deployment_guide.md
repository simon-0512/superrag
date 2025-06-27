# SuperRAG 云服务器部署指南

本指南将详细介绍如何在阿里云、腾讯云等主流云服务平台上部署SuperRAG系统。

## 📋 系统要求

### 最低配置
- **CPU**: 2核
- **内存**: 4GB
- **存储**: 40GB SSD
- **操作系统**: Ubuntu 20.04 LTS 或 CentOS 8
- **网络**: 5Mbps 带宽

### 推荐配置
- **CPU**: 4核
- **内存**: 8GB
- **存储**: 100GB SSD
- **操作系统**: Ubuntu 22.04 LTS
- **网络**: 10Mbps 带宽

## 🚀 部署步骤

### 1. 服务器准备

#### 1.1 创建云服务器

**阿里云 ECS**
```bash
# 选择实例规格: ecs.t6-c1m2.large 或更高
# 操作系统: Ubuntu 22.04 LTS
# 存储: 40GB 以上 SSD
# 网络: 分配公网IP，带宽5Mbps以上
```

**腾讯云 CVM**
```bash
# 选择实例规格: S5.MEDIUM4 或更高
# 操作系统: Ubuntu Server 22.04 LTS
# 存储: 40GB 以上高性能云硬盘
# 网络: 分配公网IP，带宽5Mbps以上
```

#### 1.2 配置安全组

**开放端口**
- 22 (SSH)
- 80 (HTTP)
- 443 (HTTPS)
- 5432 (PostgreSQL，仅内网)

**防火墙规则**
```bash
# Ubuntu UFW 配置
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow from 10.0.0.0/8 to any port 5432
sudo ufw enable
```

### 2. 系统环境配置

#### 2.1 更新系统
```bash
# Ubuntu
sudo apt update && sudo apt upgrade -y

# CentOS
sudo yum update -y
```

#### 2.2 安装基础依赖
```bash
# Ubuntu
sudo apt install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib redis-server git curl wget

# CentOS
sudo yum install -y python3 python3-pip nginx postgresql postgresql-server redis git curl wget
sudo python3 -m ensurepip --upgrade
```

#### 2.3 配置 PostgreSQL
```bash
# 启动 PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 创建数据库和用户
sudo -u postgres psql << EOF
CREATE DATABASE superrag;
CREATE USER superrag WITH PASSWORD 'your_secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE superrag TO superrag;
ALTER USER superrag CREATEDB;
\q
EOF

# 配置 PostgreSQL 连接
sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = 'localhost'/" /etc/postgresql/*/main/postgresql.conf
sudo sed -i "s/local   all             all                                     peer/local   all             all                                     md5/" /etc/postgresql/*/main/pg_hba.conf
sudo systemctl restart postgresql
```

#### 2.4 配置 Redis
```bash
# 启动 Redis
sudo systemctl start redis
sudo systemctl enable redis

# 配置 Redis (可选: 设置密码)
sudo sed -i 's/# requirepass foobared/requirepass your_redis_password/' /etc/redis/redis.conf
sudo systemctl restart redis
```

### 3. 应用部署

#### 3.1 创建应用用户
```bash
# 创建专用用户
sudo adduser --system --group --home /opt/superrag superrag
sudo usermod -a -G www-data superrag
```

#### 3.2 下载代码
```bash
# 切换到应用用户
sudo -u superrag -i

# 克隆代码 (替换为你的代码仓库地址)
cd /opt/superrag
git clone https://github.com/your-username/SuperRAG.git app
cd app

# 或者上传代码包
# scp -r ./SuperRAG user@your-server-ip:/opt/superrag/app
```

#### 3.3 创建虚拟环境
```bash
# 创建 Python 虚拟环境
python3 -m venv venv
source venv/bin/activate

# 升级 pip
pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt
```

#### 3.4 配置环境变量
```bash
# 创建环境配置文件
cat > .env << EOF
# Flask 配置
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-change-this-in-production

# 数据库配置
DB_HOST=localhost
DB_PORT=5432
DB_NAME=superrag
DB_USER=superrag
DB_PASSWORD=your_secure_password_here

# Redis 配置
REDIS_URL=redis://localhost:6379/0

# DeepSeek API 配置
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com

# 文件上传配置
UPLOAD_PATH=/opt/superrag/uploads
MAX_CONTENT_LENGTH=100MB

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=/opt/superrag/logs/app.log
EOF

# 设置文件权限
chmod 600 .env
```

#### 3.5 初始化数据库
```bash
# 初始化数据库
python manage.py init_db

# 检查数据库状态
python manage.py health_check
python manage.py db_info
```

#### 3.6 创建必要目录
```bash
# 创建上传和日志目录
mkdir -p /opt/superrag/uploads
mkdir -p /opt/superrag/logs
mkdir -p /opt/superrag/static
mkdir -p /opt/superrag/backups

# 设置权限
sudo chown -R superrag:superrag /opt/superrag
sudo chmod -R 755 /opt/superrag
sudo chmod -R 777 /opt/superrag/uploads
sudo chmod -R 777 /opt/superrag/logs
```

### 4. 配置 Web 服务器

#### 4.1 配置 Gunicorn
```bash
# 创建 Gunicorn 配置文件
cat > /opt/superrag/app/gunicorn.conf.py << EOF
import multiprocessing

# 服务器配置
bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 60
keepalive = 2
max_requests = 1000
max_requests_jitter = 100

# 应用配置
wsgi_module = "run:app"
pythonpath = "/opt/superrag/app"

# 日志配置
accesslog = "/opt/superrag/logs/gunicorn_access.log"
errorlog = "/opt/superrag/logs/gunicorn_error.log"
loglevel = "info"

# 进程配置
daemon = False
pidfile = "/opt/superrag/gunicorn.pid"
user = "superrag"
group = "superrag"
EOF
```

#### 4.2 创建 systemd 服务
```bash
# 创建服务文件
sudo tee /etc/systemd/system/superrag.service << EOF
[Unit]
Description=SuperRAG Gunicorn application server
Documentation=https://github.com/your-username/SuperRAG
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=superrag
Group=superrag
RuntimeDirectory=superrag
WorkingDirectory=/opt/superrag/app
Environment=PATH=/opt/superrag/app/venv/bin
EnvironmentFile=/opt/superrag/app/.env
ExecStart=/opt/superrag/app/venv/bin/gunicorn --config /opt/superrag/app/gunicorn.conf.py
ExecReload=/bin/kill -s HUP \$MAINPID
ExecStop=/bin/kill -s TERM \$MAINPID
TimeoutStopSec=5
KillMode=mixed
PrivateTmp=true
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 启动服务
sudo systemctl daemon-reload
sudo systemctl enable superrag
sudo systemctl start superrag
sudo systemctl status superrag
```

#### 4.3 配置 Nginx
```bash
# 创建 Nginx 配置
sudo tee /etc/nginx/sites-available/superrag << EOF
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    # 静态文件
    location /static/ {
        alias /opt/superrag/app/app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # 上传文件
    location /uploads/ {
        alias /opt/superrag/uploads/;
        expires 1h;
    }
    
    # 应用代理
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
        
        # 文件上传大小限制
        client_max_body_size 100M;
    }
    
    # 安全配置
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    
    # 日志
    access_log /var/log/nginx/superrag_access.log;
    error_log /var/log/nginx/superrag_error.log;
}
EOF

# 启用站点
sudo ln -s /etc/nginx/sites-available/superrag /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 5. SSL 证书配置 (推荐)

#### 5.1 使用 Let's Encrypt
```bash
# 安装 Certbot
sudo apt install -y certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# 设置自动续期
sudo crontab -e
# 添加以下行:
# 0 12 * * * /usr/bin/certbot renew --quiet
```

### 6. 监控和备份

#### 6.1 创建备份脚本
```bash
# 创建备份脚本
sudo tee /opt/superrag/backup.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="/opt/superrag/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="superrag"
DB_USER="superrag"

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 数据库备份
pg_dump -h localhost -U "$DB_USER" -W "$DB_NAME" > "$BACKUP_DIR/db_backup_$DATE.sql"

# 文件备份
tar -czf "$BACKUP_DIR/uploads_backup_$DATE.tar.gz" /opt/superrag/uploads

# 清理旧备份 (保留30天)
find "$BACKUP_DIR" -name "*.sql" -mtime +30 -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
EOF

sudo chmod +x /opt/superrag/backup.sh

# 设置定时备份
sudo crontab -e
# 添加以下行 (每天凌晨2点备份):
# 0 2 * * * /opt/superrag/backup.sh >> /opt/superrag/logs/backup.log 2>&1
```

#### 6.2 日志轮转
```bash
# 配置 logrotate
sudo tee /etc/logrotate.d/superrag << EOF
/opt/superrag/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 superrag superrag
    postrotate
        systemctl reload superrag
    endscript
}
EOF
```

### 7. 性能优化

#### 7.1 数据库优化
```bash
# 优化 PostgreSQL 配置
sudo tee -a /etc/postgresql/*/main/postgresql.conf << EOF
# 性能优化
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
EOF

sudo systemctl restart postgresql
```

#### 7.2 Redis 优化
```bash
# 优化 Redis 配置
sudo tee -a /etc/redis/redis.conf << EOF
# 内存优化
maxmemory 512mb
maxmemory-policy allkeys-lru

# 持久化配置
save 900 1
save 300 10
save 60 10000
EOF

sudo systemctl restart redis
```

## 🔧 故障排除

### 常见问题

#### 1. 服务无法启动
```bash
# 检查服务状态
sudo systemctl status superrag
sudo journalctl -u superrag -f

# 检查日志
tail -f /opt/superrag/logs/gunicorn_error.log
tail -f /opt/superrag/logs/app.log
```

#### 2. 数据库连接失败
```bash
# 检查 PostgreSQL 状态
sudo systemctl status postgresql

# 测试数据库连接
sudo -u postgres psql -c "SELECT version();"

# 检查配置
cat /etc/postgresql/*/main/pg_hba.conf | grep local
```

#### 3. 文件上传问题
```bash
# 检查目录权限
ls -la /opt/superrag/uploads/

# 检查 Nginx 配置
sudo nginx -t
tail -f /var/log/nginx/superrag_error.log
```

### 性能监控
```bash
# 系统资源监控
htop
iotop
df -h

# 应用监控
curl -I http://localhost
sudo netstat -tulpn | grep :8000
```

## 📝 维护清单

### 日常维护
- [ ] 检查服务状态
- [ ] 查看错误日志
- [ ] 监控磁盘空间
- [ ] 检查备份状态

### 周期性维护
- [ ] 更新系统包
- [ ] 更新应用代码
- [ ] 清理日志文件
- [ ] 检查安全补丁

### 安全检查
- [ ] 检查登录日志
- [ ] 更新密码
- [ ] 检查防火墙规则
- [ ] 验证SSL证书

## 🔗 相关链接

- [阿里云ECS文档](https://help.aliyun.com/product/25365.html)
- [腾讯云CVM文档](https://cloud.tencent.com/document/product/213)
- [Ubuntu服务器指南](https://ubuntu.com/server/docs)
- [Nginx官方文档](https://nginx.org/en/docs/)
- [PostgreSQL文档](https://www.postgresql.org/docs/)

---

> **注意**: 请根据实际情况调整配置参数，确保在生产环境中使用强密码和适当的安全配置。 