import aiohttp
import asyncio
import time
import logging
from typing import Optional
from config import TestConfig
from auth_service import AuthService
from task_service import TaskService
from scale_service import ScaleService

class TestRunner:
    """
    测试运行器
    
    协调各个服务组件，执行完整的测试流程：登录 -> 获取任务 -> 填写问卷 -> 获取报告
    """
    
    def __init__(self, config: TestConfig):
        """
        初始化测试运行器
        
        Args:
            config: 测试配置对象
        """
        self.config = config
        # 初始化各个服务组件
        self.auth_service = AuthService(config.base_url, config.debug)
        self.task_service = TaskService(config.base_url, self.auth_service, config.debug)
        self.scale_service = ScaleService(config.base_url, self.auth_service, 
                                        self.task_service, config.debug)
        # 设置日志器
        self.logger = logging.getLogger('TestRunner')
        self.logger.setLevel(logging.DEBUG if config.debug else logging.INFO)
    
    async def run_test(self, session: Optional[aiohttp.ClientSession] = None) -> bool:
        """
        运行单个用户测试
        
        Args:
            session: 可选的aiohttp会话对象，如果不提供则创建新的
            
        Returns:
            bool: 测试是否成功
        """
        # 判断是否需要创建和关闭会话
        should_close_session = session is None
        if session is None:
            session = aiohttp.ClientSession()
        
        try:
            return await self._execute_test(session)
        finally:
            # 只有自己创建的会话才需要关闭
            if should_close_session:
                await session.close()
    
    async def _execute_test(self, session: aiohttp.ClientSession) -> bool:
        """
        执行测试逻辑的核心方法
        
        Args:
            session: aiohttp会话对象
            
        Returns:
            bool: 测试是否成功
        """
        self.logger.info("=== 开始学生端自动化测试 ===")
        
        # 步骤1: 用户登录
        if not await self.auth_service.login(session, self.config.username, self.config.password):
            self.logger.error("测试失败：登录失败")
            return False
        
        # 步骤2: 获取任务列表
        if not await self.task_service.get_student_tasks(session):
            self.logger.error("测试失败：无法获取任务")
            return False
        
        # 步骤3: 处理所有问卷
        return await self._process_scales(session)
    
    async def _process_scales(self, session: aiohttp.ClientSession) -> bool:
        """
        处理所有问卷的方法
        
        Args:
            session: aiohttp会话对象
        
        Returns:
            bool: 所有问卷处理是否成功
        """
        # 遍历任务中的所有问卷
        for i, scale in enumerate(self.task_service.scale_list, 1):
            scale_id = scale['id']
            scale_name = scale['scaleName']
            option_vo_list = scale['optionVo']
            
            self.logger.info(f"[{i}/{len(self.task_service.scale_list)}] 开始填写问卷: {scale_name}")
            
            # 为当前问卷生成随机答案
            answers = self.scale_service.generate_random_answers(option_vo_list)
            
            # 提交问卷答案
            if await self.scale_service.submit_scale_answers(session, scale_id, answers):
                self.logger.info("✓ 答案提交成功")
            else:
                self.logger.error("✗ 答案提交失败")
                return False  # 立即返回失败
            
            # 获取测评报告
            if await self.scale_service.get_report(session, scale_id):
                self.logger.info("✓ 报告获取成功")
            else:
                self.logger.error("✗ 报告获取失败")
                return False  # 立即返回失败
        
        self.logger.info("=== 学生端自动化测试完成 ===")
        return True