# coding: utf-8
"""统一响应格式"""

from typing import Any, Generic, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar('T')


class APIResponse(BaseModel, Generic[T]):
    """统一 API 响应格式"""
    code: int = 0
    msg: str = ""
    data: Optional[T] = None


def success(data: Any = None, msg: str = "") -> dict:
    """成功响应"""
    return {
        "code": 0,
        "msg": msg,
        "data": data
    }


def error(code: int, msg: str, data: Any = None) -> dict:
    """错误响应"""
    return {
        "code": code,
        "msg": msg,
        "data": data
    }


# 错误码定义
class ErrorCode:
    """错误码常量"""
    SUCCESS = 0
    
    # 通用错误 1xxx
    PARAM_ERROR = 1001          # 参数错误
    INTERNAL_ERROR = 1002       # 服务器内部错误
    
    # 认证错误 2xxx
    SESSION_INVALID = 2001      # Session 无效
    SESSION_EXPIRED = 2002      # Session 已过期
    UNAUTHORIZED = 2003         # 未登录
    FORBIDDEN = 2004            # 权限不足
    
    # 用户错误 3xxx
    USER_NOT_FOUND = 3001       # 用户不存在
    USER_ALREADY_REGISTERED = 3002  # 用户已注册
    
    # 激活码错误 4xxx
    ACTIVATION_CODE_NOT_FOUND = 4001    # 激活码不存在
    ACTIVATION_CODE_USED = 4002         # 激活码已使用
    ACTIVATION_CODE_INVALID = 4003      # 激活码已作废
    
    # 微信错误 5xxx
    WECHAT_API_ERROR = 5001     # 微信 API 错误
    
    # 飞书错误 6xxx
    FEISHU_API_ERROR = 6001     # 飞书 API 错误
