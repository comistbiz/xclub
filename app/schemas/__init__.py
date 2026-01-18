# coding: utf-8
"""Pydantic Schemas"""

from app.schemas.auth import (
    WechatLoginRequest,
    LoginResponse,
    SessionCheckResponse,
    LogoutResponse
)
from app.schemas.record import (
    MealType,
    CreateRecordRequest,
    CreateRecordResponse
)
