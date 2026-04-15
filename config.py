"""配置文件"""
import os

# 数据库配置
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "password"),
    "database": os.getenv("DB_NAME", "organization_db"),
    "charset": "utf8mb4"
}

# JWT配置
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60 * 24 * 7  # 7天过期

# 微信小程序配置
WECHAT_APPID = os.getenv("WECHAT_APPID", "your-appid")
WECHAT_SECRET = os.getenv("WECHAT_SECRET", "your-secret")
