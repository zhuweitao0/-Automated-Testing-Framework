import asyncio
from config import TestConfig, ConcurrentTestConfig, AdminConfig
from test_runner import TestRunner
from concurrent_test_manager import ConcurrentTestManager
from full_test_manager import FullTestManager

async def run_single_test():
    """
    运行单个用户测试的示例函数
    
    用于测试单个用户的完整流程，便于调试和验证功能
    """
    # 创建测试配置
    config = TestConfig(
        base_url="http://localhost:8999/",  # API服务器地址
        username="test0018",                               # 测试用户名
        password="123456",                                 # 测试密码
        debug=True                                         # 开启调试模式，显示详细日志
    )
    
    # 创建并运行测试
    runner = TestRunner(config)
    success = await runner.run_test()
    
    # 输出测试结果
    if success:
        print("测试完成")
    else:
        print("测试失败")

async def run_concurrent_test():
    """
    运行并发测试的示例函数
    
    用于执行大规模并发测试，模拟多用户同时访问系统
    """
    # 创建并发测试配置
    concurrent_config = ConcurrentTestConfig(user_count=1000)  # 1000个并发用户（最高优先级）
    
    # 创建并发测试管理器
    manager = ConcurrentTestManager(
        base_url="http://localhost:8999/",  # API服务器地址
        concurrent_config=concurrent_config
    )
    
    # 执行并发测试（关闭调试模式以提高性能）
    await manager.run_concurrent_tests(debug=False)

async def run_full_flow_test():
    """运行完整流程测试：管理员发布 + 学生并发测试"""
    admin_config = AdminConfig(
        base_url="http://localhost:8999/",
        admin_username="testAdmin",
        admin_password="testAdmin@2025",
        task_name="1000并发自动化测评",
        scale_id="1571395659305803777",  # 改为单个问卷ID，优先级最高
        debug=False
    )
    
    # 并发测试配置
    concurrent_config = ConcurrentTestConfig(user_count=1000)
    
    # 创建完整流程管理器
    full_manager = FullTestManager(admin_config, concurrent_config)
    
    # 执行完整流程
    success = await full_manager.run_full_test_flow()
    
    if success:
        print("完整流程测试成功")
    else:
        print("完整流程测试失败")

async def main():
    """
    主函数，程序入口点
    
    可以选择运行不同类型的测试
    """
    # 运行完整流程测试（管理员发布 + 学生并发测试）
    await run_full_flow_test()
    
    # 或者运行并发测试
    #await run_concurrent_test()
    
    # 或者运行单个测试（用于调试）
    # await run_single_test()

if __name__ == '__main__':
    asyncio.run(main())