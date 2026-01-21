# coding: utf-8
"""认证路由"""

import logging
from fastapi import APIRouter, Depends

from app.schemas.auth import (
    WechatLoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    SessionCheckResponse,
    LogoutResponse
)
from app.services.wechat import wechat_service
from app.services.session import session_service, SessionData
from app.services.user import user_service
from app.dependencies import get_current_session, require_login
from app.core.response import success, ErrorCode
from app.core.exceptions import BizError

log = logging.getLogger(__name__)

router = APIRouter(prefix="/xclub/v1/auth", tags=["认证"])


@router.post("/login")
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
    
    # 获取用户角色信息
    user = user_service.get_user_by_openid(openid)
    role = user.get('role', 1) if user else 1
    role_name = user.get('role_name', '游客') if user else '游客'
    
    log.info(f"用户登录成功: openid={openid}, is_new_user={is_new_user}")
    
    return success(data={
        "session_id": session_id,
        "openid": openid,
        "is_new_user": is_new_user,
        "role": role,
        "role_name": role_name
    })


@router.get("/check")
async def check_session(session: SessionData = Depends(get_current_session)):
    """检查登录状态
    
    需要在 Header 中传入 X-Session-Id
    """
    if session is None:
        return success(data={"valid": False})
    
    # 获取用户信息以获取 role
    user = user_service.get_user_by_openid(session.openid)
    role = user.get('role', 1) if user else 1
    role_name = user.get('role_name', '游客') if user else '游客'
    
    return success(data={
        "valid": True,
        "openid": session.openid,
        "nickname": session.nickname,
        "role": role,
        "role_name": role_name
    })


@router.post("/logout")
async def logout(session: SessionData = Depends(require_login)):
    """退出登录
    
    需要在 Header 中传入 X-Session-Id
    """
    # 通过 openid 删除 session
    session_service.delete_session_by_openid(session.openid)
    
    log.info(f"用户退出登录: openid={session.openid}")
    
    return success(msg="退出成功")


@router.post("/register")
async def register(request: RegisterRequest):
    """用户注册
    
    使用激活码注册，注册成功后自动创建 session
    激活码只能使用一次，使用后会关联到用户
    """
    # 调用微信 API 获取 openid 和 session_key
    wechat_result = await wechat_service.code2session(request.code)
    
    openid = wechat_result["openid"]
    session_key = wechat_result["session_key"]
    
    # 注册用户
    user_id, error_msg = user_service.register_user(
        openid=openid,
        activation_code=request.activation_code,
        realname=request.realname or "",
        nickname=request.nickname or "",
        avatar=request.avatar_url or "",
    )
    
    if error_msg:
        # 根据错误信息返回不同的错误码
        error_code_map = {
            "激活码不存在": ErrorCode.ACTIVATION_CODE_NOT_FOUND,
            "激活码已被使用": ErrorCode.ACTIVATION_CODE_USED,
            "激活码已作废": ErrorCode.ACTIVATION_CODE_INVALID,
            "用户已注册": ErrorCode.USER_ALREADY_REGISTERED,
        }
        code = error_code_map.get(error_msg, ErrorCode.PARAM_ERROR)
        raise BizError(code=code, msg=error_msg)
    
    # 创建 session
    session_id = session_service.create_session(
        openid=openid,
        session_key=session_key,
        nickname=request.nickname,
        avatar_url=request.avatar_url,
    )
    
    # 获取用户角色信息
    user = user_service.get_user_by_openid(openid)
    role = user.get('role', 1) if user else 2  # 注册成功默认为成员
    role_name = user.get('role_name', '成员') if user else '成员'
    
    log.info(f"用户注册成功: openid={openid}, user_id={user_id}")
    
    return success(data={
        "session_id": session_id,
        "openid": openid,
        "user_id": user_id,
        "role": role,
        "role_name": role_name
    }, msg="注册成功")
