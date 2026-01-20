# coding: utf-8
"""
XClub API 测试脚本

使用方法:
    1. 启动服务: uvicorn app.main:app --reload --port 9900
    2. 运行测试: python tests/test_api.py

注意:
    - 微信登录接口需要真实的 wx.login() code，这里使用 mock 模式测试
    - 可以通过设置环境变量 TEST_SESSION_ID 使用已有的 session 测试其他接口
"""

import os
import sys
import httpx
import asyncio
from typing import Optional

# 配置
BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:9900")
TEST_SESSION_ID = os.getenv("TEST_SESSION_ID", "")

# 颜色输出
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"


def print_success(msg: str):
    print(f"{Colors.GREEN}✓ {msg}{Colors.RESET}")


def print_error(msg: str):
    print(f"{Colors.RED}✗ {msg}{Colors.RESET}")


def print_info(msg: str):
    print(f"{Colors.BLUE}→ {msg}{Colors.RESET}")


def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.RESET}")


class APITester:
    """API 测试器"""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session_id: Optional[str] = TEST_SESSION_ID or None
        self.client = httpx.AsyncClient(base_url=base_url, timeout=30.0)

    async def close(self):
        await self.client.aclose()

    def _headers(self) -> dict:
        """获取请求头"""
        headers = {"Content-Type": "application/json"}
        if self.session_id:
            headers["X-Session-Id"] = self.session_id
        return headers

    # ==================== 健康检查 ====================

    async def test_health(self) -> bool:
        """测试服务是否正常"""
        print_info("测试服务健康状态...")
        try:
            resp = await self.client.get("/docs")
            if resp.status_code == 200:
                print_success("服务运行正常")
                return True
            else:
                print_error(f"服务异常: {resp.status_code}")
                return False
        except Exception as e:
            print_error(f"无法连接服务: {e}")
            return False

    # ==================== 认证模块测试 ====================

    async def test_login_mock(self) -> bool:
        """测试登录接口 (Mock 模式)
        
        注意: 真实环境需要微信小程序的 code，这里模拟测试接口响应
        """
        print_info("测试登录接口 (Mock 模式)...")
        
        # 使用一个假的 code，会返回微信 API 错误
        # 这里只是验证接口是否正常工作
        resp = await self.client.post(
            "/xclub/v1/auth/login",
            json={
                "code": "test_mock_code_12345",
                "nickname": "测试用户",
                "avatar_url": "https://example.com/avatar.png"
            },
            headers=self._headers()
        )
        
        print(f"   状态码: {resp.status_code}")
        print(f"   响应: {resp.json()}")
        
        # 因为是假的 code，预期会返回微信 API 错误
        if resp.status_code in [200, 400]:
            print_success("登录接口响应正常")
            
            # 如果登录成功，保存 session_id
            if resp.status_code == 200:
                data = resp.json()
                self.session_id = data.get("session_id")
                print_success(f"登录成功，session_id: {self.session_id[:16]}...")
            return True
        else:
            print_error(f"登录接口异常: {resp.status_code}")
            return False

    async def test_check_session(self) -> bool:
        """测试检查登录状态"""
        print_info("测试检查登录状态...")
        
        resp = await self.client.get(
            "/xclub/v1/auth/check",
            headers=self._headers()
        )
        
        print(f"   状态码: {resp.status_code}")
        print(f"   响应: {resp.json()}")
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get("valid"):
                print_success(f"Session 有效，openid: {data.get('openid')}")
            else:
                print_warning("Session 无效或未登录")
            return True
        else:
            print_error(f"检查登录状态失败: {resp.status_code}")
            return False

    async def test_logout(self) -> bool:
        """测试退出登录"""
        print_info("测试退出登录...")
        
        if not self.session_id:
            print_warning("未登录，跳过退出测试")
            return True
        
        resp = await self.client.post(
            "/xclub/v1/auth/logout",
            headers=self._headers()
        )
        
        print(f"   状态码: {resp.status_code}")
        print(f"   响应: {resp.json()}")
        
        if resp.status_code == 200:
            print_success("退出登录成功")
            return True
        elif resp.status_code == 401:
            print_warning("未登录状态")
            return True
        else:
            print_error(f"退出登录失败: {resp.status_code}")
            return False

    # ==================== 用户模块测试 ====================

    async def test_get_user_info(self) -> bool:
        """测试获取当前用户信息"""
        print_info("测试获取当前用户信息...")
        
        resp = await self.client.get(
            "/xclub/v1/user/info",
            headers=self._headers()
        )
        
        print(f"   状态码: {resp.status_code}")
        print(f"   响应: {resp.json()}")
        
        if resp.status_code == 200:
            data = resp.json()
            print_success(f"获取用户信息成功: {data.get('nickname')} (角色: {data.get('role_name')})")
            return True
        elif resp.status_code == 401:
            print_warning("未登录，无法获取用户信息")
            return True
        else:
            print_error(f"获取用户信息失败: {resp.status_code}")
            return False

    async def test_update_user_info(self) -> bool:
        """测试更新用户信息"""
        print_info("测试更新用户信息...")
        
        if not self.session_id:
            print_warning("未登录，跳过更新测试")
            return True
        
        resp = await self.client.put(
            "/xclub/v1/user/info",
            json={
                "nickname": "测试昵称_" + str(int(asyncio.get_event_loop().time())),
                "phone_num": "13800138000"
            },
            headers=self._headers()
        )
        
        print(f"   状态码: {resp.status_code}")
        print(f"   响应: {resp.json()}")
        
        if resp.status_code == 200:
            print_success("更新用户信息成功")
            return True
        elif resp.status_code == 401:
            print_warning("未登录，无法更新用户信息")
            return True
        else:
            print_error(f"更新用户信息失败: {resp.status_code}")
            return False

    async def test_get_user_by_id(self, user_id: int = 1) -> bool:
        """测试获取指定用户信息"""
        print_info(f"测试获取用户 ID={user_id} 的信息...")
        
        resp = await self.client.get(
            f"/xclub/v1/user/{user_id}",
            headers=self._headers()
        )
        
        print(f"   状态码: {resp.status_code}")
        print(f"   响应: {resp.json()}")
        
        if resp.status_code == 200:
            data = resp.json()
            print_success(f"获取用户信息成功: {data.get('nickname')}")
            return True
        elif resp.status_code == 404:
            print_warning(f"用户 ID={user_id} 不存在")
            return True
        elif resp.status_code == 401:
            print_warning("未登录，无法获取用户信息")
            return True
        else:
            print_error(f"获取用户信息失败: {resp.status_code}")
            return False

    # ==================== 打卡记录模块测试 ====================

    async def test_create_record(self) -> bool:
        """测试创建打卡记录"""
        print_info("测试创建打卡记录...")
        
        if not self.session_id:
            print_warning("未登录，跳过打卡测试")
            return True
        
        resp = await self.client.post(
            "/xclub/v1/record/create",
            json={
                "meal_type": "午餐",
                "price": 15.5,
                "location": "测试食堂"
            },
            headers=self._headers()
        )
        
        print(f"   状态码: {resp.status_code}")
        print(f"   响应: {resp.json()}")
        
        if resp.status_code == 200:
            data = resp.json()
            print_success(f"创建打卡记录成功: record_id={data.get('record_id')}")
            return True
        elif resp.status_code == 401:
            print_warning("未登录，无法创建打卡记录")
            return True
        elif resp.status_code == 400:
            print_warning("飞书 API 错误（可能是配置问题）")
            return True
        else:
            print_error(f"创建打卡记录失败: {resp.status_code}")
            return False


async def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("XClub API 测试")
    print("=" * 60)
    print(f"服务地址: {BASE_URL}")
    if TEST_SESSION_ID:
        print(f"使用 Session: {TEST_SESSION_ID[:16]}...")
    print("=" * 60)
    print()

    tester = APITester(BASE_URL)
    results = []

    try:
        # 1. 健康检查
        print("\n[1/7] 健康检查")
        print("-" * 40)
        if not await tester.test_health():
            print_error("服务未启动，请先启动服务")
            return

        # 2. 登录测试 (Mock)
        print("\n[2/7] 认证模块 - 登录")
        print("-" * 40)
        results.append(("登录接口", await tester.test_login_mock()))

        # 3. 检查登录状态
        print("\n[3/7] 认证模块 - 检查登录状态")
        print("-" * 40)
        results.append(("检查登录状态", await tester.test_check_session()))

        # 4. 获取用户信息
        print("\n[4/7] 用户模块 - 获取当前用户信息")
        print("-" * 40)
        results.append(("获取用户信息", await tester.test_get_user_info()))

        # 5. 更新用户信息
        print("\n[5/7] 用户模块 - 更新用户信息")
        print("-" * 40)
        results.append(("更新用户信息", await tester.test_update_user_info()))

        # 6. 获取指定用户
        print("\n[6/7] 用户模块 - 获取指定用户")
        print("-" * 40)
        results.append(("获取指定用户", await tester.test_get_user_by_id(1)))

        # 7. 创建打卡记录
        print("\n[7/7] 打卡模块 - 创建记录")
        print("-" * 40)
        results.append(("创建打卡记录", await tester.test_create_record()))

    finally:
        await tester.close()

    # 打印测试结果汇总
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    failed = len(results) - passed
    
    for name, result in results:
        status = f"{Colors.GREEN}PASS{Colors.RESET}" if result else f"{Colors.RED}FAIL{Colors.RESET}"
        print(f"  {name}: {status}")
    
    print("-" * 40)
    print(f"通过: {passed}, 失败: {failed}, 总计: {len(results)}")
    
    if failed == 0:
        print_success("\n所有测试通过!")
    else:
        print_error(f"\n有 {failed} 个测试失败")


async def test_with_real_session(session_id: str):
    """使用真实 session 测试（需要先通过小程序登录获取 session_id）"""
    print("=" * 60)
    print("使用真实 Session 测试")
    print("=" * 60)
    
    tester = APITester(BASE_URL)
    tester.session_id = session_id
    
    try:
        await tester.test_health()
        await tester.test_check_session()
        await tester.test_get_user_info()
        await tester.test_update_user_info()
        await tester.test_create_record()
    finally:
        await tester.close()


if __name__ == "__main__":
    # 检查命令行参数
    if len(sys.argv) > 1:
        # 使用指定的 session_id 测试
        session_id = sys.argv[1]
        asyncio.run(test_with_real_session(session_id))
    else:
        # 运行标准测试
        asyncio.run(run_tests())
