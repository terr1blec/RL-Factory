import json
from ast import literal_eval
from omegaconf import OmegaConf
from envs.tool_manager.qwen3_manager import QwenManager
import os

def log(message):
    # 确保日志目录存在
    log_dir = "/home/ma-user/work/RL-Factory/tmp"
    log_file = os.path.join(log_dir, "draft.log")
    os.makedirs(log_dir, exist_ok=True)
    
    # 写入日志文件
    with open(log_file, "a") as f:
        f.write(f"{message}\n")
    
    # 同时在控制台输出（可选）
    print(message)

def parse_mcp_tools_config(file_path):
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        # 使用 literal_eval 安全地解析 Python 字面量
        data = literal_eval(content)
        return data
    except Exception as e:
        log(f"解析错误: {e}")
        return None

def create_qwen_manager_with_tools():
    """创建QwenManager实例并加载工具配置"""
    # 创建配置
    config = {
        'config_path': "/home/ma-user/work/RL-Factory/envs/configs/data_process.pydata",
        'mcp_mode': 'stdio',  # 或者 'sse'
        'enable_limiter': False,
        'enable_thinking': False,
        'tool_name_selected': [],
        'parallel_sse_tool_call': {
            'is_enabled': False,
            'num_instances': 1
        }
    }
    
    # 转换为OmegaConf对象
    verl_config = OmegaConf.create(config)
    
    # 创建QwenManager实例
    manager = QwenManager(verl_config)
    
    log(f"已加载工具数量: {len(manager.all_tools)}")
    log(f"可用工具列表: {list(manager.all_tools.keys())}")
    
    return manager

def execute_tool_example(manager, tool_name, args):
    """执行工具的示例函数"""
    try:
        # 构造工具调用格式
        response_content = f"""
<tool_call>
{{"name": "{tool_name}", "arguments": {json.dumps(args, ensure_ascii=False)}}}
</tool_call>
"""
        
        # 使用manager执行工具
        actions, results = manager.execute_actions([response_content])
        
        log(f"执行动作: {actions}")
        log(f"执行结果: {results}")
        
        return results
    except Exception as e:
        log(f"工具执行失败: {e}")
        return None

if __name__ == "__main__":
    # 创建管理器并加载工具
    manager = create_qwen_manager_with_tools()
    if "file_system-load_scenario" in manager.all_tools:
        log("\n执行file_system-load_scenario工具示例:")
        scenario_config = {
            "root": {
                "workspace": {
                    "type": "directory", 
                    "contents": {
                        "document": {
                            "type": "directory", 
                            "contents": {
                                "final_report.pdf": {
                                    "type": "file", 
                                    "content": "Year2024 This is the final report content including budget analysis and other sections."
                                }, 
                                "previous_report.pdf": {
                                    "type": "file", 
                                    "content": "Year2023 This is the previous report content with different budget analysis."
                                }
                            }
                        }, 
                        "archive": {
                            "type": "directory", 
                            "contents": {}
                        }
                    }
                }
            }
        }
        execute_tool_example(manager, 'file_system-load_scenario', {"scenario": scenario_config})
    
    # 示例1：执行文件系统ls工具
    if 'file_system-ls' in manager.all_tools:
        log("\n执行file_system-ls工具示例:")
        execute_tool_example(manager, 'file_system-ls', {'show_hidden': False})
    
    # 示例2：执行pwd工具
    if 'file_system-pwd' in manager.all_tools:
        log("\n执行file_system-pwd工具示例:")
        execute_tool_example(manager, 'file_system-pwd', {})
    
    # 示例3：切换到document目录
    if 'file_system-cd' in manager.all_tools:
        log("\n执行file_system-cd工具示例（切换到document目录）:")
        execute_tool_example(manager, 'file_system-cd', {'folder': 'document'})
    
    # 示例4：再次列出目录内容
    if 'file_system-ls' in manager.all_tools:
        log("\n再次执行file_system-ls工具:")
        execute_tool_example(manager, 'file_system-ls', {'show_hidden': False})
    
    # 示例5：执行cat工具读取文件
    if 'file_system-cat' in manager.all_tools:
        log("\n执行file_system-cat工具示例:")
        execute_tool_example(manager, 'file_system-cat', {'file_name': 'final_report.pdf'})
    


    # 测试Message工具的scenario保存和加载一致性
    log("\n" + "="*50)
    log("开始测试Message工具的scenario保存和加载一致性")
    log("="*50)
    
    # 测试1：加载空scenario
    if 'message-load_scenario' in manager.all_tools:
        log("\n测试1：加载空scenario")
        empty_scenario = {}
        result1 = execute_tool_example(manager, 'message-load_scenario', {"scenario": empty_scenario, "long_context": False})
        log(f"空scenario加载结果: {result1}")
    
    # 测试2：保存当前scenario
    if 'message-save_scenario' in manager.all_tools:
        log("\n测试2：保存当前scenario")
        result2 = execute_tool_example(manager, 'message-save_scenario', {})
        log(f"保存scenario结果: {result2}")
        
        # 提取保存的scenario数据
        if result2 and len(result2) > 0:
            saved_scenario_str = result2[0] if isinstance(result2, list) else str(result2)
            log(f"保存的scenario字符串: {saved_scenario_str}")
    
    # 测试3：执行一些操作改变状态
    if 'message-add_contact' in manager.all_tools:
        log("\n测试3：添加新联系人改变状态")
        result3 = execute_tool_example(manager, 'message-add_contact', {"user_name": "TestUser"})
        log(f"添加联系人结果: {result3}")
    
    if 'message-message_login' in manager.all_tools:
        log("\n测试4：登录用户")
        result4 = execute_tool_example(manager, 'message-message_login', {"user_id": "USR001"})
        log(f"登录结果: {result4}")
    
    if 'message-send_message' in manager.all_tools:
        log("\n测试5：发送消息")
        result5 = execute_tool_example(manager, 'message-send_message', {"receiver_id": "USR002", "message": "Hello from test!"})
        log(f"发送消息结果: {result5}")
    
    # 测试6：再次保存scenario
    if 'message-save_scenario' in manager.all_tools:
        log("\n测试6：再次保存scenario（包含新状态）")
        result6 = execute_tool_example(manager, 'message-save_scenario', {})
        log(f"第二次保存scenario结果: {result6}")
    
    # 测试7：重新加载空scenario（重置状态）
    if 'message-load_scenario' in manager.all_tools:
        log("\n测试7：重新加载空scenario（重置状态）")
        empty_scenario = {}
        result7 = execute_tool_example(manager, 'message-load_scenario', {"scenario": empty_scenario, "long_context": False})
        log(f"重新加载空scenario结果: {result7}")
    
    # 测试8：验证状态是否重置
    if 'message-list_users' in manager.all_tools:
        log("\n测试8：验证用户列表（应该回到默认状态）")
        result8 = execute_tool_example(manager, 'message-list_users', {})
        log(f"用户列表: {result8}")
    
    if 'message-view_messages_sent' in manager.all_tools:
        log("\n测试9：验证发送的消息（应该回到默认状态）")
        result9 = execute_tool_example(manager, 'message-view_messages_sent', {})
        log(f"发送的消息: {result9}")
    
    # 测试10：最终保存并比较
    if 'message-save_scenario' in manager.all_tools:
        log("\n测试10：最终保存scenario（应该与第一次保存一致）")
        result10 = execute_tool_example(manager, 'message-save_scenario', {})
        log(f"最终保存scenario结果: {result10}")
        
        # 比较两次保存的结果
        if 'result2' in locals() and result10:
            log(f"\n比较结果:")
            log(f"第一次保存: {result2}")
            log(f"最终保存: {result10}")
            if str(result2) == str(result10):
                log("✅ 两次保存结果完全一致！")
            else:
                log("❌ 两次保存结果不一致！")
    
    log("\n" + "="*50)
    log("Message工具scenario测试完成")
    log("="*50)

    # 测试Posting工具的scenario保存和加载一致性
    log("\n" + "="*50)
    log("开始测试Posting工具的scenario保存和加载一致性")
    log("="*50)

    # 测试P-1：加载空scenario（应回到默认）
    if 'posting-load_scenario' in manager.all_tools:
        log("\n测试P-1：加载空scenario")
        empty_scenario = {}
        presult1 = execute_tool_example(manager, 'posting-load_scenario', {"scenario": empty_scenario, "long_context": False})
        log(f"空scenario加载结果: {presult1}")

    # 测试P-2：保存当前scenario（基线）
    if 'posting-save_scenario' in manager.all_tools:
        log("\n测试P-2：保存当前scenario（基线）")
        presult2 = execute_tool_example(manager, 'posting-save_scenario', {})
        log(f"保存scenario结果: {presult2}")

    # 测试P-3：执行操作改变状态（登录、发推）
    if 'posting-authenticate_twitter' in manager.all_tools:
        log("\n测试P-3：登录默认用户john/john123")
        presult3 = execute_tool_example(manager, 'posting-authenticate_twitter', {"username": "john", "password": "john123"})
        log(f"登录结果: {presult3}")

    if 'posting-post_tweet' in manager.all_tools:
        log("\n测试P-4：发一条推文")
        presult4 = execute_tool_example(manager, 'posting-post_tweet', {"content": "hello from posting test", "tags": ["#test"], "mentions": ["@alice"]})
        log(f"发推结果: {presult4}")

    # 测试P-5：再次保存scenario（包含新状态）
    if 'posting-save_scenario' in manager.all_tools:
        log("\n测试P-5：再次保存scenario（包含新状态）")
        presult5 = execute_tool_example(manager, 'posting-save_scenario', {})
        log(f"第二次保存scenario结果: {presult5}")

    # 测试P-6：重新加载空scenario（重置状态）
    if 'posting-load_scenario' in manager.all_tools:
        log("\n测试P-6：重新加载空scenario（重置状态）")
        empty_scenario = {}
        presult6 = execute_tool_example(manager, 'posting-load_scenario', {"scenario": empty_scenario, "long_context": False})
        log(f"重新加载空scenario结果: {presult6}")

    # 测试P-7：验证登录状态应为未登录
    if 'posting-posting_get_login_status' in manager.all_tools:
        log("\n测试P-7：验证登录状态（应未登录）")
        presult7 = execute_tool_example(manager, 'posting-posting_get_login_status', {})
        log(f"登录状态: {presult7}")

    # 测试P-8：最终保存并与P-2比较（应一致）
    if 'posting-save_scenario' in manager.all_tools:
        log("\n测试P-8：最终保存scenario（应与P-2一致）")
        presult8 = execute_tool_example(manager, 'posting-save_scenario', {})
        log(f"最终保存scenario结果: {presult8}")

        if 'presult2' in locals() and presult8:
            log("\n比较结果(Posting):")
            log(f"第一次保存: {presult2}")
            log(f"最终保存: {presult8}")
            if str(presult2) == str(presult8):
                log("✅ Posting 两次保存结果完全一致！")
            else:
                log("❌ Posting 两次保存结果不一致！")

    #
    # 测试Ticket工具的scenario保存和加载一致性
    log("\n" + "="*50)
    log("开始测试Ticket工具的scenario保存和加载一致性")
    log("="*50)
    # T-1：加载空scenario（应回到默认）
    if 'ticket-load_scenario' in manager.all_tools:
        log("\n测试T-1：加载空scenario")
        empty_scenario = {}
        tresult1 = execute_tool_example(manager, 'ticket-load_scenario', {"scenario": empty_scenario, "long_context": False})
        log(f"空scenario加载结果: {tresult1}")

    # T-2：保存当前scenario（基线）
    if 'ticket-save_scenario' in manager.all_tools:
        log("\n测试T-2：保存当前scenario（基线）")
        tresult2 = execute_tool_example(manager, 'ticket-save_scenario', {})
        log(f"保存scenario结果: {tresult2}")

    # T-3：登录并创建两个工单
    if 'ticket-ticket_login' in manager.all_tools:
        log("\n测试T-3：登录ticket系统用户")
        tresult3 = execute_tool_example(manager, 'ticket-ticket_login', {"username": "tester", "password": "pwd"})
        log(f"登录结果: {tresult3}")

    if 'ticket-create_ticket' in manager.all_tools:
        log("\n测试T-4：创建两个工单")
        tresult4a = execute_tool_example(manager, 'ticket-create_ticket', {"title": "Bug: cannot login", "description": "login page error", "priority": 3})
        log(f"创建工单结果1: {tresult4a}")
        tresult4b = execute_tool_example(manager, 'ticket-create_ticket', {"title": "Feature: dark mode", "description": "add dark theme", "priority": 2})
        log(f"创建工单结果2: {tresult4b}")

    # T-5：关闭第一个工单并解决第二个
    if 'ticket-close_ticket' in manager.all_tools:
        log("\n测试T-5：关闭第一个工单(1)")
        tresult5a = execute_tool_example(manager, 'ticket-close_ticket', {"ticket_id": 1})
        log(f"关闭结果: {tresult5a}")
    if 'ticket-resolve_ticket' in manager.all_tools:
        log("\n测试T-6：解决第二个工单(2)")
        tresult5b = execute_tool_example(manager, 'ticket-resolve_ticket', {"ticket_id": 2, "resolution": "implemented"})
        log(f"解决结果: {tresult5b}")

    # T-7：再次保存scenario（包含新状态）
    if 'ticket-save_scenario' in manager.all_tools:
        log("\n测试T-7：再次保存scenario（包含新状态）")
        tresult7 = execute_tool_example(manager, 'ticket-save_scenario', {})
        log(f"第二次保存scenario结果: {tresult7}")

    # T-8：重新加载空scenario（重置状态）
    if 'ticket-load_scenario' in manager.all_tools:
        log("\n测试T-8：重新加载空scenario（重置状态）")
        empty_scenario = {}
        tresult8 = execute_tool_example(manager, 'ticket-load_scenario', {"scenario": empty_scenario, "long_context": False})
        log(f"重新加载空scenario结果: {tresult8}")

    # T-9：验证登录状态应为未登录
    if 'ticket-ticket_get_login_status' in manager.all_tools:
        log("\n测试T-9：验证登录状态（应未登录）")
        tresult9 = execute_tool_example(manager, 'ticket-ticket_get_login_status', {})
        log(f"登录状态: {tresult9}")

    # T-10：最终保存并与T-2比较（应一致）
    if 'ticket-save_scenario' in manager.all_tools:
        log("\n测试T-10：最终保存scenario（应与T-2一致）")
        tresult10 = execute_tool_example(manager, 'ticket-save_scenario', {})
        log(f"最终保存scenario结果: {tresult10}")
        if 'tresult2' in locals() and tresult10:
            log("\n比较结果(Ticket):")
            log(f"第一次保存: {tresult2}")
            log(f"最终保存: {tresult10}")
            if str(tresult2) == str(tresult10):
                log("✅ Ticket 两次保存结果完全一致！")
            else:
                log("❌ Ticket 两次保存结果不一致！")

    log("\n" + "="*50)
    log("Ticket工具scenario测试完成")
    log("="*50)


    log("="*50)
    
    # 测试Trading工具的scenario保存和加载一致性
    log("\n" + "="*50)
    log("开始测试Trading工具的scenario保存和加载一致性")
    log("="*50)
    
    # T-1：加载空scenario
    if 'trading-load_scenario' in manager.all_tools:
        log("\n测试T-1：加载空scenario")
        empty_scenario = {}
        tresult1 = execute_tool_example(manager, 'trading-load_scenario', {"scenario": empty_scenario, "long_context": False})
        log(f"空scenario加载结果: {tresult1}")
    
    # T-2：保存当前scenario（基线）
    if 'trading-save_scenario' in manager.all_tools:
        log("\n测试T-2：保存当前scenario（基线）")
        tresult2 = execute_tool_example(manager, 'trading-save_scenario', {})
        log(f"保存scenario结果: {tresult2}")
    
    # T-3：登录并执行操作
    if 'trading-trading_login' in manager.all_tools:
        log("\n测试T-3：登录trading系统")
        tresult3 = execute_tool_example(manager, 'trading-trading_login', {"username": "trader", "password": "pass123"})
        log(f"登录结果: {tresult3}")
    
    if 'trading-place_order' in manager.all_tools:
        log("\n测试T-4：下一个订单")
        tresult4 = execute_tool_example(manager, 'trading-place_order', {"order_type": "Buy", "symbol": "AAPL", "price": 150.0, "amount": 10})
        log(f"下单结果: {tresult4}")
    
    # T-5：再次保存scenario（包含新状态）
    if 'trading-save_scenario' in manager.all_tools:
        log("\n测试T-5：再次保存scenario（包含新状态）")
        tresult5 = execute_tool_example(manager, 'trading-save_scenario', {})
        log(f"第二次保存scenario结果: {tresult5}")
    
    # T-6：重新加载空scenario（重置状态）
    if 'trading-load_scenario' in manager.all_tools:
        log("\n测试T-6：重新加载空scenario（重置状态）")
        empty_scenario = {}
        tresult6 = execute_tool_example(manager, 'trading-load_scenario', {"scenario": empty_scenario, "long_context": False})
        log(f"重新加载空scenario结果: {tresult6}")
    
    # T-7：验证登录状态应为未登录
    if 'trading-trading_get_login_status' in manager.all_tools:
        log("\n测试T-7：验证登录状态（应未登录）")
        tresult7 = execute_tool_example(manager, 'trading-trading_get_login_status', {})
        log(f"登录状态: {tresult7}")
    
    # T-8：最终保存并与T-2比较（应一致）
    if 'trading-save_scenario' in manager.all_tools:
        log("\n测试T-8：最终保存scenario（应与T-2一致）")
        tresult8 = execute_tool_example(manager, 'trading-save_scenario', {})
        log(f"最终保存scenario结果: {tresult8}")
        if 'tresult2' in locals() and tresult8:
            log("\n比较结果(Trading):")
            log(f"第一次保存: {tresult2}")
            log(f"最终保存: {tresult8}")
            if str(tresult2) == str(tresult8):
                log("✅ Trading 两次保存结果完全一致！")
            else:
                log("❌ Trading 两次保存结果不一致！")
    
    log("\n" + "="*50)
    log("Trading工具scenario测试完成")
    log("="*50)
    log("="*50)
    
    # 测试Travel工具的scenario保存和加载一致性
    log("\n" + "="*50)
    log("开始测试Travel工具的scenario保存和加载一致性")
    log("="*50)
    
    # T-1：加载空scenario
    if 'travel-load_scenario' in manager.all_tools:
        log("\n测试T-1：加载空scenario")
        empty_scenario = {}
        tresult1 = execute_tool_example(manager, 'travel-load_scenario', {"scenario": empty_scenario, "long_context": False})
        log(f"空scenario加载结果: {tresult1}")
    
    # T-2：保存当前scenario（基线）
    if 'travel-save_scenario' in manager.all_tools:
        log("\n测试T-2：保存当前scenario（基线）")
        tresult2 = execute_tool_example(manager, 'travel-save_scenario', {})
        log(f"保存scenario结果: {tresult2}")
    
    # T-3：登录并执行操作
    if 'travel-authenticate_travel' in manager.all_tools:
        log("\n测试T-3：登录travel系统")
        tresult3 = execute_tool_example(manager, 'travel-authenticate_travel', {
            "client_id": "client123", 
            "client_secret": "secret123", 
            "refresh_token": "refresh123", 
            "grant_type": "read_write", 
            "user_first_name": "John", 
            "user_last_name": "Doe"
        })
        log(f"登录结果: {tresult3}")
    
    if 'travel-register_credit_card' in manager.all_tools:
        log("\n测试T-4：注册信用卡")
        tresult4 = execute_tool_example(manager, 'travel-register_credit_card', {
            "access_token": "123456", 
            "card_number": "4111111111111111", 
            "expiration_date": "12/2025", 
            "cardholder_name": "John Doe", 
            "card_verification_number": 123
        })
        log(f"注册结果: {tresult4}")
    
    # T-5：再次保存scenario（包含新状态）
    if 'travel-save_scenario' in manager.all_tools:
        log("\n测试T-5：再次保存scenario（包含新状态）")
        tresult5 = execute_tool_example(manager, 'travel-save_scenario', {})
        log(f"第二次保存scenario结果: {tresult5}")
    
    # T-6：重新加载空scenario（重置状态）
    if 'travel-load_scenario' in manager.all_tools:
        log("\n测试T-6：重新加载空scenario（重置状态）")
        empty_scenario = {}
        tresult6 = execute_tool_example(manager, 'travel-load_scenario', {"scenario": empty_scenario, "long_context": False})
        log(f"重新加载空scenario结果: {tresult6}")
    
    # T-7：验证登录状态应为未登录
    if 'travel-travel_get_login_status' in manager.all_tools:
        log("\n测试T-7：验证登录状态（应未登录）")
        tresult7 = execute_tool_example(manager, 'travel-travel_get_login_status', {})
        log(f"登录状态: {tresult7}")
    
    # T-8：最终保存并与T-2比较（应一致）
    if 'travel-save_scenario' in manager.all_tools:
        log("\n测试T-8：最终保存scenario（应与T-2一致）")
        tresult8 = execute_tool_example(manager, 'travel-save_scenario', {})
        log(f"最终保存scenario结果: {tresult8}")
        if 'tresult2' in locals() and tresult8:
            log("\n比较结果(Travel):")
            log(f"第一次保存: {tresult2}")
            log(f"最终保存: {tresult8}")
            if str(tresult2) == str(tresult8):
                log("✅ Travel 两次保存结果完全一致！")
            else:
                log("❌ Travel 两次保存结果不一致！")
    
    log("\n" + "="*50)
    log("Travel工具scenario测试完成")
    log("="*50)

    log("="*50)
    
    # 测试Vehicle工具的scenario保存和加载一致性
    log("\n" + "="*50)
    log("开始测试Vehicle工具的scenario保存和加载一致性")
    log("="*50)
    
    # T-1：加载空scenario
    if 'vehicle-load_scenario' in manager.all_tools:
        log("\n测试T-1：加载空scenario")
        empty_scenario = {}
        tresult1 = execute_tool_example(manager, 'vehicle-load_scenario', {"scenario": empty_scenario, "long_context": False})
        log(f"空scenario加载结果: {tresult1}")
    
    # T-2：保存当前scenario（基线）
    if 'vehicle-save_scenario' in manager.all_tools:
        log("\n测试T-2：保存当前scenario（基线）")
        tresult2 = execute_tool_example(manager, 'vehicle-save_scenario', {})
        log(f"保存scenario结果: {tresult2}")    
