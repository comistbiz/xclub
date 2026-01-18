# coding: utf-8
"""微信 API 服务"""

import logging
import httpx
from typing import Optional

from app.config import settings
from app.core.exceptions import WechatAPIError

log = logging.getLogger(__name__)


class WechatService:
    """微信 API 服务"""
    
    CODE2SESSION_URL = "https://api.weixin.qq.com/sns/jscode2session"
    
    def __init__(self):
        self.appid = settings.WECHAT_APPID
        self.secret = settings.WECHAT_SECRET
    
    async def code2session(self, code: str) -> dict:
        """通过 code 换取 session_key 和 openid
        
        微信 API 文档:
        https://developers.weixin.qq.com/miniprogram/dev/OpenApiDoc/user-login/code2Session.html
        
        Args:
            code: wx.login() 获取的临时登录凭证
            
        Returns:
            {
                "openid": "用户唯一标识",
                "session_key": "会话密钥",
                "unionid": "用户在开放平台的唯一标识符 (可能没有)"
            }
            
        Raises:
            WechatAPIError: 微信 API 返回错误
        """
        params = {
            "appid": self.appid,
            "secret": self.secret,
            "js_code": code,
            "grant_type": "authorization_code"
        }
        
        log.debug(f"调用微信 code2session: code={code[:10]}...")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(self.CODE2SESSION_URL, params=params)
            result = response.json()
        
        log.debug(f"微信 code2session 响应: {result}")
        
        # 检查错误
        if "errcode" in result and result["errcode"] != 0:
            raise WechatAPIError(
                errcode=result["errcode"],
                errmsg=result.get("errmsg", "未知错误")
            )
        
        return {
            "openid": result["openid"],
            "session_key": result["session_key"],
            "unionid": result.get("unionid")
        }


# 全局单例
wechat_service = WechatService()
