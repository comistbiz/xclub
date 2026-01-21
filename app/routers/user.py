# coding: utf-8
"""用户路由"""

import logging
from fastapi import APIRouter, Depends

from app.schemas.user import UserInfo, UserUpdate, UserRoleUpdate
from app.services.user import user_service
from app.services.session import SessionData
from app.dependencies import require_login
from app.core.response import success, ErrorCode
from app.core.exceptions import BizError

log = logging.getLogger(__name__)

router = APIRouter(prefix="/xclub/v1/user", tags=["用户"])


@router.get("/info")
async def get_current_user_info(session: SessionData = Depends(require_login)):
    """获取当前登录用户信息
    
    需要在 Header 中传入 X-Session-Id
    """
    user = user_service.get_user_by_openid(session.openid)
    
    if not user:
        # 用户不存在，自动创建
        user, _ = user_service.get_or_create_user(
            openid=session.openid,
            nickname=session.nickname or "",
            avatar=session.avatar_url or ""
        )
    
    return success(data=UserInfo(**user).model_dump())


@router.get("/{user_id}")
async def get_user_info(
    user_id: int,
    session: SessionData = Depends(require_login)
):
    """获取指定用户信息
    
    需要在 Header 中传入 X-Session-Id
    """
    user = user_service.get_user_by_id(user_id)
    
    if not user:
        raise BizError(code=ErrorCode.USER_NOT_FOUND, msg="用户不存在")
    
    return success(data=UserInfo(**user).model_dump())


@router.put("/info")
async def update_current_user_info(
    data: UserUpdate,
    session: SessionData = Depends(require_login)
):
    """更新当前登录用户信息
    
    需要在 Header 中传入 X-Session-Id
    """
    update_data = data.model_dump(exclude_none=True)
    
    if not update_data:
        raise BizError(code=ErrorCode.PARAM_ERROR, msg="没有要更新的数据")
    
    # 确保用户存在
    user = user_service.get_user_by_openid(session.openid)
    if not user:
        user_service.create_user(
            openid=session.openid,
            nickname=session.nickname or "",
            avatar=session.avatar_url or ""
        )
    
    # 更新用户信息
    user_service.update_user(session.openid, **update_data)
    
    # 返回更新后的用户信息
    updated_user = user_service.get_user_by_openid(session.openid)
    return success(data=UserInfo(**updated_user).model_dump())


@router.put("/{user_id}/role")
async def update_user_role(
    user_id: int,
    data: UserRoleUpdate,
    session: SessionData = Depends(require_login)
):
    """更新用户角色 (仅管理员)
    
    需要在 Header 中传入 X-Session-Id
    """
    # 检查当前用户是否为管理员
    if not user_service.is_admin(session.openid):
        raise BizError(code=ErrorCode.FORBIDDEN, msg="需要管理员权限")
    
    # 获取目标用户
    target_user = user_service.get_user_by_id(user_id)
    if not target_user:
        raise BizError(code=ErrorCode.USER_NOT_FOUND, msg="用户不存在")
    
    # 更新角色
    ok = user_service.update_user_role(target_user['openid'], data.role)
    
    if not ok:
        raise BizError(code=ErrorCode.PARAM_ERROR, msg="更新失败")
    
    return success(msg="更新成功")
