# XClub

俱乐部小程序后端 - 支持微信登录和飞书多维表格打卡

## 功能

- **微信登录**: 通过微信小程序 code 换取用户信息，维护服务端 session
- **用户管理**: 用户信息管理，支持角色权限控制
- **飞书打卡**: 将打卡记录保存到飞书多维表格

## 技术栈

- **Web 框架**: FastAPI
- **HTTP 客户端**: httpx (异步)
- **数据验证**: Pydantic
- **数据库**: MySQL + 自定义 dbpool 连接池
- **运行时**: Python 3.8+

## 项目结构

```
xclub/
├── app/
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 配置管理
│   ├── dependencies.py      # 依赖注入
│   ├── core/
│   │   ├── exceptions.py    # 异常处理
│   │   └── security.py      # 安全工具
│   ├── db/
│   │   ├── dbpool.py        # 数据库连接池
│   │   └── pager.py         # 分页工具
│   ├── routers/
│   │   ├── auth.py          # 认证路由
│   │   ├── user.py          # 用户路由
│   │   └── record.py        # 打卡记录路由
│   ├── schemas/
│   │   ├── auth.py          # 认证 Schema
│   │   ├── user.py          # 用户 Schema
│   │   └── record.py        # 打卡记录 Schema
│   └── services/
│       ├── session.py       # Session 服务
│       ├── user.py          # 用户服务
│       ├── wechat.py        # 微信 API 服务
│       └── feishu.py        # 飞书 API 服务
├── docs/
│   ├── init.sql             # 数据库初始化脚本
│   └── REFACTOR.md          # 重构文档
├── .env                     # 环境变量 (需自行创建)
├── requirements.txt
└── README.md
```

## 安装

```bash
# 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt
```

## 配置

### 1. 初始化数据库

```bash
mysql -u root -p < docs/init.sql
```

### 2. 创建 `.env` 文件

```env
# 微信小程序
WECHAT_APPID=wxxxxxxxxxxx
WECHAT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 飞书应用凭证
FEISHU_APP_ID=cli_xxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxx

# 飞书多维表格配置
FEISHU_APP_TOKEN=UIRWbcMQoaDj2tsOoEycr2htnzg
FEISHU_TABLE_ID=tblSaLg0GWrGxLAc

# 数据库配置
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=xclub
DB_CHARSET=utf8mb4
DB_POOL_SIZE=10
```

## 运行

```bash
# 开发环境
uvicorn app.main:app --reload --host 0.0.0.0 --port 9900

# 生产环境
uvicorn app.main:app --host 0.0.0.0 --port 9900 --workers 4
```

## API 文档

启动服务后访问:

- Swagger UI: http://localhost:9900/docs
- ReDoc: http://localhost:9900/redoc

## API 接口

### 认证模块

| 方法 | 路径 | 说明 | 需要登录 |
|------|------|------|---------|
| POST | `/xclub/v1/auth/login` | 微信登录 | 否 |
| GET | `/xclub/v1/auth/check` | 检查登录状态 | 是 |
| POST | `/xclub/v1/auth/logout` | 退出登录 | 是 |

### 用户模块

| 方法 | 路径 | 说明 | 需要登录 |
|------|------|------|---------|
| GET | `/xclub/v1/user/info` | 获取当前用户信息 | 是 |
| GET | `/xclub/v1/user/{user_id}` | 获取指定用户信息 | 是 |
| PUT | `/xclub/v1/user/info` | 更新当前用户信息 | 是 |
| PUT | `/xclub/v1/user/{user_id}/role` | 更新用户角色 (管理员) | 是 |

### 打卡记录模块

| 方法 | 路径 | 说明 | 需要登录 |
|------|------|------|---------|
| POST | `/xclub/v1/record/create` | 创建打卡记录 | 是 |

## 请求示例

### 登录

```bash
curl -X POST http://localhost:9900/xclub/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"code": "wx_login_code", "nickname": "张三"}'
```

响应:
```json
{
  "session_id": "abc123...",
  "openid": "oXxx...",
  "is_new_user": true
}
```

### 获取当前用户信息

```bash
curl -X GET http://localhost:9900/xclub/v1/user/info \
  -H "X-Session-Id: abc123..."
```

响应:
```json
{
  "id": 1,
  "openid": "oXxx...",
  "nickname": "张三",
  "avatar": "https://...",
  "realname": "",
  "phone_num": "",
  "sex": 1,
  "role": 1,
  "role_name": "游客",
  "state": 1,
  "birthday": null,
  "address": "",
  "email": "",
  "create_time": "2026-01-18 12:00:00"
}
```

### 更新用户信息

```bash
curl -X PUT http://localhost:9900/xclub/v1/user/info \
  -H "Content-Type: application/json" \
  -H "X-Session-Id: abc123..." \
  -d '{"nickname": "新昵称", "phone_num": "13800138000"}'
```

响应:
```json
{
  "id": 1,
  "openid": "oXxx...",
  "nickname": "新昵称",
  "phone_num": "13800138000",
  ...
}
```

### 创建打卡记录

```bash
curl -X POST http://localhost:9900/xclub/v1/record/create \
  -H "Content-Type: application/json" \
  -H "X-Session-Id: abc123..." \
  -d '{"meal_type": "午餐", "price": 15, "location": "万科食堂"}'
```

响应:
```json
{
  "record_id": "recxxx",
  "message": "success"
}
```

## 用户角色

| 角色值 | 名称 | 说明 |
|-------|------|------|
| 1 | 游客 | 默认角色，基本权限 |
| 2 | 成员 | 俱乐部成员 |
| 3 | 管理员 | 可管理用户角色 |

## 用户状态

| 状态值 | 名称 | 说明 |
|-------|------|------|
| 1 | 正常 | 正常使用 |
| 2 | 封禁 | 账号被封禁 |
| 3 | 注销 | 账号已注销 |
