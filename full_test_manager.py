import aiohttp
import asyncio
import logging
from typing import Optional, Any, Union, Coroutine
from admin_service import AdminService
from concurrent_test_manager import ConcurrentTestManager
from config import AdminConfig, ConcurrentTestConfig



class FullTestManager:
    """完整测试流程管理器 - 管理员发布 + 学生并发测试"""
    
    def __init__(self, admin_config: AdminConfig, concurrent_config: ConcurrentTestConfig):
        self.admin_config = admin_config
        self.concurrent_config = concurrent_config
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志器"""
        logger = logging.getLogger('FullTestManager')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    async def run_full_test_flow(self) -> bool:
        """执行完整测试流程"""
        self.logger.info("=== 开始完整测试流程 ===")
        
        # 管理员发布测评
        success = await self._admin_publish_evaluation()
        if not success:
            self.logger.error("管理员发布测评失败，终止流程")
            return False
        
        # 等待任务生效
        self.logger.info("等待任务生效...")
        await asyncio.sleep(3)
        
        # 学生端自行搜索和执行任务
        await self._run_student_concurrent_tests()

        #获取预警报告
        await self._get_warning_report()

        self.logger.info("=== 完整测试流程结束 ===")
        return True
    
    async def _admin_publish_evaluation(self) -> Union[str, None, bool]:
        """管理员发布测评"""
        self.logger.info("开始管理员发布测评...")
        self.admin_service = AdminService(self.admin_config.base_url, self.admin_config.debug)
        
        async with aiohttp.ClientSession() as session:
            if not await self.admin_service.admin_login(
                session, self.admin_config.admin_username, self.admin_config.admin_password
            ):
                return False
            
            return await self.admin_service.publish_evaluation(
                session, self.admin_config.task_name, self.admin_config.scale_id
            )
    
    async def _run_student_concurrent_tests(self):
        """执行学生并发测试"""
        self.logger.info("开始学生并发测试...")
        manager = ConcurrentTestManager(
            self.admin_config.base_url, self.concurrent_config
        )
        await manager.run_concurrent_tests(debug=False)

    async def _get_warning_report(self) :
        """获取学生的预警信息"""
        self.logger.info("开始获取预警信息...")
        async with aiohttp.ClientSession() as session:
            await self.admin_service.get_warning_report(session)

