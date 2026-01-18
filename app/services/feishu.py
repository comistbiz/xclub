# coding: utf-8
"""飞书 API 服务"""

import time
import logging
import httpx
from typing import Optional

from app.config import settings
from app.core.exceptions import FeishuAPIError

log = logging.getLogger(__name__)


class FeishuService:
    """飞书 API 服务"""
    
    TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    RECORD_URL_TEMPLATE = "https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
    
    # Token 缓存 (类级别)
    _token: Optional[str] = None
    _token_expire_at: float = 0
    
    def __init__(self):
        self.app_id = settings.FEISHU_APP_ID
        self.app_secret = settings.FEISHU_APP_SECRET
        # 从配置文件读取多维表格配置
        self.app_token = settings.FEISHU_APP_TOKEN
        self.table_id = settings.FEISHU_TABLE_ID
    
    @property
    def record_url(self) -> str:
        """获取创建记录的 URL"""
        return self.RECORD_URL_TEMPLATE.format(
            app_token=self.app_token,
            table_id=self.table_id
        )
    
    async def get_access_token(self) -> str:
        """获取 tenant_access_token
        
        - 检查缓存是否有效 (提前 5 分钟刷新)
        - 无效则调用 API 获取新 token
        - 缓存 token 和过期时间
        
        Returns:
            tenant_access_token
            
        Raises:
            FeishuAPIError: 飞书 API 返回错误
        """
        # 检查缓存是否有效 (提前 5 分钟刷新)
        if self._token and time.time() < self._token_expire_at - 300:
            log.debug("使用缓存的飞书 token")
            return self._token
        
        log.info("获取新的飞书 access_token")
        
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(self.TOKEN_URL, json=payload)
            result = response.json()
        
        # 检查错误
        if result.get("code") != 0:
            raise FeishuAPIError(
                code=result.get("code", -1),
                msg=result.get("msg", "获取 token 失败")
            )
        
        # 缓存 token
        FeishuService._token = result["tenant_access_token"]
        FeishuService._token_expire_at = time.time() + result.get("expire", 7200)
        
        log.info(f"飞书 token 获取成功，有效期 {result.get('expire', 7200)} 秒")
        
        return self._token
    
    async def create_record(
        self,
        nickname: str,
        meal_type: str,
        price: float,
        location: str,
        date: Optional[int] = None
    ) -> str:
        """创建打卡记录
        
        Args:
            nickname: 微信昵称
            meal_type: 时间段 (早餐/午餐/晚餐)
            price: 价格
            location: 地点
            date: 日期时间戳 (毫秒)，默认当前时间
            
        Returns:
            record_id
            
        Raises:
            FeishuAPIError: 飞书 API 返回错误
        """
        # 获取 access_token
        token = await self.get_access_token()
        
        # 默认使用当前时间
        if date is None:
            date = int(time.time() * 1000)
        
        # 构建请求体
        payload = {
            "fields": {
                "微信昵称": nickname,
                "时间段": meal_type,
                "价格": price,
                "地点": location,
                "日期": date
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        log.info(f"创建飞书记录: nickname={nickname}, meal_type={meal_type}, price={price}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.record_url,
                json=payload,
                headers=headers
            )
            result = response.json()
        
        log.debug(f"飞书创建记录响应: {result}")
        
        # 检查错误
        if result.get("code") != 0:
            raise FeishuAPIError(
                code=result.get("code", -1),
                msg=result.get("msg", "创建记录失败")
            )
        
        record_id = result["data"]["record"]["record_id"]
        log.info(f"飞书记录创建成功: record_id={record_id}")
        
        return record_id


# 全局单例
feishu_service = FeishuService()
