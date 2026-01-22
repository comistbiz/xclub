# XClub 小程序后端 API 文档

## 基本信息

- **Base URL**: `https://your-domain.com` 或 `http://localhost:9900`
- **API 前缀**: `/xclub/v1`
- **数据格式**: JSON
- **字符编码**: UTF-8

## 认证方式

除登录接口外，所有接口都需要在 HTTP Header 中携带 `X-Session-Id`：

```
X-Session-Id: your_session_id_here
```

Session 有效期为 7 天，过期后需重新登录。

---

## 统一响应格式

所有接口返回统一的 JSON 格式：

```json
{
  "code": 0,
  "msg": "",
  "data": {}
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| code | integer | 错误码，0 表示成功，非 0 表示失败 |
| msg | string | 提示信息 |
| data | object/null | 响应数据，失败时为 null |

### 错误码定义

| 错误码 | 说明 |
|--------|------|
| 0 | 成功 |
| 1001 | 参数错误 |
| 1002 | 服务器内部错误 |
| 2001 | Session 无效 |
| 2002 | Session 已过期 |
| 2003 | 未登录 |
| 2004 | 权限不足 |
| 3001 | 用户不存在 |
| 3002 | 用户已注册 |
| 4001 | 激活码不存在 |
| 4002 | 激活码已使用 |
| 4003 | 激活码已作废 |
| 5001 | 微信 API 错误 |
| 6001 | 飞书 API 错误 |

---

## 一、认证模块 `/xclub/v1/auth`

### 1.1 微信登录

**接口**: `POST /xclub/v1/auth/login`

**描述**: 使用微信小程序 `wx.login()` 获取的 code 进行登录，返回 session_id 用于后续请求认证。

**是否需要登录**: 否

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | string | 是 | wx.login() 返回的 code |
| nickname | string | 否 | 用户昵称 |
| avatar_url | string | 否 | 用户头像 URL |

**请求示例**:

```json
{
  "code": "0a3xxx...",
  "nickname": "张三",
  "avatar_url": "https://thirdwx.qlogo.cn/..."
}
```

**响应参数** (data 字段):

| 参数 | 类型 | 说明 |
|------|------|------|
| session_id | string | 登录凭证，后续请求需携带 |
| openid | string | 用户唯一标识 |
| is_new_user | boolean | 是否为新用户 |
| role | integer | 用户角色：1=游客，2=成员，3=管理员 |
| role_name | string | 角色名称 |

**响应示例**:

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "session_id": "abc123def456...",
    "openid": "oXxxxxxxxxxxxx",
    "is_new_user": true,
    "role": 1,
    "role_name": "游客"
  }
}
```

**小程序调用示例**:

```javascript
// 1. 调用 wx.login 获取 code
wx.login({
  success: async (res) => {
    if (res.code) {
      // 2. 获取用户信息（可选）
      const userInfo = wx.getStorageSync('userInfo') || {}
      
      // 3. 调用后端登录接口
      const result = await wx.request({
        url: 'https://your-domain.com/xclub/v1/auth/login',
        method: 'POST',
        data: {
          code: res.code,
          nickname: userInfo.nickName,
          avatar_url: userInfo.avatarUrl
        }
      })
      
      // 4. 保存 session_id
      if (result.data.code === 0) {
        wx.setStorageSync('session_id', result.data.data.session_id)
        wx.setStorageSync('openid', result.data.data.openid)
      }
    }
  }
})
```

---

### 1.2 检查登录状态

**接口**: `GET /xclub/v1/auth/check`

**描述**: 检查当前 session 是否有效。

**是否需要登录**: 是（需要 X-Session-Id）

**请求参数**: 无

**响应参数** (data 字段):

| 参数 | 类型 | 说明 |
|------|------|------|
| valid | boolean | session 是否有效 |
| openid | string | 用户 openid（有效时返回） |
| nickname | string | 用户昵称（有效时返回） |
| role | integer | 用户角色：1=游客，2=成员，3=管理员（有效时返回） |
| role_name | string | 角色名称（有效时返回） |

**响应示例**:

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "valid": true,
    "openid": "oXxxxxxxxxxxxx",
    "nickname": "张三",
    "role": 2,
    "role_name": "成员"
  }
}
```

**小程序调用示例**:

```javascript
const sessionId = wx.getStorageSync('session_id')

const result = await wx.request({
  url: 'https://your-domain.com/xclub/v1/auth/check',
  method: 'GET',
  header: {
    'X-Session-Id': sessionId
  }
})

if (result.data.code !== 0 || !result.data.data.valid) {
  // session 无效，需要重新登录
  wx.removeStorageSync('session_id')
  // 跳转登录页或重新调用 wx.login
}
```

---

### 1.3 退出登录

**接口**: `POST /xclub/v1/auth/logout`

**描述**: 退出登录，清除服务端 session。

**是否需要登录**: 是

**请求参数**: 无

**响应示例**:

```json
{
  "code": 0,
  "msg": "退出成功",
  "data": null
}
```

---

### 1.4 用户注册

**接口**: `POST /xclub/v1/auth/register`

**描述**: 使用激活码注册成为俱乐部成员。激活码只能使用一次，使用后会关联到用户。

**是否需要登录**: 否

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | string | 是 | wx.login() 返回的 code |
| activation_code | string | 是 | 激活码 |
| realname | string | 否 | 真实姓名 |
| nickname | string | 否 | 用户昵称 |
| avatar_url | string | 否 | 用户头像 URL |

**请求示例**:

```json
{
  "code": "0a3xxx...",
  "activation_code": "ABC123XYZ789",
  "realname": "张三",
  "nickname": "小张",
  "avatar_url": "https://thirdwx.qlogo.cn/..."
}
```

**响应参数** (data 字段):

| 参数 | 类型 | 说明 |
|------|------|------|
| session_id | string | 登录凭证，后续请求需携带 |
| openid | string | 用户唯一标识 |
| user_id | integer | 用户 ID |
| role | integer | 用户角色：1=游客，2=成员，3=管理员 |
| role_name | string | 角色名称 |

**响应示例**:

```json
{
  "code": 0,
  "msg": "注册成功",
  "data": {
    "session_id": "abc123def456...",
    "openid": "oXxxxxxxxxxxxx",
    "user_id": 1,
    "role": 2,
    "role_name": "成员"
  }
}
```

**错误响应示例**:

```json
{
  "code": 4001,
  "msg": "激活码不存在",
  "data": null
}
```

**错误码**:

| code | msg | 说明 |
|------|-----|------|
| 4001 | 激活码不存在 | 输入的激活码不存在 |
| 4002 | 激活码已被使用 | 激活码已被其他用户使用 |
| 4003 | 激活码已作废 | 激活码已被管理员作废 |
| 3002 | 用户已注册 | 用户已经是成员或管理员 |

**小程序调用示例**:

```javascript
// 1. 调用 wx.login 获取 code
wx.login({
  success: async (res) => {
    if (res.code) {
      // 2. 调用后端注册接口
      const result = await wx.request({
        url: 'https://your-domain.com/xclub/v1/auth/register',
        method: 'POST',
        data: {
          code: res.code,
          activation_code: 'ABC123XYZ789',
          realname: '张三',
          nickname: '小张'
        }
      })
      
      if (result.data.code === 0) {
        // 3. 保存 session_id
        wx.setStorageSync('session_id', result.data.data.session_id)
        wx.setStorageSync('openid', result.data.data.openid)
        wx.showToast({ title: '注册成功' })
      } else {
        // 4. 处理错误
        wx.showToast({ title: result.data.msg, icon: 'none' })
      }
    }
  }
})
```

**业务逻辑说明**:

1. 如果用户已存在且角色 >= 成员，返回 "用户已注册" 错误
2. 如果用户已存在但是游客，升级为成员并更新用户信息
3. 如果用户不存在，创建新用户，角色直接设置为成员
4. 注册成功后，激活码状态变为 "已使用"，并关联 user_id

---

## 二、用户模块 `/xclub/v1/user`

### 2.1 获取当前用户信息

**接口**: `GET /xclub/v1/user/info`

**描述**: 获取当前登录用户的详细信息。

**是否需要登录**: 是

**请求参数**: 无

**响应参数** (data 字段):

| 参数 | 类型 | 说明 |
|------|------|------|
| id | integer | 用户 ID |
| openid | string | 微信 openid |
| nickname | string | 昵称 |
| avatar | string | 头像 URL |
| realname | string | 真实姓名 |
| phone_num | string | 手机号码 |
| sex | integer | 性别：1=男，2=女，3=未知 |
| role | integer | 角色：1=游客，2=成员，3=管理员 |
| role_name | string | 角色名称 |
| state | integer | 状态：1=正常，2=封禁，3=注销 |
| birthday | string | 生日（格式：YYYY-MM-DD） |
| address | string | 地址 |
| email | string | 邮箱 |
| create_time | string | 创建时间 |

**响应示例**:

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "id": 1,
    "openid": "oXxxxxxxxxxxxx",
    "nickname": "张三",
    "avatar": "https://thirdwx.qlogo.cn/...",
    "realname": "",
    "phone_num": "",
    "sex": 1,
    "role": 1,
    "role_name": "游客",
    "state": 1,
    "birthday": null,
    "address": "",
    "email": "",
    "create_time": "2026-01-21 10:00:00"
  }
}
```

**小程序调用示例**:

```javascript
const sessionId = wx.getStorageSync('session_id')

const result = await wx.request({
  url: 'https://your-domain.com/xclub/v1/user/info',
  method: 'GET',
  header: {
    'X-Session-Id': sessionId
  }
})

if (result.data.code === 0) {
  console.log('用户信息:', result.data.data)
}
```

---

### 2.2 获取指定用户信息

**接口**: `GET /xclub/v1/user/{user_id}`

**描述**: 根据用户 ID 获取用户信息。

**是否需要登录**: 是

**路径参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | integer | 是 | 用户 ID |

**响应参数**: 同 2.1

**错误响应示例**:

```json
{
  "code": 3001,
  "msg": "用户不存在",
  "data": null
}
```

---

### 2.3 更新当前用户信息

**接口**: `PUT /xclub/v1/user/info`

**描述**: 更新当前登录用户的信息。

**是否需要登录**: 是

**请求参数**（所有字段可选，只传需要更新的字段）:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| nickname | string | 否 | 昵称 |
| avatar | string | 否 | 头像 URL |
| realname | string | 否 | 真实姓名 |
| phone_num | string | 否 | 手机号码 |
| sex | integer | 否 | 性别：1=男，2=女，3=未知 |
| birthday | string | 否 | 生日（格式：YYYY-MM-DD） |
| address | string | 否 | 地址 |
| email | string | 否 | 邮箱 |

**请求示例**:

```json
{
  "nickname": "新昵称",
  "phone_num": "13800138000"
}
```

**响应参数**: 返回更新后的完整用户信息，同 2.1

**小程序调用示例**:

```javascript
const sessionId = wx.getStorageSync('session_id')

const result = await wx.request({
  url: 'https://your-domain.com/xclub/v1/user/info',
  method: 'PUT',
  header: {
    'Content-Type': 'application/json',
    'X-Session-Id': sessionId
  },
  data: {
    nickname: '新昵称',
    phone_num: '13800138000'
  }
})

if (result.data.code === 0) {
  console.log('更新后的用户信息:', result.data.data)
}
```

---

### 2.4 更新用户角色（管理员）

**接口**: `PUT /xclub/v1/user/{user_id}/role`

**描述**: 更新指定用户的角色，仅管理员可操作。

**是否需要登录**: 是（需要管理员权限）

**路径参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | integer | 是 | 目标用户 ID |

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| role | integer | 是 | 角色：1=游客，2=成员，3=管理员 |

**请求示例**:

```json
{
  "role": 2
}
```

**响应示例**:

```json
{
  "code": 0,
  "msg": "更新成功",
  "data": null
}
```

**错误响应示例**:

```json
{
  "code": 2004,
  "msg": "需要管理员权限",
  "data": null
}
```

---

## 三、打卡记录模块 `/xclub/v1/record`

### 3.1 创建打卡记录

**接口**: `POST /xclub/v1/record/create`

**描述**: 创建一条打卡记录，记录会保存到飞书多维表格。

**是否需要登录**: 是

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| meal_type | string | 是 | 时间段：早餐/午餐/晚餐 |
| price | number | 是 | 价格 |
| location | string | 否 | 地点（可选，暂不使用） |
| date | integer | 否 | 日期时间戳（毫秒），默认当前时间 |

**请求示例**:

```json
{
  "meal_type": "午餐",
  "price": 15.5
}
```

**响应参数** (data 字段):

| 参数 | 类型 | 说明 |
|------|------|------|
| record_id | string | 飞书记录 ID |

**响应示例**:

```json
{
  "code": 0,
  "msg": "打卡成功",
  "data": {
    "record_id": "recxxxxxxxxxxxxx"
  }
}
```

**小程序调用示例**:

```javascript
const sessionId = wx.getStorageSync('session_id')

const result = await wx.request({
  url: 'https://your-domain.com/xclub/v1/record/create',
  method: 'POST',
  header: {
    'Content-Type': 'application/json',
    'X-Session-Id': sessionId
  },
  data: {
    meal_type: '午餐',
    price: 15.5,
    location: '万科食堂'
  }
})

if (result.data.code === 0) {
  wx.showToast({ title: '打卡成功' })
}
```

---

## 四、小程序封装建议

### 请求封装

```javascript
// utils/request.js
const BASE_URL = 'https://your-domain.com'

const request = async (options) => {
  const sessionId = wx.getStorageSync('session_id')
  
  const header = {
    'Content-Type': 'application/json',
    ...options.header
  }
  
  // 自动添加 session_id
  if (sessionId) {
    header['X-Session-Id'] = sessionId
  }
  
  try {
    const res = await wx.request({
      url: BASE_URL + options.url,
      method: options.method || 'GET',
      data: options.data,
      header
    })
    
    const { code, msg, data } = res.data
    
    // 处理登录态失效
    if (code === 2001 || code === 2002 || code === 2003) {
      wx.removeStorageSync('session_id')
      wx.navigateTo({ url: '/pages/login/login' })
      return Promise.reject(new Error(msg || '登录已过期'))
    }
    
    // 处理业务错误
    if (code !== 0) {
      return Promise.reject(new Error(msg || '请求失败'))
    }
    
    return data
  } catch (err) {
    return Promise.reject(err)
  }
}

// 导出 API 方法
export const api = {
  // 认证
  login: (data) => request({ url: '/xclub/v1/auth/login', method: 'POST', data }),
  register: (data) => request({ url: '/xclub/v1/auth/register', method: 'POST', data }),
  checkSession: () => request({ url: '/xclub/v1/auth/check' }),
  logout: () => request({ url: '/xclub/v1/auth/logout', method: 'POST' }),
  
  // 用户
  getUserInfo: () => request({ url: '/xclub/v1/user/info' }),
  updateUserInfo: (data) => request({ url: '/xclub/v1/user/info', method: 'PUT', data }),
  
  // 打卡
  createRecord: (data) => request({ url: '/xclub/v1/record/create', method: 'POST', data })
}
```

### 使用示例

```javascript
import { api } from '../../utils/request'

// 登录
const login = async () => {
  const { code } = await wx.login()
  const result = await api.login({ code })
  wx.setStorageSync('session_id', result.session_id)
}

// 注册
const register = async (activationCode, realname) => {
  const { code } = await wx.login()
  const result = await api.register({
    code,
    activation_code: activationCode,
    realname
  })
  wx.setStorageSync('session_id', result.session_id)
}

// 获取用户信息
const getUserInfo = async () => {
  const userInfo = await api.getUserInfo()
  console.log(userInfo)
}

// 打卡
const checkIn = async () => {
  const result = await api.createRecord({
    meal_type: '午餐',
    price: 15,
    location: '食堂'
  })
  wx.showToast({ title: '打卡成功' })
}
```

---

## 五、枚举值参考

### 用户角色 (role)

| 值 | 名称 | 说明 |
|----|------|------|
| 1 | 游客 | 默认角色 |
| 2 | 成员 | 俱乐部成员 |
| 3 | 管理员 | 可管理用户 |

### 用户状态 (state)

| 值 | 名称 | 说明 |
|----|------|------|
| 1 | 正常 | 正常使用 |
| 2 | 封禁 | 账号被封禁 |
| 3 | 注销 | 账号已注销 |

### 用户性别 (sex)

| 值 | 名称 |
|----|------|
| 1 | 男 |
| 2 | 女 |
| 3 | 未知 |

### 餐次类型 (meal_type)

| 值 | 说明 |
|----|------|
| 早餐 | 早餐时段 |
| 午餐 | 午餐时段 |
| 晚餐 | 晚餐时段 |
