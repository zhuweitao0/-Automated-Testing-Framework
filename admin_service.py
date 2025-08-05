import aiohttp
import time
from typing import Optional, Dict, Any, Tuple, Coroutine, Union

from Tools.scripts.generate_opcode_h import header

from api_client import APIClient

class AdminService(APIClient):
    """管理员服务类 - 负责管理员登录和测评发布"""
    
    def __init__(self, base_url: str, debug: bool = False):
        super().__init__(base_url, debug)
        self.admin_token: Optional[str] = None
        self.admin_id: Optional[str] = None

    def _generate_timestamp(self) -> int:
        """生成时间戳"""
        return int(time.time() * 1000)

    async def _get_captcha(self, session: aiohttp.ClientSession) -> Optional[Dict[str, Any]]:
        """获取验证码"""
        timestamp = self._generate_timestamp()
        captcha_url = f"/jeecg-boot/sys/randomImage/{timestamp}?_t={int(time.time())}"

        status, data = await self._make_request(session, "GET", captcha_url)
        self.log_response("获取验证码", f"{self.base_url}{captcha_url}", status, data)

        if status == 200 and data.get('success'):
            return {
                'captcha': data.get('message', ''),
                'checkKey': timestamp
            }
        return None

    async def admin_login(self, session: aiohttp.ClientSession,
                         username: str, password: str) -> bool:
        """管理员登录"""
        # 步骤1: 获取验证码
        captcha_info = await self._get_captcha(session)
        if not captcha_info:
            self.logger.error("获取验证码失败")
            return False

        # 步骤2: 使用验证码登录
        login_data = {
            "username": username,
            "password": password,
            "captcha": captcha_info['captcha'],
            "checkKey": captcha_info['checkKey'],
            "remember_me": True
        }

        status, data = await self._make_request(
            session, "POST", "/jeecg-boot/sys/login", data=login_data
        )
        self.log_response("管理员登录", f"{self.base_url}/jeecg-boot/sys/login", status, data)

        if status == 200 and data.get('success'):
            result = data.get('result', {})
            self.admin_token = result.get('token')
            # 假设管理员信息在userInfo中
            user_info = result.get('userInfo', {})
            self.admin_id = user_info.get('id')
            self.logger.info(f"管理员登录成功: {username}")
            return True
        else:
            self.logger.error(f"管理员登录失败: {data.get('message', '未知错误')}")
            return False



    async def _get_students(self, session: aiohttp.ClientSession) -> Optional[Dict[str, Any]]:
        """发布任务之前先获取到需要的学生编号"""
        timestamp = self._generate_timestamp()
        """获取当前时间戳"""
        Stu_Id_url=f"/jeecg-boot/cp/userArchives/treeQuery?_t={timestamp}&idArr=1947194708543455234&createBy=testAdmin&level=2&order=desc&version=1&field=id,,account,userName,age,sex_dictText,school_dictText,grade_dictText,form_dictText&pageNo=1&pageSize=1000"
        """添加认证头"""
        headers={"X-Access-Token":  self.admin_token}

        status, data = await self._make_request(session, "GET", Stu_Id_url, headers=headers)

        """打印到控制台"""
        self.log_response("获取学生信息",f"{self.base_url}{Stu_Id_url}", status, data)

        if status == 200 and data.get('success'):
            result = data.get('result', {})
            records = result.get('records', {})
            """提取每个学生id"""
            students_ids = [record["id"] for record in records]
            self.logger.info(f"获取到{len(students_ids)}个学生id")
            return students_ids
        else:
            self.logger.error(f"获取信息失败 {data.get('message','奇奇怪怪的错误')}")
            return None



    async def publish_evaluation(self, session: aiohttp.ClientSession, task_name: str, scale_id: str) -> Optional[bool]:
        """发布测评任务 - 修改为单个问卷"""
        if not self.admin_token:
            self.logger.error("未登录，无法发布测评任务")
            return None
        
        headers = {'X-Access-Token': self.admin_token}
        student_ids = await self._get_students(session)


        scale_list = [{
            "scaleId": scale_id,  # 直接使用传入的scale_id
            "warningType": 0,
            "isView": 1,
            "scaleName": f"问卷_{scale_id}"
        }]

        publish_data = {
            "createBy": "testAdmin",
            "evaluation": {
                "taskName": task_name,
                "taskIntroduction": "自动化发布测试",
                "endTime": "2025-08-22 15:27:13",
                "isViewReport": 1,
                "isEmotion": 0,
                "isHide": 0,
                "startTime": "2025-07-22 15:27:13"
            },
            "identifying": "0",
            "orgIds": [],
            "scaleList": scale_list,  # 只包含一个问卷
            "state": "0",
            "stuIdList": student_ids
        }

        status, data = await self._make_request(
            session, "POST", "/jeecg-boot/cp/evaluation/add",
            headers=headers, data=publish_data
        )

        if status == 200 and data.get('success'):
            self.logger.info(f"测评发布成功: {task_name}")
            return True  # 只需要返回成功状态即可
        else:
            self.logger.error(f"测评发布失败: {data.get('message', '未知错误')}")
            return False



    async def get_warning_report(self, session: aiohttp.ClientSession,) -> None:
        """时间戳"""
        timestamp = self._generate_timestamp()
        """认证头"""

        headers={"X-Access-Token":  self.admin_token}



        """url"""
        Test_Admin_Url=f"/jeecg-boot/index/indexEchartsVo/testAdmin?_t={timestamp}"

        status, data = await self._make_request(session, "GET",Test_Admin_Url , headers=headers)

        """打印到控制台"""
        #self.log_response("获取学生预警信息", f"{self.base_url}{Test_Admin_Url}", status, data)

        if status == 200 and data.get('success'):
            result = data.get('result', {})
            waringSumCount = result.get('waringSumCount')
            dayWaringCount = result.get('dayWaringCount')
            interveneCountMap = result.get('interveneCountMap',{})
            self.logger.info(f"总警告数：{waringSumCount}  今日预警数：{dayWaringCount}   处理情况 {interveneCountMap}")

        else:
             self.logger.error(f"获取预警信息失败 {data.get('message', '奇奇怪怪的错误')}")