# coding: utf-8
"""配置管理"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""
    
    # 服务配置
    APP_NAME: str = "xclub"
    DEBUG: bool = True
    
    # 微信小程序配置
    WECHAT_APPID: str = ""
    WECHAT_SECRET: str = ""
    
    # 飞书应用凭证
    FEISHU_APP_ID: str = ""
    FEISHU_APP_SECRET: str = ""
    
    # 飞书多维表格配置
    FEISHU_APP_TOKEN: str = ""      # 多维表格 App Token
    FEISHU_TABLE_ID: str = ""       # 数据表 ID
    
    # Session 配置
    SESSION_EXPIRE_SECONDS: int = 86400 * 7  # 7 天过期
    
    # 数据库配置
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "xclub"
    DB_CHARSET: str = "utf8mb4"
    DB_POOL_SIZE: int = 10
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()


# 数据库配置字典 (用于 dbpool.install)
DATABASE = {
    'xclub': {
        'engine': 'pymysql',
        'host': settings.DB_HOST,
        'port': settings.DB_PORT,
        'user': settings.DB_USER,
        'passwd': settings.DB_PASSWORD,
        'db': settings.DB_NAME,
        'charset': settings.DB_CHARSET,
        'conn': settings.DB_POOL_SIZE,
        'idle_timeout': 60,
    }
}
