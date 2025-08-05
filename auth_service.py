import aiohttp
from typing import Optional, Tuple
from api_client import APIClient

class AuthService(APIClient):
    """
    认证服务类
    
    负责用户登录认证和token管理，提供认证相关的功能
    """
    
    def __init__(self, base_url: str, debug: bool = False):
        """
        初始化认证服务
        
        Args:
            base_url: API服务器基础URL
            debug: 是否开启调试模式
        """
        super().__init__(base_url, debug)
        self.user_id: Optional[str] = None  # 用户ID，登录成功后设置
        self.token: Optional[str] = None    # 认证token，登录成功后设置
    
    async def login(self, session: aiohttp.ClientSession, username: str, password: str) -> bool:
        """
        用户登录
        
        Args:
            session: aiohttp会话对象
            username: 用户名
            password: 密码
            
        Returns:
            bool: 登录是否成功
        """
        # 构造登录请求数据
        login_data = {"account": username, "password": password}
        
        # 发送登录请求
        status, data = await self._make_request(session, "POST", "/jeecg-boot/api/clientLogin", data=login_data)
        self.log_response("登录", f"{self.base_url}/jeecg-boot/api/clientLogin", status, data)
        
        # 检查HTTP状态码
        if status != 200:
            self.logger.error(f"登录失败: {status}")
            return False
        
        # 检查业务逻辑是否成功
        if data.get('success'):
            result = data['result']
            # 保存用户信息和token
            self.user_id = result['studentInfo']['id']
            self.token = result['token']
            username = result['studentInfo']['userName']
            self.logger.info(f"登录成功: {username}, 用户ID: {self.user_id}")
            return True
        else:
            self.logger.error(f"登录失败: {data.get('message', '未知错误')}")
            return False
    
    def get_auth_headers(self) -> dict:
        """
        获取认证请求头
        
        Returns:
            dict: 包含认证信息的请求头字典
        """
        headers = {}
        if self.token:
            # 添加Bearer token到Authorization头
            headers['Authorization'] = f'Bearer {self.token}'
        return headers