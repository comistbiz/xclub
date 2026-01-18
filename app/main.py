# coding: utf-8
"""FastAPI 应用入口"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings, DATABASE
from app.routers import auth, record, user
from app.core.exceptions import setup_exception_handlers
from app.db import install as db_install

# 配置日志
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

log = logging.getLogger(__name__)

# 初始化数据库连接池
db_install(DATABASE)

# 创建 FastAPI 应用
app = FastAPI(
    title="XClub API",
    description="俱乐部小程序后端 API - 支持微信登录和飞书多维表格打卡",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(record.router)

# 注册异常处理
setup_exception_handlers(app)


@app.get("/", tags=["健康检查"])
def root():
    """根路径"""
    return {
        "service": settings.APP_NAME,
        "version": "2.0.0",
        "status": "running"
    }


@app.get("/health", tags=["健康检查"])
def health_check():
    """健康检查"""
    return {"status": "ok"}


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    log.info(f"XClub API 启动成功")
    log.info(f"API 文档: http://localhost:9900/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    log.info("XClub API 关闭")
