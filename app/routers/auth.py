# coding: utf-8
"""认证路由"""

import logging
from fastapi import APIRouter, Depends

from app.schemas.auth import (
    WechatLoginRequest,
    LoginResponse,
    SessionCheckResponse,
    LogoutResponse
)
from app.services.wechat import wechat_service
from app.services.session import session_service, SessionData
from app.dependencies import get_current_session, require_login

log = logging.getLogger(__name__)

router = APIRouter(prefix="/xclub/v1/auth", tags=["认证"])


@router.post("/login", response_model=LoginResponse)
async def login(request: WechatLoginRequest):
    """微信登录
    
    通过微信小程序的 code 换取用户信息，创建服务端 session
    """
    # 调用微信 API 获取 openid 和 session_key
    wechat_result = await wechat_service.code2session(request.code)
    
    openid = wechat_result["openid"]
    session_key = wechat_result["session_key"]
    
    # 获取或创建 session
    session_id, is_new_user = session_service.get_or_create_user(
        openid=openid,
        session_key=session_key,
        nickname=request.nickname,
        avatar_url=request.avatar_url
    )
    
    log.info(f"用户登录成功: openid={openid}, is_new_user={is_new_user}")
    
    return LoginResponse(
        session_id=session_id,
        openid=openid,
        is_new_user=is_new_user
    )


@router.get("/check", response_model=SessionCheckResponse)
async def check_session(session: SessionData = Depends(get_current_session)):
    """检查登录状态
    
    需要在 Header 中传入 X-Session-Id
    """
    if session is None:
        return SessionCheckResponse(valid=False)
    
    return SessionCheckResponse(
        valid=True,
        openid=session.openid,
        nickname=session.nickname
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout(session: SessionData = Depends(require_login)):
    """退出登录
    
    需要在 Header 中传入 X-Session-Id
    """
    # 通过 openid 删除 session
    session_service.delete_session_by_openid(session.openid)
    
    log.info(f"用户退出登录: openid={session.openid}")
    
    return LogoutResponse(message="success")
