# coding: utf-8
"""依赖注入"""

from fastapi import Header, HTTPException
from typing import Optional

from app.services.session import session_service, SessionData


async def get_session_id(
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id")
) -> Optional[str]:
    """从 Header 获取 session_id"""
    return x_session_id


async def get_current_session(
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id")
) -> Optional[SessionData]:
    """获取当前 session (可选)
    
    如果未提供 session_id 或 session 无效，返回 None
    """
    if not x_session_id:
        return None
    return session_service.get_session(x_session_id)


async def require_login(
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id")
) -> SessionData:
    """要求登录
    
    如果未登录或 session 无效，抛出 401 错误
    """
    if not x_session_id:
        raise HTTPException(
            status_code=401,
            detail="未登录，请先登录"
        )
    
    session = session_service.get_session(x_session_id)
    if not session:
        raise HTTPException(
            status_code=401,
            detail="登录已过期，请重新登录"
        )
    
    return session
