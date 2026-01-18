# coding: utf-8
"""打卡记录相关 Schema"""

from pydantic import BaseModel
from typing import Optional
from enum import Enum


class MealType(str, Enum):
    """餐次类型"""
    BREAKFAST = "早餐"
    LUNCH = "午餐"
    DINNER = "晚餐"


class CreateRecordRequest(BaseModel):
    """创建打卡记录请求"""
    meal_type: MealType              # 时间段: 早餐/午餐/晚餐
    price: float                     # 价格
    location: str                    # 地点
    date: Optional[int] = None       # 日期时间戳(毫秒)，默认当前时间


class CreateRecordResponse(BaseModel):
    """创建打卡记录响应"""
    record_id: str                   # 飞书记录 ID
    message: str = "success"
