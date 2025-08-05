import aiohttp
import asyncio
import time
import logging
from typing import List
from config import TestConfig, ConcurrentTestConfig
from test_runner import TestRunner

class ConcurrentTestManager:
    """
    并发测试管理器
    
    负责管理和执行大规模并发测试，包括连接池管理、任务调度和结果统计
    """
    
    def __init__(self, base_url: str, concurrent_config: ConcurrentTestConfig):
        """
        初始化并发测试管理器
        
        Args:
            base_url: API服务器基础URL
            concurrent_config: 并发测试配置对象
        """
        self.base_url = base_url
        self.concurrent_config = concurrent_config
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """
        设置日志器，确保日志格式统一且不重复添加处理器
        
        Returns:
            logging.Logger: 配置好的日志器
        """
        logger = logging.getLogger('ConcurrentTest')
        logger.setLevel(logging.INFO)
        
        # 避免重复添加处理器
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _create_connector(self) -> aiohttp.TCPConnector:
        """
        创建优化的TCP连接器，用于高并发场景
        
        Returns:
            aiohttp.TCPConnector: 配置好的连接器
        """
        return aiohttp.TCPConnector(
            limit=self.concurrent_config.connection_limit,                    # 总连接数限制
            limit_per_host=self.concurrent_config.connection_limit_per_host,  # 每主机连接数限制
            ttl_dns_cache=self.concurrent_config.dns_cache_ttl,              # DNS缓存TTL
            use_dns_cache=True,                                               # 启用DNS缓存
        )
    
    async def run_concurrent_tests(self, debug: bool = False) -> None:
        """
        运行并发测试的主方法
        
        Args:
            debug: 是否开启调试模式
        """
        self.logger.info(f"开始 {self.concurrent_config.user_count} 个真正并发测试")
        start_time = time.time()
        
        # 创建优化的连接器
        connector = self._create_connector()
        
        # 使用单个会话管理所有并发请求
        async with aiohttp.ClientSession(connector=connector) as session:
            # 创建所有用户的测试任务
            tasks = [
                self._run_single_user_test(session, i, debug) 
                for i in range(1, self.concurrent_config.user_count + 1)
            ]
            # 并发执行所有任务，收集结果和异常
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 统计和报告测试结果
        self._report_results(results, start_time)
    
    async def _run_single_user_test(self, session: aiohttp.ClientSession, 
                                   user_index: int, debug: bool) -> bool:
        """
        运行单个用户的测试
        
        Args:
            session: 共享的aiohttp会话对象
            user_index: 用户索引，用于生成用户名
            debug: 是否开启调试模式
            
        Returns:
            bool: 测试是否成功
        """
        # 生成测试用户名和密码
        username = f"test{user_index:04d}"  # 格式化为test0001, test0002等
        password = "123456"
        
        # 创建测试配置
        config = TestConfig(
            base_url=self.base_url,
            username=username,
            password=password,
            debug=debug
        )
        
        # 创建测试运行器
        runner = TestRunner(config)
        
        try:
            start_time = time.time()
            # 执行测试，复用传入的session
            success = await runner.run_test(session)
            end_time = time.time()
            
            # 记录测试结果
            if success:
                self.logger.info(f"用户 {username} 测试成功，耗时: {end_time - start_time:.2f}秒")
                return True
            else:
                self.logger.error(f"用户 {username} 测试失败")
                return False
                
        except Exception as e:
            # 捕获并记录异常
            self.logger.error(f"用户 {username} 测试异常: {str(e)}")
            return False
    
    def _report_results(self, results: List, start_time: float) -> None:
        """
        统计并报告测试结果
        
        Args:
            results: 所有测试任务的结果列表
            start_time: 测试开始时间
        """
        end_time = time.time()
        # 统计成功和失败的数量
        success_count = sum(1 for result in results if result is True)
        failed_count = len(results) - success_count
        total_time = end_time - start_time
        
        # 输出详细的测试报告
        self.logger.info(f"=== {self.concurrent_config.user_count}并发测试完成 ===")
        self.logger.info(f"总用户数: {self.concurrent_config.user_count}")
        self.logger.info(f"成功: {success_count}")
        self.logger.info(f"失败: {failed_count}")
        self.logger.info(f"成功率: {success_count/self.concurrent_config.user_count*100:.2f}%")
        self.logger.info(f"总耗时: {total_time:.2f}秒")
        self.logger.info(f"QPS: {self.concurrent_config.user_count/total_time:.2f}")