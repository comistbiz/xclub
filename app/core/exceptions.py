# coding: utf-8
"""异常处理"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.response import ErrorCode


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


class BizError(Exception):
    """业务错误"""
    def __init__(self, code: int, msg: str):
        self.code = code
        self.msg = msg
        super().__init__(msg)


def setup_exception_handlers(app: FastAPI):
    """注册全局异常处理器"""

    @app.exception_handler(BizError)
    async def biz_error_handler(request: Request, exc: BizError):
        """业务错误处理"""
        return JSONResponse(
            status_code=200,
            content={
                "code": exc.code,
                "msg": exc.msg,
                "data": None
            }
        )

    @app.exception_handler(WechatAPIError)
    async def wechat_error_handler(request: Request, exc: WechatAPIError):
        return JSONResponse(
            status_code=200,
            content={
                "code": ErrorCode.WECHAT_API_ERROR,
                "msg": f"微信API错误: {exc.errmsg}",
                "data": None
            }
        )

    @app.exception_handler(FeishuAPIError)
    async def feishu_error_handler(request: Request, exc: FeishuAPIError):
        return JSONResponse(
            status_code=200,
            content={
                "code": ErrorCode.FEISHU_API_ERROR,
                "msg": f"飞书API错误: {exc.msg}",
                "data": None
            }
        )

    @app.exception_handler(SessionError)
    async def session_error_handler(request: Request, exc: SessionError):
        return JSONResponse(
            status_code=200,
            content={
                "code": ErrorCode.SESSION_INVALID,
                "msg": exc.message,
                "data": None
            }
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """HTTP 异常处理"""
        # 映射 HTTP 状态码到业务错误码
        code_map = {
            400: ErrorCode.PARAM_ERROR,
            401: ErrorCode.UNAUTHORIZED,
            403: ErrorCode.FORBIDDEN,
            404: ErrorCode.USER_NOT_FOUND,
        }
        error_code = code_map.get(exc.status_code, ErrorCode.INTERNAL_ERROR)
        return JSONResponse(
            status_code=200,
            content={
                "code": error_code,
                "msg": exc.detail if isinstance(exc.detail, str) else str(exc.detail),
                "data": None
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        """参数验证错误处理"""
        errors = exc.errors()
        msg = errors[0].get('msg', '参数错误') if errors else '参数错误'
        return JSONResponse(
            status_code=200,
            content={
                "code": ErrorCode.PARAM_ERROR,
                "msg": f"参数错误: {msg}",
                "data": None
            }
        )

    @app.exception_handler(Exception)
    async def general_error_handler(request: Request, exc: Exception):
        import logging
        logging.getLogger(__name__).exception("未处理的异常")
        return JSONResponse(
            status_code=200,
            content={
                "code": ErrorCode.INTERNAL_ERROR,
                "msg": "服务器内部错误",
                "data": None
            }
        )
