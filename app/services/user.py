# coding: utf-8
"""用户服务"""

import logging
from typing import Optional, Dict, Any

from app.db import get_connection
from app.schemas.user import ROLE_NAME_MAP, UserRole

log = logging.getLogger(__name__)


class UserService:
    """用户服务
    
    数据库表结构:
    CREATE TABLE `club_user` (
        `id` bigint NOT NULL AUTO_INCREMENT,
        `openid` varchar(64) NOT NULL COMMENT '微信 openid',
        `nickname` varchar(128) NOT NULL DEFAULT '' COMMENT '昵称',
        `avatar` varchar(500) NOT NULL DEFAULT '' COMMENT '头像',
        `realname` varchar(50) NOT NULL DEFAULT '' COMMENT '真实姓名',
        `phone_num` varchar(20) NOT NULL DEFAULT '' COMMENT '手机号码',
        `sex` smallint DEFAULT '1' COMMENT '性别 1.男性 2.女性 3.未知',
        `birthday` date DEFAULT NULL COMMENT '生日',
        `address` varchar(200) NOT NULL DEFAULT '' COMMENT '住址',
        `email` varchar(75) DEFAULT '' COMMENT '邮箱',
        `role` smallint DEFAULT '1' COMMENT '角色 1.游客 2.成员 3.管理员',
        `state` smallint DEFAULT '1' COMMENT '状态 1.正常 2.封禁 3.注销',
        `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
        `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (`id`),
        UNIQUE KEY `uk_openid` (`openid`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='俱乐部用户表';
    """

    TABLE = 'club_user'
    DB_NAME = 'xclub'

    def get_user_by_openid(self, openid: str) -> Optional[Dict[str, Any]]:
        """通过 openid 获取用户信息
        
        Args:
            openid: 微信 openid
            
        Returns:
            用户信息字典，不存在返回 None
        """
        with get_connection(self.DB_NAME) as db:
            user = db.select_one(self.TABLE, where={'openid': openid})

        if user:
            user['role_name'] = ROLE_NAME_MAP.get(user.get('role', 1), '游客')
            # 格式化日期时间
            if user.get('birthday'):
                user['birthday'] = str(user['birthday'])
            if user.get('create_time'):
                user['create_time'] = str(user['create_time'])

        return user

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """通过 ID 获取用户信息
        
        Args:
            user_id: 用户 ID
            
        Returns:
            用户信息字典，不存在返回 None
        """
        with get_connection(self.DB_NAME) as db:
            user = db.select_one(self.TABLE, where={'id': user_id})

        if user:
            user['role_name'] = ROLE_NAME_MAP.get(user.get('role', 1), '游客')
            if user.get('birthday'):
                user['birthday'] = str(user['birthday'])
            if user.get('create_time'):
                user['create_time'] = str(user['create_time'])

        return user

    def create_user(
        self,
        openid: str,
        nickname: str = "",
        avatar: str = "",
        role: int = None,
        **kwargs
    ) -> int:
        """创建用户
        
        Args:
            openid: 微信 openid
            nickname: 昵称
            avatar: 头像
            role: 角色，默认为游客
            **kwargs: 其他字段
            
        Returns:
            用户 ID
        """
        data = {
            'openid': openid,
            'nickname': nickname or '',
            'avatar': avatar or '',
            'role': role if role is not None else UserRole.VISITOR,
            'state': 1,
        }
        
        # 添加其他可选字段
        optional_fields = ['realname', 'phone_num', 'sex', 'birthday', 'address', 'email']
        for field in optional_fields:
            if field in kwargs and kwargs[field] is not None:
                data[field] = kwargs[field]

        with get_connection(self.DB_NAME) as db:
            db.insert(self.TABLE, data)
            user_id = db.last_insert_id()

        log.info(f"创建用户: openid={openid}, user_id={user_id}")
        return user_id

    def register_user(
        self,
        openid: str,
        activation_code: str,
        realname: str = "",
        nickname: str = "",
        avatar: str = "",
    ) -> tuple[int, str]:
        """注册用户（使用激活码）
        
        Args:
            openid: 微信 openid
            activation_code: 激活码
            realname: 真实姓名
            nickname: 昵称
            avatar: 头像
            
        Returns:
            (用户ID, 错误信息)，成功时错误信息为空
        """
        from app.services.activation_code import activation_code_service
        
        # 检查用户是否已存在
        existing_user = self.get_user_by_openid(openid)
        if existing_user:
            # 如果用户已经是成员或管理员，不需要再注册
            if existing_user.get('role', 1) >= UserRole.MEMBER:
                return existing_user['id'], "用户已注册"
        
        # 验证激活码
        is_valid, error_msg = activation_code_service.validate_code(activation_code)
        if not is_valid:
            return 0, error_msg
        
        if existing_user:
            # 用户存在但是游客，升级为成员
            user_id = existing_user['id']
            update_data = {'role': UserRole.MEMBER}
            if realname:
                update_data['realname'] = realname
            if nickname:
                update_data['nickname'] = nickname
            if avatar:
                update_data['avatar'] = avatar
            
            with get_connection(self.DB_NAME) as db:
                db.update(self.TABLE, values=update_data, where={'id': user_id})
        else:
            # 创建新用户，直接设置为成员
            user_id = self.create_user(
                openid=openid,
                nickname=nickname,
                avatar=avatar,
                role=UserRole.MEMBER,
                realname=realname,
            )
        
        # 使用激活码
        activation_code_service.use_code(activation_code, user_id)
        
        log.info(f"用户注册成功: openid={openid}, user_id={user_id}, activation_code={activation_code}")
        return user_id, ""

    def get_or_create_user(self, openid: str, nickname: str = "", avatar: str = "") -> Dict[str, Any]:
        """获取或创建用户
        
        Args:
            openid: 微信 openid
            nickname: 昵称
            avatar: 头像
            
        Returns:
            (用户信息, 是否新用户)
        """
        user = self.get_user_by_openid(openid)
        
        if user:
            # 如果有新的昵称或头像，更新
            update_data = {}
            if nickname and nickname != user.get('nickname'):
                update_data['nickname'] = nickname
            if avatar and avatar != user.get('avatar'):
                update_data['avatar'] = avatar
            
            if update_data:
                self.update_user(openid, **update_data)
                user.update(update_data)
            
            return user, False
        
        # 创建新用户
        user_id = self.create_user(openid, nickname, avatar)
        user = self.get_user_by_id(user_id)
        return user, True

    def update_user(self, openid: str, **kwargs) -> bool:
        """更新用户信息
        
        Args:
            openid: 微信 openid
            **kwargs: 要更新的字段
            
        Returns:
            是否更新成功
        """
        # 只允许更新特定字段
        allowed_fields = {
            'nickname', 'avatar', 'realname', 'phone_num',
            'sex', 'birthday', 'address', 'email'
        }
        update_data = {k: v for k, v in kwargs.items() if k in allowed_fields and v is not None}

        if not update_data:
            return False

        with get_connection(self.DB_NAME) as db:
            affected = db.update(
                self.TABLE,
                values=update_data,
                where={'openid': openid}
            )

        if affected:
            log.info(f"更新用户信息: openid={openid}, data={update_data}")
        return affected > 0

    def update_user_role(self, openid: str, role: int) -> bool:
        """更新用户角色
        
        Args:
            openid: 微信 openid
            role: 角色值 (1=游客, 2=成员, 3=管理员)
            
        Returns:
            是否更新成功
        """
        if role not in [1, 2, 3]:
            return False

        with get_connection(self.DB_NAME) as db:
            affected = db.update(
                self.TABLE,
                values={'role': role},
                where={'openid': openid}
            )

        if affected:
            log.info(f"更新用户角色: openid={openid}, role={role}")
        return affected > 0

    def is_admin(self, openid: str) -> bool:
        """检查用户是否为管理员
        
        Args:
            openid: 微信 openid
            
        Returns:
            是否为管理员
        """
        user = self.get_user_by_openid(openid)
        return user is not None and user.get('role') == UserRole.ADMIN


# 全局单例
user_service = UserService()
