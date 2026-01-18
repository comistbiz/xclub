# coding: utf-8
"""异常处理"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class WechatAPIError(Exception):
    """微信 API 错误"""
    def __init__(self, errcode: int, errmsg: str):
        self.errcode = errcode
        self.errmsg = errmsg
        super().__init__(f"微信API错误: {errcode} - {errmsg}")


class FeishuAPIError(Exception):
    """飞书 API 错误"""
    def __init__(self, code: int, msg: str):
        self.code = code
        self.msg = msg
        super().__init__(f"飞书API错误: {code} - {msg}")


class SessionError(Exception):
    """Session 错误"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def setup_exception_handlers(app: FastAPI):
    """注册全局异常处理器"""

    @app.exception_handler(WechatAPIError)
    async def wechat_error_handler(request: Request, exc: WechatAPIError):
        return JSONResponse(
            status_code=400,
            content={
                "code": f"WECHAT_{exc.errcode}",
                "message": exc.errmsg
            }
        )

    @app.exception_handler(FeishuAPIError)
    async def feishu_error_handler(request: Request, exc: FeishuAPIError):
        return JSONResponse(
            status_code=500,
            content={
                "code": f"FEISHU_{exc.code}",
                "message": exc.msg
            }
        )

    @app.exception_handler(SessionError)
    async def session_error_handler(request: Request, exc: SessionError):
        return JSONResponse(
            status_code=401,
            content={
                "code": "SESSION_ERROR",
                "message": exc.message
            }
        )

    @app.exception_handler(Exception)
    async def general_error_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "code": "INTERNAL_ERROR",
                "message": "服务器内部错误"
            }
        )
