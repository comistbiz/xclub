# coding: utf-8
"""安全相关工具"""

import secrets


def generate_session_id() -> str:
    """生成安全的 session_id
    
    使用 secrets.token_urlsafe 生成 256 位随机 token
    """
    return secrets.token_urlsafe(32)
