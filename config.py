from dataclasses import dataclass
from typing import Optional

@dataclass
class TestConfig:
    """
    测试配置类
    
    用于存储单个测试实例的配置信息，包括服务器地址、用户凭据等
    """
    base_url: str  # API服务器基础URL
    username: Optional[str] = None  # 登录用户名
    password: Optional[str] = None  # 登录密码
    debug: bool = False  # 是否开启调试模式
    
    def __post_init__(self):
        """初始化后处理，确保URL格式正确"""
        self.base_url = self.base_url.rstrip('/')

@dataclass
class ConcurrentTestConfig:
    """
    并发测试配置类
    
    用于配置并发测试的参数，包括用户数量、连接限制等
    """
    user_count: int = 1000  # 并发用户数量
    connection_limit: int = 2000  # 总连接数限制
    connection_limit_per_host: int = 1500  # 每个主机的连接数限制
    dns_cache_ttl: int = 300  # DNS缓存生存时间（秒）

@dataclass
class AdminConfig:
    """管理员配置类"""
    base_url: str
    admin_username: str
    admin_password: str
    task_name: str = "自动化测评任务"
    scale_id: str = "1571395659305803777"  # 改为单个问卷ID，默认值优先级较低
    debug: bool = False
    
    def __post_init__(self):
        self.base_url = self.base_url.rstrip('/')
