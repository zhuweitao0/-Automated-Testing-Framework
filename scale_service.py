import aiohttp
import random
from typing import List, Dict, Any
from api_client import APIClient

class ScaleService(APIClient):
    """
    问卷服务类
    
    负责问卷相关的操作，包括生成随机答案、提交答案和获取测评报告
    """
    
    def __init__(self, base_url: str, auth_service, task_service, debug: bool = True):
        """
        初始化问卷服务
        
        Args:
            base_url: API服务器基础URL
            auth_service: 认证服务实例
            task_service: 任务服务实例
            debug: 是否开启调试模式
        """
        super().__init__(base_url, debug)
        self.auth_service = auth_service
        self.task_service = task_service
    
    def generate_random_answers(self, option_vo_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        为问卷生成随机答案
        
        Args:
            option_vo_list: 问卷选项列表，每个元素包含题目和选项信息
            
        Returns:
            List[Dict]: 生成的答案列表
        """
        answers = []
        for i, option_vo in enumerate(option_vo_list):
            # 获取当前题目的所有选项
            question_options = option_vo['questionOptionScoreList']
            # 随机选择一个选项
            selected_option = random.choice(question_options)
            
            # 构造答案格式
            answers.append({
                'contentOptions': selected_option['contentOptions'],  # 选项内容
                'scoring': str(selected_option['scoring']),           # 选项分数
                'subscript': str(selected_option.get('subscript', i)) # 题目下标
            })
        return answers
    
    async def submit_scale_answers(self, session: aiohttp.ClientSession, 
                                 scale_id: str, answers: List[Dict[str, Any]]) -> bool:
        """
        提交问卷答案
        
        Args:
            session: aiohttp会话对象
            scale_id: 问卷ID
            answers: 答案列表
            
        Returns:
            bool: 提交是否成功
        """
        # 设置请求头
        headers = {'Content-Type': 'application/json'}
        headers.update(self.auth_service.get_auth_headers())
        
        # 构造提交数据
        submit_data = {
            'createBy': self.task_service.create_by,           # 任务创建者
            'emotionalVos': [],                                # 情感数据（空）
            'eyeMoveData': '',                                 # 眼动数据（空）
            'questionOptionScoreList': answers,               # 问卷答案
            'resourceUrls': '',                                # 资源URL（空）
            'scaleId': scale_id,                              # 问卷ID
            'taskId': self.task_service.task_id,              # 任务ID
            'useTime': '00:07:033',                           # 用时（固定值）
            'userId': self.auth_service.user_id               # 用户ID
        }
        
        # 发送提交请求
        status, data = await self._make_request(session, "POST", "/jeecg-boot/api/getResult", 
                                              headers=headers, data=submit_data)
        self.log_response("提交问卷答案", f"{self.base_url}/jeecg-boot/api/getResult", status, data)
        
        # 检查提交结果
        if status == 200 and data.get('success'):
            return True

        
        self.logger.error(f"提交答案失败: {data}")
        return False
    
    async def get_report(self, session: aiohttp.ClientSession, scale_id: str) -> bool:
        """
        获取测评报告
        
        Args:
            session: aiohttp会话对象
            scale_id: 问卷ID
            
        Returns:
            bool: 获取是否成功
        """
        # 获取认证头
        headers = self.auth_service.get_auth_headers()
        
        # 构造报告请求数据
        report_data = {
            "taskId": str(self.task_service.task_id),    # 任务ID
            "stuId": str(self.auth_service.user_id),     # 学生ID
            "scaleId": str(scale_id)                     # 问卷ID
        }
        
        # 发送获取报告请求
        status, data = await self._make_request(session, "POST", "/jeecg-boot/api/getReportUserInfo", 
                                              headers=headers, data=report_data)
        self.log_response("获取测评报告", f"{self.base_url}/jeecg-boot/api/getReportUserInfo", status, data)
        
        return status == 200