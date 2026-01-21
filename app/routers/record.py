# coding: utf-8
"""打卡记录路由"""

import logging
from fastapi import APIRouter, Depends

from app.schemas.record import CreateRecordRequest
from app.services.feishu import feishu_service
from app.services.session import SessionData
from app.dependencies import require_login
from app.core.response import success

log = logging.getLogger(__name__)

router = APIRouter(prefix="/xclub/v1/record", tags=["打卡记录"])


@router.post("/create")
async def create_record(
    request: CreateRecordRequest,
    session: SessionData = Depends(require_login)
):
    """创建打卡记录
    
    需要在 Header 中传入 X-Session-Id
    
    记录会保存到飞书多维表格中
    """
    # 获取用户昵称，如果没有则使用 openid 前 8 位
    nickname = session.nickname or f"用户{session.openid[:8]}"
    
    # 调用飞书 API 创建记录
    record_id = await feishu_service.create_record(
        nickname=nickname,
        meal_type=request.meal_type.value,
        price=request.price,
        location=request.location,
        date=request.date
    )
    
    log.info(f"打卡记录创建成功: openid={session.openid}, record_id={record_id}")
    
    return success(data={"record_id": record_id}, msg="打卡成功")
