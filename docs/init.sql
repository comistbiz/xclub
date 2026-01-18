-- XClub 数据库初始化脚本

-- 创建数据库
CREATE DATABASE IF NOT EXISTS `xclub` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE `xclub`;

-- 用户会话表
CREATE TABLE IF NOT EXISTS `user_session` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `session_id` varchar(64) NOT NULL COMMENT 'Session ID',
    `openid` varchar(64) NOT NULL COMMENT '微信 openid',
    `session_key` varchar(128) NOT NULL COMMENT '微信 session_key',
    `nickname` varchar(64) DEFAULT NULL COMMENT '用户昵称',
    `avatar_url` varchar(512) DEFAULT NULL COMMENT '头像 URL',
    `created_at` int(11) NOT NULL COMMENT '创建时间戳',
    `expire_at` int(11) NOT NULL COMMENT '过期时间戳',
    `ctime` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `utime` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_session_id` (`session_id`),
    KEY `idx_openid` (`openid`),
    KEY `idx_expire_at` (`expire_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户会话表';

-- 俱乐部用户表
CREATE TABLE IF NOT EXISTS `club_user` (
    `id` bigint NOT NULL AUTO_INCREMENT,
    `openid` varchar(64) NOT NULL COMMENT '微信 openid',
    `nickname` varchar(128) NOT NULL DEFAULT '' COMMENT '昵称',
    `avatar` varchar(500) NOT NULL DEFAULT '' COMMENT '头像',
    `realname` varchar(50) NOT NULL DEFAULT '' COMMENT '真实姓名',
    `phone_num` varchar(20) NOT NULL DEFAULT '' COMMENT '手机号码',
    `sex` smallint DEFAULT '3' COMMENT '性别 1.男性 2.女性 3.未知',
    `birthday` date DEFAULT NULL COMMENT '生日',
    `address` varchar(200) NOT NULL DEFAULT '' COMMENT '住址',
    `email` varchar(75) DEFAULT '' COMMENT '邮箱',
    `role` smallint DEFAULT '1' COMMENT '角色 1.游客 2.成员 3.管理员',
    `state` smallint DEFAULT '1' COMMENT '状态 1.正常 2.封禁 3.注销',
    `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_openid` (`openid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='俱乐部用户表';
