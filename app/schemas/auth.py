# coding: utf-8
"""认证相关 Schema"""

from pydantic import BaseModel
from typing import Optional


class WechatLoginRequest(BaseModel):
    """微信登录请求"""
    code: str                        # wx.login() 获取的 code
    nickname: Optional[str] = None   # 用户昵称
    avatar_url: Optional[str] = None # 头像 URL


class LoginResponse(BaseModel):
    """登录响应"""
    session_id: str                  # 自定义登录态标识
    openid: str                      # 用户 openid
    is_new_user: bool = False        # 是否新用户


class SessionCheckResponse(BaseModel):
    """登录状态检查响应"""
    valid: bool                      # 是否有效
    openid: Optional[str] = None
    nickname: Optional[str] = None


class LogoutResponse(BaseModel):
    """退出登录响应"""
    message: str = "success"
