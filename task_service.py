import aiohttp
from typing import List, Dict, Any, Optional
from api_client import APIClient

class TaskService(APIClient):
    """
    任务服务类
    
    负责获取和管理学生的测评任务，包括任务列表和问卷信息
    """
    
    def __init__(self, base_url: str, auth_service, debug: bool = False):
        """
        初始化任务服务
        
        Args:
            base_url: API服务器基础URL
            auth_service: 认证服务实例，用于获取认证信息
            debug: 是否开启调试模式
        """
        super().__init__(base_url, debug)
        self.auth_service = auth_service
        self.task_id: Optional[str] = None              # 当前任务ID
        self.create_by: Optional[str] = None            # 任务创建者ID
        self.scale_list: List[Dict[str, Any]] = []      # 问卷列表
    
    async def get_student_tasks(self, session: aiohttp.ClientSession) -> bool:
        """
        获取学生任务列表
        
        Args:
            session: aiohttp会话对象
            
        Returns:
            bool: 是否成功获取任务
        """
        # 获取认证头信息
        headers = self.auth_service.get_auth_headers()
        # 构造请求端点，包含用户ID
        endpoint = f"/jeecg-boot/api/isUserHasTask/{self.auth_service.user_id}"
        
        # 发送获取任务请求
        status, data = await self._make_request(session, "GET", endpoint, headers=headers)
        self.log_response("获取任务列表", f"{self.base_url}{endpoint}", status, data)
        
        # 检查HTTP状态码
        if status != 200:
            self.logger.error(f"获取任务失败: {status}")
            return False
        
        # 检查是否有可用任务
        if data.get('success') and data.get('isHaveTask') and data.get('result'):
            if len(data['result']) > 0:
                # 获取第一个任务的信息
                task_info = data['result'][0]
                self.task_id = task_info['evaluation']['id']
                self.create_by = task_info['evaluation']['createBy']
                self.scale_list = task_info['scaleList']
                
                # 记录任务信息
                self.logger.info(f"获取到任务: {task_info['evaluation']['taskName']}")
                self.logger.info(f"创建者: {self.create_by}, 包含 {len(self.scale_list)} 个问卷")
                return True
            else:
                self.logger.warning("任务列表为空")
                return False
        else:
            self.logger.warning("暂无可用任务")
            return False