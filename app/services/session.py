# coding: utf-8
"""Session 管理服务 - MySQL 存储"""

import time
import logging
from dataclasses import dataclass
from typing import Optional

from app.config import settings
from app.core.security import generate_session_id
from app.db import get_connection

log = logging.getLogger(__name__)


@dataclass
class SessionData:
    """Session 数据结构"""
    session_id: str
    openid: str
    session_key: str
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: int = 0
    expire_at: int = 0

    def is_expired(self) -> bool:
        """检查是否过期"""
        return int(time.time()) > self.expire_at


class SessionService:
    """Session 管理服务 (MySQL 存储)
    
    数据库表结构:
    CREATE TABLE `user_session` (
        `id` int(11) NOT NULL AUTO_INCREMENT,
        `session_id` varchar(64) NOT NULL COMMENT 'Session ID',
        `openid` varchar(64) NOT NULL COMMENT '微信 openid',
        `session_key` varchar(128) NOT NULL COMMENT '微信 session_key',
        `nickname` varchar(64) DEFAULT NULL COMMENT '用户昵称',
        `avatar_url` varchar(512) DEFAULT NULL COMMENT '头像 URL',
        `created_at` int(11) NOT NULL COMMENT '创建时间戳',
        `expire_at` int(11) NOT NULL COMMENT '过期时间戳',
        `ctime` datetime DEFAULT CURRENT_TIMESTAMP,
        `utime` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (`id`),
        UNIQUE KEY `uk_session_id` (`session_id`),
        KEY `idx_openid` (`openid`),
        KEY `idx_expire_at` (`expire_at`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户会话表';
    """

    TABLE = 'user_session'
    DB_NAME = 'xclub'

    def create_session(
        self,
        openid: str,
        session_key: str,
        nickname: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> str:
        """创建 session
        
        Args:
            openid: 微信用户 openid
            session_key: 微信 session_key
            nickname: 用户昵称
            avatar_url: 用户头像
            
        Returns:
            session_id
        """
        # 删除该用户的旧 session
        with get_connection(self.DB_NAME) as db:
            db.delete(self.TABLE, where={'openid': openid})

        # 生成新的 session_id
        session_id = generate_session_id()
        now = int(time.time())
        expire_at = now + settings.SESSION_EXPIRE_SECONDS

        # 插入新 session
        with get_connection(self.DB_NAME) as db:
            db.insert(self.TABLE, {
                'session_id': session_id,
                'openid': openid,
                'session_key': session_key,
                'nickname': nickname,
                'avatar_url': avatar_url,
                'created_at': now,
                'expire_at': expire_at,
            })

        log.info(f"创建 session: openid={openid}, expire_at={expire_at}")
        return session_id

    def get_session(self, session_id: str) -> Optional[SessionData]:
        """获取 session 数据
        
        Args:
            session_id: session 标识
            
        Returns:
            SessionData 或 None (不存在或已过期)
        """
        with get_connection(self.DB_NAME) as db:
            row = db.select_one(
                self.TABLE,
                where={'session_id': session_id},
                fields=['session_id', 'openid', 'session_key', 'nickname', 'avatar_url', 'created_at', 'expire_at']
            )

        if not row:
            return None

        # 检查是否过期
        if int(time.time()) > row['expire_at']:
            self.delete_session(session_id)
            log.debug(f"session 已过期: session_id={session_id[:8]}...")
            return None

        return SessionData(
            session_id=row['session_id'],
            openid=row['openid'],
            session_key=row['session_key'],
            nickname=row.get('nickname'),
            avatar_url=row.get('avatar_url'),
            created_at=row['created_at'],
            expire_at=row['expire_at']
        )

    def delete_session(self, session_id: str) -> bool:
        """删除 session
        
        Args:
            session_id: session 标识
            
        Returns:
            是否删除成功
        """
        with get_connection(self.DB_NAME) as db:
            affected = db.delete(self.TABLE, where={'session_id': session_id})

        if affected:
            log.info(f"删除 session: session_id={session_id[:8]}...")
            return True
        return False

    def delete_session_by_openid(self, openid: str) -> bool:
        """通过 openid 删除 session
        
        Args:
            openid: 用户 openid
            
        Returns:
            是否删除成功
        """
        with get_connection(self.DB_NAME) as db:
            affected = db.delete(self.TABLE, where={'openid': openid})

        if affected:
            log.info(f"删除 session: openid={openid}")
            return True
        return False

    def update_session(self, session_id: str, **kwargs) -> bool:
        """更新 session 数据
        
        Args:
            session_id: session 标识
            **kwargs: 要更新的字段 (nickname, avatar_url)
            
        Returns:
            是否更新成功
        """
        # 只允许更新特定字段
        allowed_fields = {'nickname', 'avatar_url'}
        update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not update_data:
            return False

        with get_connection(self.DB_NAME) as db:
            affected = db.update(
                self.TABLE,
                values=update_data,
                where={'session_id': session_id}
            )

        return affected > 0

    def cleanup_expired(self) -> int:
        """清理过期的 session
        
        Returns:
            清理的数量
        """
        now = int(time.time())
        with get_connection(self.DB_NAME) as db:
            affected = db.delete(
                self.TABLE,
                where={'expire_at': ('<', now)}
            )

        if affected:
            log.info(f"清理过期 session: {affected} 个")

        return affected

    def get_or_create_user(self, openid: str, session_key: str, **kwargs) -> tuple:
        """获取或创建用户 session
        
        Returns:
            (session_id, is_new_user)
        """
        # 检查是否有有效的 session
        with get_connection(self.DB_NAME) as db:
            row = db.select_one(
                self.TABLE,
                where={'openid': openid},
                fields=['session_id', 'expire_at']
            )

        is_new_user = row is None

        # 创建新 session
        session_id = self.create_session(
            openid=openid,
            session_key=session_key,
            **kwargs
        )

        return session_id, is_new_user


# 全局单例
session_service = SessionService()
