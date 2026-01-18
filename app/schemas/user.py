# coding: utf-8
"""用户相关 Schema"""

from pydantic import BaseModel
from typing import Optional
from enum import IntEnum


class UserRole(IntEnum):
    """用户角色"""
    VISITOR = 1     # 游客
    MEMBER = 2      # 成员
    ADMIN = 3       # 管理员


class UserState(IntEnum):
    """用户状态"""
    NORMAL = 1      # 正常
    BANNED = 2      # 封禁
    DELETED = 3     # 注销


class UserSex(IntEnum):
    """用户性别"""
    MALE = 1        # 男性
    FEMALE = 2      # 女性
    UNKNOWN = 3     # 未知


# 角色名称映射
ROLE_NAME_MAP = {
    UserRole.VISITOR: '游客',
    UserRole.MEMBER: '成员',
    UserRole.ADMIN: '管理员',
}


class UserInfo(BaseModel):
    """用户信息响应"""
    id: int
    openid: Optional[str] = None
    nickname: str = ""
    avatar: str = ""
    realname: str = ""
    phone_num: str = ""
    sex: int = 1
    role: int = 1
    role_name: str = "游客"
    state: int = 1
    birthday: Optional[str] = None
    address: str = ""
    email: str = ""
    create_time: Optional[str] = None

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """更新用户信息请求"""
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    realname: Optional[str] = None
    phone_num: Optional[str] = None
    sex: Optional[int] = None
    birthday: Optional[str] = None
    address: Optional[str] = None
    email: Optional[str] = None


class UserRoleUpdate(BaseModel):
    """更新用户角色请求 (仅管理员)"""
    role: int
