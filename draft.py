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
    
    # 获取特定工具的详细信息
    tool = manager.get_tool('file_system-ls')
    if tool:
        log(f"\n获取到工具: {tool.name}")
        log(f"工具描述: {tool.function}")
    else:
        log("未找到指定工具")
    
    # 显示所有可用工具的功能描述
    log("\n所有工具的功能描述:")
    for tool_name, tool_obj in manager.all_tools.items():
        log(f"- {tool_name}: {tool_obj.function.get('description', 'No description')}")