# coding: utf-8
"""激活码服务

数据库表结构:
CREATE TABLE `club_activation_code` (
    `id` bigint NOT NULL AUTO_INCREMENT,
    `code` varchar(32) NOT NULL COMMENT '激活码',
    `user_id` bigint DEFAULT NULL COMMENT '使用者用户ID',
    `used_at` datetime DEFAULT NULL COMMENT '使用时间',
    `state` smallint NOT NULL DEFAULT '1' COMMENT '状态 1.未使用 2.已使用 3.已作废',
    `remark` varchar(200) NOT NULL DEFAULT '' COMMENT '备注',
    `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_code` (`code`),
    KEY `idx_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='激活码表';
"""

import logging
import secrets
import string
from datetime import datetime
from typing import Optional, Dict, Any
from enum import IntEnum

from app.db import get_connection

log = logging.getLogger(__name__)


class ActivationCodeState(IntEnum):
    """激活码状态"""
    UNUSED = 1      # 未使用
    USED = 2        # 已使用
    INVALID = 3     # 已作废


class ActivationCodeService:
    """激活码服务"""

    TABLE = 'club_activation_code'
    DB_NAME = 'xclub'

    def generate_code(self, length: int = 12) -> str:
        """生成随机激活码
        
        Args:
            length: 激活码长度，默认12位
            
        Returns:
            激活码字符串 (大写字母+数字)
        """
        alphabet = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    def create_activation_code(self, remark: str = "") -> str:
        """创建激活码
        
        Args:
            remark: 备注信息
            
        Returns:
            新创建的激活码
        """
        code = self.generate_code()
        
        data = {
            'code': code,
            'state': ActivationCodeState.UNUSED,
            'remark': remark,
        }

        with get_connection(self.DB_NAME) as db:
            db.insert(self.TABLE, data)

        log.info(f"创建激活码: code={code}, remark={remark}")
        return code

    def batch_create_codes(self, count: int, remark: str = "") -> list:
        """批量创建激活码
        
        Args:
            count: 创建数量
            remark: 备注信息
            
        Returns:
            激活码列表
        """
        codes = []
        for _ in range(count):
            code = self.create_activation_code(remark)
            codes.append(code)
        return codes

    def get_code_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """通过激活码获取信息
        
        Args:
            code: 激活码
            
        Returns:
            激活码信息字典，不存在返回 None
        """
        with get_connection(self.DB_NAME) as db:
            result = db.select_one(self.TABLE, where={'code': code})
        
        if result:
            if result.get('used_at'):
                result['used_at'] = str(result['used_at'])
            if result.get('create_time'):
                result['create_time'] = str(result['create_time'])
        
        return result

    def validate_code(self, code: str) -> tuple[bool, str]:
        """验证激活码是否可用
        
        Args:
            code: 激活码
            
        Returns:
            (是否可用, 错误信息)
        """
        code_info = self.get_code_by_code(code)
        
        if not code_info:
            return False, "激活码不存在"
        
        if code_info['state'] == ActivationCodeState.USED:
            return False, "激活码已被使用"
        
        if code_info['state'] == ActivationCodeState.INVALID:
            return False, "激活码已作废"
        
        return True, ""

    def use_code(self, code: str, user_id: int) -> bool:
        """使用激活码
        
        Args:
            code: 激活码
            user_id: 使用者用户ID
            
        Returns:
            是否成功
        """
        with get_connection(self.DB_NAME) as db:
            affected = db.update(
                self.TABLE,
                values={
                    'user_id': user_id,
                    'used_at': datetime.now(),
                    'state': ActivationCodeState.USED,
                },
                where={
                    'code': code,
                    'state': ActivationCodeState.UNUSED,
                }
            )

        if affected:
            log.info(f"激活码使用成功: code={code}, user_id={user_id}")
        else:
            log.warning(f"激活码使用失败: code={code}, user_id={user_id}")
        
        return affected > 0

    def invalidate_code(self, code: str) -> bool:
        """作废激活码
        
        Args:
            code: 激活码
            
        Returns:
            是否成功
        """
        with get_connection(self.DB_NAME) as db:
            affected = db.update(
                self.TABLE,
                values={'state': ActivationCodeState.INVALID},
                where={
                    'code': code,
                    'state': ActivationCodeState.UNUSED,
                }
            )

        if affected:
            log.info(f"激活码已作废: code={code}")
        return affected > 0

    def get_user_activation_code(self, user_id: int) -> Optional[Dict[str, Any]]:
        """获取用户使用的激活码
        
        Args:
            user_id: 用户ID
            
        Returns:
            激活码信息，不存在返回 None
        """
        with get_connection(self.DB_NAME) as db:
            result = db.select_one(self.TABLE, where={'user_id': user_id})
        
        if result:
            if result.get('used_at'):
                result['used_at'] = str(result['used_at'])
            if result.get('create_time'):
                result['create_time'] = str(result['create_time'])
        
        return result


# 全局单例
activation_code_service = ActivationCodeService()
