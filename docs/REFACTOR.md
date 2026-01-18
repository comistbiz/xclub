# XClub 重构方案文档

## 一、需求概述

重构 XClub 后端服务，实现以下核心功能：

1. **微信小程序登录** - 通过微信 code 换取用户信息，维护服务端 session
2. **飞书多维表格集成** - 调用飞书 API 创建打卡记录

---

## 二、功能模块

### 2.1 用户认证模块

| 功能 | 说明 |
|------|------|
| 微信登录 | 小程序传入 code，后端调用微信 API 换取 openid/session_key |
| Session 管理 | 生成自定义 session_id，存储用户登录状态 |
| 登录态验证 | 通过 session_id 验证用户身份 |

**微信登录流程**：

```
小程序                    后端服务                   微信服务器
  |                         |                          |
  |-- wx.login() 获取 code -->|                          |
  |                         |-- code2session 请求 ------>|
  |                         |<-- openid, session_key ---|
  |                         |                          |
  |                         |-- 生成 session_id        |
  |                         |-- 存储 session 数据      |
  |<-- 返回 session_id -----|                          |
```

### 2.2 飞书多维表格模块

| 功能 | 说明 |
|------|------|
| Token 管理 | 获取并缓存 tenant_access_token (有效期 2 小时) |
| 创建记录 | 向指定数据表新增打卡记录 |

**飞书 API 调用流程**：

```
后端服务                              飞书服务器
  |                                      |
  |-- 检查 token 缓存                    |
  |   (过期则重新获取)                   |
  |-- POST tenant_access_token/internal ->|
  |<-- tenant_access_token --------------|
  |                                      |
  |-- POST /records (带 token) --------->|
  |<-- record_id ------------------------|
```

---

## 三、项目结构

```
xclub/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 配置管理 (Pydantic Settings)
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── exceptions.py    # 自定义异常
│   │   └── security.py      # 安全相关 (session_id 生成)
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py          # 认证相关 Schema
│   │   └── record.py        # 打卡记录 Schema
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py          # 认证路由 (/xclub/v1/auth/*)
│   │   └── record.py        # 打卡记录路由 (/xclub/v1/record/*)
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── wechat.py        # 微信 API 服务
│   │   ├── feishu.py        # 飞书 API 服务 (使用配置的 app_token/table_id)
│   │   └── session.py       # Session 管理服务
│   │
│   └── dependencies.py      # FastAPI 依赖注入
│
├── .env                     # 环境变量 (不提交到 git)
├── .env.example             # 环境变量示例
├── requirements.txt
└── README.md
```

### API 路由结构

```
/xclub/v1/
├── auth/
│   ├── login      POST  微信登录
│   ├── check      GET   检查登录状态
│   └── logout     POST  退出登录
│
└── record/
    └── create     POST  创建打卡记录
```

---

## 四、配置设计

### 4.1 配置类

```python
# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 服务配置
    APP_NAME: str = "xclub"
    DEBUG: bool = True
    
    # 微信小程序配置
    WECHAT_APPID: str = ""
    WECHAT_SECRET: str = ""
    
    # 飞书配置
    FEISHU_APP_ID: str = ""
    FEISHU_APP_SECRET: str = ""
    
    # 飞书多维表格配置 (写在配置文件中)
    FEISHU_APP_TOKEN: str = ""      # 多维表格 App Token
    FEISHU_TABLE_ID: str = ""       # 数据表 ID
    
    # Session 配置
    SESSION_EXPIRE_SECONDS: int = 86400 * 7  # 7 天过期
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### 4.2 环境变量文件

```env
# .env.example

# 微信小程序
WECHAT_APPID=wxxxxxxxxxxx
WECHAT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 飞书应用凭证
FEISHU_APP_ID=cli_xxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxx

# 飞书多维表格配置
# app_token: 多维表格的唯一标识，从多维表格 URL 中获取
# 例如: https://xxx.feishu.cn/base/UIRWbcMQoaDj2tsOoEycr2htnzg 中的 UIRWbcMQoaDj2tsOoEycr2htnzg
FEISHU_APP_TOKEN=UIRWbcMQoaDj2tsOoEycr2htnzg

# table_id: 数据表 ID，创建数据表时返回或从 URL 中获取
FEISHU_TABLE_ID=tblSaLg0GWrGxLAc

# Session
SESSION_EXPIRE_SECONDS=604800
```

### 4.3 配置说明

| 配置项 | 说明 | 获取方式 |
|--------|------|---------|
| `FEISHU_APP_ID` | 飞书应用 ID | 飞书开放平台 - 应用凭证 |
| `FEISHU_APP_SECRET` | 飞书应用密钥 | 飞书开放平台 - 应用凭证 |
| `FEISHU_APP_TOKEN` | 多维表格 App Token | 多维表格 URL 中获取 |
| `FEISHU_TABLE_ID` | 数据表 ID | 创建数据表 API 返回 / URL 中获取 |

---

## 五、API 设计

### 5.1 API 路径规范

所有 API 遵循统一格式：`/xclub/v1/{module}/{action}`

- **前缀**: `/xclub/v1`
- **module**: 模块名 (auth, record)
- **action**: 操作名 (login, check, create)

### 5.2 认证接口

| 方法 | 路径 | 说明 | 需要登录 |
|------|------|------|---------|
| POST | `/xclub/v1/auth/login` | 微信登录 | 否 |
| GET | `/xclub/v1/auth/check` | 检查登录状态 | 是 |
| POST | `/xclub/v1/auth/logout` | 退出登录 | 是 |

### 5.3 打卡记录接口

| 方法 | 路径 | 说明 | 需要登录 |
|------|------|------|---------|
| POST | `/xclub/v1/record/create` | 创建打卡记录 | 是 |

---

## 六、Schema 设计

### 6.1 认证相关

```python
# app/schemas/auth.py
from pydantic import BaseModel
from typing import Optional

class WechatLoginRequest(BaseModel):
    """微信登录请求"""
    code: str                        # wx.login() 获取的 code
    nickname: Optional[str] = None   # 用户昵称
    avatar_url: Optional[str] = None # 头像 URL

class LoginResponse(BaseModel):
    """登录响应"""
    session_id: str                  # 自定义登录态标识
    openid: str                      # 用户 openid (可脱敏)
    is_new_user: bool                # 是否新用户

class SessionCheckResponse(BaseModel):
    """登录状态检查响应"""
    valid: bool                      # 是否有效
    openid: Optional[str] = None
    nickname: Optional[str] = None
```

### 6.2 打卡记录相关

```python
# app/schemas/record.py
from pydantic import BaseModel
from typing import Optional
from enum import Enum

class MealType(str, Enum):
    """餐次类型"""
    BREAKFAST = "早餐"
    LUNCH = "午餐"
    DINNER = "晚餐"

class CreateRecordRequest(BaseModel):
    """创建打卡记录请求"""
    meal_type: MealType              # 时间段: 早餐/午餐/晚餐
    price: float                     # 价格
    location: str                    # 地点
    date: Optional[int] = None       # 日期时间戳(毫秒)，默认当前时间

class CreateRecordResponse(BaseModel):
    """创建打卡记录响应"""
    record_id: str                   # 飞书记录 ID
    message: str = "success"
```

---

## 七、服务层设计

### 7.1 微信服务 (WechatService)

```python
# app/services/wechat.py

class WechatService:
    """微信 API 服务"""
    
    CODE2SESSION_URL = "https://api.weixin.qq.com/sns/jscode2session"
    
    async def code2session(self, code: str) -> dict:
        """
        通过 code 换取 session_key 和 openid
        
        微信 API: GET https://api.weixin.qq.com/sns/jscode2session
        参数: appid, secret, js_code, grant_type=authorization_code
        
        Returns:
            成功: {"openid": "xxx", "session_key": "xxx", "unionid": "xxx"}
            失败: {"errcode": 40029, "errmsg": "invalid code"}
        """
        pass
```

### 7.2 飞书服务 (FeishuService)

```python
# app/services/feishu.py
from app.config import settings

class FeishuService:
    """飞书 API 服务"""
    
    TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    RECORD_URL_TEMPLATE = "https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
    
    # Token 缓存 (类级别)
    _token: str = None
    _token_expire_at: float = 0
    
    def __init__(self):
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
        """
        获取 tenant_access_token
        
        - 检查缓存是否有效 (提前 5 分钟刷新)
        - 无效则调用 API 获取新 token
        - 缓存 token 和过期时间
        
        Returns:
            tenant_access_token
        """
        pass
    
    async def create_record(
        self,
        nickname: str,
        meal_type: str,
        price: float,
        location: str,
        date: int
    ) -> str:
        """
        创建打卡记录
        
        使用配置文件中的 app_token 和 table_id
        
        请求体:
        {
            "fields": {
                "微信昵称": nickname,
                "时间段": meal_type,
                "价格": price,
                "地点": location,
                "日期": date
            }
        }
        
        Returns:
            record_id
        """
        pass
```

### 7.3 Session 服务 (SessionService)

```python
# app/services/session.py
from dataclasses import dataclass
from typing import Dict, Optional
import time

@dataclass
class SessionData:
    """Session 数据结构"""
    openid: str
    session_key: str
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: float = 0
    expire_at: float = 0

class SessionService:
    """Session 管理服务 (内存存储)"""
    
    _sessions: Dict[str, SessionData] = {}
    
    def create_session(
        self, 
        openid: str, 
        session_key: str,
        nickname: str = None,
        avatar_url: str = None
    ) -> str:
        """
        创建 session
        
        - 生成安全随机 session_id
        - 存储 session 数据
        - 设置过期时间
        
        Returns:
            session_id
        """
        pass
    
    def get_session(self, session_id: str) -> Optional[SessionData]:
        """
        获取 session 数据
        
        - 检查 session 是否存在
        - 检查是否过期
        - 过期则删除并返回 None
        
        Returns:
            SessionData or None
        """
        pass
    
    def delete_session(self, session_id: str) -> bool:
        """删除 session"""
        pass
    
    def update_session(self, session_id: str, **kwargs) -> bool:
        """更新 session 数据"""
        pass
```

---

## 八、依赖注入设计

```python
# app/dependencies.py
from fastapi import Header, HTTPException, Depends
from typing import Optional
from app.services.session import SessionService, SessionData

session_service = SessionService()

async def get_session_id(
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id")
) -> Optional[str]:
    """从 Header 获取 session_id"""
    return x_session_id

async def get_current_session(
    session_id: Optional[str] = Depends(get_session_id)
) -> Optional[SessionData]:
    """获取当前 session (可选)"""
    if not session_id:
        return None
    return session_service.get_session(session_id)

async def require_login(
    session: Optional[SessionData] = Depends(get_current_session)
) -> SessionData:
    """要求登录"""
    if not session:
        raise HTTPException(
            status_code=401,
            detail="未登录或登录已过期"
        )
    return session
```

---

## 九、异常处理设计

```python
# app/core/exceptions.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

class WechatAPIError(Exception):
    """微信 API 错误"""
    def __init__(self, errcode: int, errmsg: str):
        self.errcode = errcode
        self.errmsg = errmsg

class FeishuAPIError(Exception):
    """飞书 API 错误"""
    def __init__(self, code: int, msg: str):
        self.code = code
        self.msg = msg

def setup_exception_handlers(app: FastAPI):
    
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
```

---

## 十、安全设计

### 10.1 Session ID 生成

```python
# app/core/security.py
import secrets

def generate_session_id() -> str:
    """生成安全的 session_id"""
    return secrets.token_urlsafe(32)
```

### 10.2 安全要点

1. **Session ID** - 使用 `secrets.token_urlsafe(32)` 生成 256 位随机 token
2. **Session 存储** - 当前使用内存存储，生产环境建议使用 Redis
3. **Session 过期** - 默认 7 天过期，可配置
4. **敏感信息** - session_key 不返回给前端，仅存储在服务端
5. **HTTPS** - 生产环境必须使用 HTTPS

---

## 十一、数据流详解

### 11.1 登录流程

```
1. 用户打开小程序
2. 小程序调用 wx.login() 获取临时 code (有效期 5 分钟)
3. 小程序请求后端:
   POST /xclub/v1/auth/login
   Body: { "code": "0a3xxx...", "nickname": "张三" }

4. 后端调用微信 API:
   GET https://api.weixin.qq.com/sns/jscode2session
   ?appid=xxx&secret=xxx&js_code=xxx&grant_type=authorization_code

5. 微信返回:
   { "openid": "oXxx...", "session_key": "xxx" }

6. 后端生成 session_id，存储 session 数据

7. 返回给小程序:
   { "session_id": "abc123...", "openid": "oXxx...", "is_new_user": true }

8. 小程序存储 session_id 到本地 (wx.setStorageSync)
```

### 11.2 打卡流程

```
1. 用户填写打卡信息，点击提交
2. 小程序请求后端:
   POST /xclub/v1/record/create
   Headers: { "X-Session-Id": "abc123..." }
   Body: { "meal_type": "午餐", "price": 15, "location": "万科食堂" }

3. 后端验证 session_id，获取用户信息

4. 后端从配置文件读取 app_token 和 table_id

5. 后端获取飞书 access_token (检查缓存)

6. 后端调用飞书 API:
   POST https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records
   
   其中:
   - app_token = settings.FEISHU_APP_TOKEN (配置文件)
   - table_id = settings.FEISHU_TABLE_ID (配置文件)
   
   Headers: { "Authorization": "Bearer {token}" }
   Body: {
     "fields": {
       "微信昵称": "张三",
       "时间段": "午餐",
       "价格": 15,
       "地点": "万科食堂",
       "日期": 1737158400000
     }
   }

7. 飞书返回:
   { "code": 0, "data": { "record": { "record_id": "recxxx" } } }

8. 返回给小程序:
   { "record_id": "recxxx", "message": "success" }
```

---

## 十二、依赖清单

```txt
# requirements.txt

# Web 框架
fastapi==0.109.0
uvicorn[standard]==0.27.0

# 数据验证
pydantic==2.5.3
pydantic-settings==2.1.0

# HTTP 客户端 (异步)
httpx==0.26.0

# 环境变量
python-dotenv==1.0.0
```

---

## 十三、实现步骤

| 阶段 | 任务 | 预计时间 |
|------|------|---------|
| **1** | 清理旧代码，创建新项目结构 | 10 分钟 |
| **2** | 实现配置管理 (config.py) | 5 分钟 |
| **3** | 实现 Session 服务 | 10 分钟 |
| **4** | 实现微信登录服务 | 15 分钟 |
| **5** | 实现认证路由 | 10 分钟 |
| **6** | 实现飞书 API 服务 | 15 分钟 |
| **7** | 实现打卡记录路由 | 10 分钟 |
| **8** | 添加异常处理和依赖注入 | 10 分钟 |
| **9** | 编写 README 和示例 | 5 分钟 |

**总计**: 约 1.5 小时

---

## 十四、后续扩展

1. **Redis Session 存储** - 支持分布式部署
2. **打卡记录查询** - 查询历史打卡记录
3. **统计功能** - 月度消费统计
4. **用户管理** - 用户信息维护
