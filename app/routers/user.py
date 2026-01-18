# coding: utf-8
"""用户路由"""

import logging
from fastapi import APIRouter, Depends, HTTPException

from app.schemas.user import UserInfo, UserUpdate, UserRoleUpdate
from app.services.user import user_service
from app.services.session import SessionData
from app.dependencies import require_login

log = logging.getLogger(__name__)

router = APIRouter(prefix="/xclub/v1/user", tags=["用户"])


@router.get("/info", response_model=UserInfo)
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
    
    return UserInfo(**user)


@router.get("/{user_id}", response_model=UserInfo)
async def get_user_info(
    user_id: int,
    session: SessionData = Depends(require_login)
):
    """获取指定用户信息
    
    需要在 Header 中传入 X-Session-Id
    """
    user = user_service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return UserInfo(**user)


@router.put("/info", response_model=UserInfo)
async def update_current_user_info(
    data: UserUpdate,
    session: SessionData = Depends(require_login)
):
    """更新当前登录用户信息
    
    需要在 Header 中传入 X-Session-Id
    """
    update_data = data.model_dump(exclude_none=True)
    
    if not update_data:
        raise HTTPException(status_code=400, detail="没有要更新的数据")
    
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
    return UserInfo(**updated_user)


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
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    # 获取目标用户
    target_user = user_service.get_user_by_id(user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 更新角色
    success = user_service.update_user_role(target_user['openid'], data.role)
    
    if not success:
        raise HTTPException(status_code=400, detail="更新失败")
    
    return {"message": "success"}
