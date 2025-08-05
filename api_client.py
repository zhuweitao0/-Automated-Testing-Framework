import aiohttp
import json
import logging
from typing import Dict, Any, Optional, List, Tuple

class APIClient:
    """
    API客户端基类
    
    提供通用的HTTP请求功能和日志记录，所有具体的API服务类都继承此类
    """
    
    def __init__(self, base_url: str, debug: bool = False):
        """
        初始化API客户端
        
        Args:
            base_url: API服务器基础URL
            debug: 是否开启调试模式
        """
        self.base_url = base_url
        self.debug = debug
        # 为每个子类创建独立的日志器
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.DEBUG if debug else logging.INFO)
        
        # 添加控制台处理器
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def log_response(self, api_name: str, url: str, status: int, data: Dict[str, Any]):
        """
        记录API响应信息
        
        Args:
            api_name: API名称，用于标识不同的接口
            url: 请求的完整URL
            status: HTTP状态码
            data: 响应数据
        """
        if self.debug:
            print(f"\n=== {api_name} API响应 ===")
            print(f"请求URL: {url}")
            print(f"状态码: {status}")
            print(f"响应数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
            print("=" * 50)
    
    async def _make_request(self, session: aiohttp.ClientSession, method: str, 
                          endpoint: str, headers: Optional[Dict] = None, 
                          data: Optional[Dict] = None) -> Tuple[int, Dict[str, Any]]:
        """
        通用HTTP请求方法
        
        Args:
            session: aiohttp会话对象
            method: HTTP方法（GET, POST等）
            endpoint: API端点路径
            headers: 请求头字典
            data: 请求体数据
            
        Returns:
            tuple: (状态码, 响应数据字典)
        """
        url = f"{self.base_url}{endpoint}"
        headers = headers or {}
        
        # 发送HTTP请求并处理响应
        async with session.request(method, url, headers=headers, json=data) as response:
            status = response.status
            # 只有状态码为200时才解析JSON响应
            response_data = await response.json() if status == 200 else {}
            return status, response_data