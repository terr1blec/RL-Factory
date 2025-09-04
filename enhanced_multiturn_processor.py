#!/usr/bin/env python3
"""
增强的多轮对话处理器 - 包含真实历史调用轨迹
基于save_scenario和load_scenario功能，生成真实的工具调用历史
"""

import json
import csv
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from omegaconf import OmegaConf
from envs.tool_manager.qwen3_manager import QwenManager

class EnhancedMultiTurnProcessor:
    """增强的多轮对话处理器，生成真实的工具调用轨迹"""
    
    def __init__(self):
        # 函数名映射：从旧格式到新格式
        self.function_mapping = {
            # FileSystem相关
            'ls': 'file_system-ls',
            'pwd': 'file_system-pwd', 
            'cd': 'file_system-cd',
            'mkdir': 'file_system-mkdir',
            'touch': 'file_system-touch',
            'echo': 'file_system-echo',
            'cat': 'file_system-cat',
            'rm': 'file_system-rm',
            'mv': 'file_system-mv',
            'cp': 'file_system-cp',
            'find': 'file_system-find',
            'grep': 'file_system-grep',
            'tail': 'file_system-tail',
            'diff': 'file_system-diff',
            'wc': 'file_system-wc',
            'sort': 'file_system-sort',
            'du': 'file_system-du',
            'rmdir': 'file_system-rmdir',
            'load_scenario': 'file_system-load_scenario',
            'save_scenario': 'file_system-save_scenario',
        }
        
        # 参数名映射
        self.param_mapping = {
            'ls': {'a': 'show_hidden'},
            'cd': {'folder': 'folder'},
            'mkdir': {'dir_name': 'dir_name'},
            'touch': {'file_name': 'file_name'},
            'echo': {'content': 'content', 'file_name': 'file_name'},
            'cat': {'file_name': 'file_name'},
            'rm': {'file_name': 'file_name'},
            'mv': {'source': 'source', 'destination': 'destination'},
            'cp': {'source': 'source', 'destination': 'destination'},
            'find': {'path': 'path', 'name': 'name'},
            'grep': {'file_name': 'file_name', 'pattern': 'pattern'},
            'tail': {'file_name': 'file_name', 'lines': 'lines'},
            'diff': {'file_name1': 'file_name1', 'file_name2': 'file_name2'},
        }
        
        self.manager = None
    
    def create_qwen_manager(self):
        """创建QwenManager实例"""
        if self.manager is None:
            config = {
                'config_path': "/home/ma-user/work/RL-Factory/envs/configs/bfcl_mcp_tools.pydata",
                'mcp_mode': 'stdio',
                'enable_limiter': False,
                'enable_thinking': False,
                'tool_name_selected': [],
                'parallel_sse_tool_call': {
                    'is_enabled': False,
                    'num_instances': 1
                }
            }
            
            verl_config = OmegaConf.create(config)
            self.manager = QwenManager(verl_config)
            print(f"已创建QwenManager，加载了{len(self.manager.all_tools)}个工具")
        
        return self.manager
    
    def execute_tool(self, tool_name: str, args: dict) -> dict:
        """执行单个工具并返回结果"""
        response_content = f"""
<tool_call>
{{"name": "{tool_name}", "arguments": {json.dumps(args, ensure_ascii=False)}}}
</tool_call>
"""
        
        try:
            actions, results = self.manager.execute_actions([response_content])
            if results and len(results) > 0:
                return {
                    'success': True,
                    'result': results[0],
                    'action': actions[0] if actions else 'unknown'
                }
            else:
                return {
                    'success': False,
                    'error': 'No results returned'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def parse_function_call(self, call_str: str) -> Tuple[str, dict]:
        """解析函数调用字符串，返回函数名和参数"""
        # 处理类似 "ls(a=True)" 的格式
        if '(' in call_str and ')' in call_str:
            func_name = call_str.split('(')[0].strip()
            params_str = call_str[call_str.find('(')+1:call_str.rfind(')')]
            
            # 解析参数
            params = {}
            if params_str.strip():
                # 简单的参数解析（支持基本类型）
                for param in params_str.split(','):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # 类型转换
                        if value.lower() == 'true':
                            value = True
                        elif value.lower() == 'false':
                            value = False
                        elif value.isdigit():
                            value = int(value)
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        elif value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        
                        params[key] = value
            
            return func_name, params
        else:
            return call_str, {}
    
    def convert_function_call(self, old_call: str) -> Tuple[str, dict]:
        """将旧格式的函数调用转换为新格式"""
        func_name, params = self.parse_function_call(old_call)
        
        # 映射函数名
        new_func_name = self.function_mapping.get(func_name, func_name)
        
        # 映射参数名
        new_params = {}
        if func_name in self.param_mapping:
            param_map = self.param_mapping[func_name]
            for old_key, value in params.items():
                new_key = param_map.get(old_key, old_key)
                new_params[new_key] = value
        else:
            new_params = params
        
        return new_func_name, new_params
    
    def simulate_multi_turn_execution(self, scenario_data: dict, golden_answers: List[List[str]]) -> List[dict]:
        """模拟多轮执行过程，生成真实的调用轨迹"""
        manager = self.create_qwen_manager()
        
        # 加载初始场景
        load_result = self.execute_tool('file_system-load_scenario', {'scenario': scenario_data})
        if not load_result['success']:
            print(f"加载场景失败: {load_result['error']}")
            return []
        
        execution_history = []
        
        # 执行每一轮的golden answers
        for turn_idx, turn_actions in enumerate(golden_answers):
            turn_history = {
                'turn_index': turn_idx,
                'actions': [],
                'scenario_after': None
            }
            
            print(f"\n执行第{turn_idx + 1}轮操作...")
            
            for action_str in turn_actions:
                print(f"  执行: {action_str}")
                
                # 转换函数调用格式
                new_func_name, new_params = self.convert_function_call(action_str)
                
                # 执行工具
                result = self.execute_tool(new_func_name, new_params)
                
                action_record = {
                    'original_call': action_str,
                    'converted_call': f"{new_func_name}({new_params})",
                    'function_name': new_func_name,
                    'parameters': new_params,
                    'execution_result': result,
                    'success': result['success']
                }
                
                turn_history['actions'].append(action_record)
                
                if result['success']:
                    print(f"    成功: {new_func_name}")
                else:
                    print(f"    失败: {result['error']}")
            
            # 保存当前轮结束后的场景状态
            save_result = self.execute_tool('file_system-save_scenario', {})
            if save_result['success']:
                turn_history['scenario_after'] = save_result
                print(f"  第{turn_idx + 1}轮结束，场景已保存")
            
            execution_history.append(turn_history)
        
        return execution_history
    
    def generate_realistic_tool_trace(self, execution_history: List[dict], current_turn: int, questions: List[str]) -> str:
        """基于真实执行历史生成标准对话格式的工具调用轨迹"""
        trace_lines = []
        
        for turn_idx in range(current_turn):
            if turn_idx < len(execution_history):
                turn_data = execution_history[turn_idx]
                
                # 添加用户问题
                if turn_idx < len(questions):
                    trace_lines.append(f"User: {questions[turn_idx]}")
                
                # 添加助手的工具调用
                assistant_calls = []
                for action in turn_data['actions']:
                    func_name = action['function_name']
                    params = action['parameters']
                    tool_call = f'<tool_call>{{"name": "{func_name}", "arguments": {json.dumps(params, ensure_ascii=False)}}}</tool_call>'
                    assistant_calls.append(tool_call)
                
                if assistant_calls:
                    trace_lines.append(f"Assistant: {' '.join(assistant_calls)}")
                
                # 添加工具执行结果
                for action in turn_data['actions']:
                    result = action['execution_result']
                    
                    if result['success'] and 'result' in result:
                        result_content = result['result']
                        if isinstance(result_content, list) and len(result_content) > 0:
                            tool_result = result_content[0]
                            if isinstance(tool_result, dict) and 'content' in tool_result:
                                content = tool_result['content']
                                # 格式化输出内容，保持可读性
                                if len(content) > 300:
                                    trace_lines.append(f"Tool: {content[:300]}...")
                                else:
                                    trace_lines.append(f"Tool: {content}")
                    else:
                        trace_lines.append(f"Tool: Error - {result.get('error', 'Unknown error')}")
                
                trace_lines.append("")  # 轮次之间的分隔
        
        return '\n'.join(trace_lines)
    
    def generate_realistic_tool_trace_with_results(self, execution_history: List[dict], current_turn: int) -> str:
        """基于真实执行历史生成包含结果的工具调用轨迹"""
        trace_lines = []
        
        for turn_idx in range(current_turn):
            if turn_idx < len(execution_history):
                turn_data = execution_history[turn_idx]
                
                # 添加轮次标题
                trace_lines.append(f"Turn {turn_idx + 1} execution:")
                
                for action in turn_data['actions']:
                    func_name = action['function_name']
                    params = action['parameters']
                    result = action['execution_result']
                    
                    # 格式化调用
                    if params:
                        param_strs = []
                        for key, value in params.items():
                            if isinstance(value, str):
                                param_strs.append(f"{key}='{value}'")
                            else:
                                param_strs.append(f"{key}={value}")
                        call_str = f"{func_name}({', '.join(param_strs)})"
                    else:
                        call_str = f"{func_name}()"
                    
                    trace_lines.append(f"  Call: {call_str}")
                    
                    # 添加真实的执行结果
                    if result['success'] and 'result' in result:
                        result_content = result['result']
                        if isinstance(result_content, list) and len(result_content) > 0:
                            # 提取工具执行结果的内容
                            tool_result = result_content[0]
                            if isinstance(tool_result, dict) and 'content' in tool_result:
                                content = tool_result['content']
                                # 简化显示，只显示关键信息
                                if "successed" in content:
                                    # 提取结果部分
                                    if "The result is:" in content:
                                        actual_result = content.split("The result is:")[-1].strip()
                                        trace_lines.append(f"  Result: {actual_result[:100]}{'...' if len(actual_result) > 100 else ''}")
                                    else:
                                        trace_lines.append(f"  Result: Success")
                                else:
                                    trace_lines.append(f"  Result: {content[:100]}{'...' if len(content) > 100 else ''}")
                    else:
                        trace_lines.append(f"  Result: Failed - {result.get('error', 'Unknown error')}")
                
                trace_lines.append("")  # 空行分隔
        
        return '\n'.join(trace_lines)
    
    def extract_scenario_from_save_result(self, save_result: dict) -> dict:
        """从save_scenario结果中提取场景数据"""
        if save_result and save_result.get('success') and 'result' in save_result:
            result_content = save_result['result']
            if isinstance(result_content, list) and len(result_content) > 0:
                tool_result = result_content[0]
                if isinstance(tool_result, dict) and 'content' in tool_result:
                    content = tool_result['content']
                    # 查找 "The result is:" 后面的JSON内容
                    if "The result is:" in content:
                        json_str = content.split("The result is:")[-1].strip()
                        try:
                            return json.loads(json_str)
                        except json.JSONDecodeError as e:
                            print(f"Failed to parse JSON from save_scenario result: {e}")
                            print(f"JSON string: {json_str[:200]}...")
        return None
    
    def process_document_pdf_scenario(self) -> dict:
        """处理document目录中PDF文件操作的多轮场景"""
        # 构建document场景数据
        scenario_data = {
            "root": {
                "user": {
                    "type": "directory",
                    "contents": {
                        "document": {
                            "type": "directory",
                            "contents": {
                                "final_report.pdf": {
                                    "type": "file",
                                    "content": "Executive Summary\nThis report contains comprehensive analysis.\n\nBudget Analysis Section\nTotal budget: $100,000\nSpent: $75,000\nRemaining: $25,000\n\nBudget analysis shows favorable results.\nThe budget analysis indicates strong performance.\n\nConclusion\nProject is on track."
                                },
                                "previous_report.pdf": {
                                    "type": "file",
                                    "content": "Executive Summary\nThis is the previous quarterly report.\n\nBudget Analysis Section\nTotal budget: $90,000\nSpent: $70,000\nRemaining: $20,000\n\nBudget analysis from last quarter.\nThe budget analysis shows different trends.\n\nConclusion\nPrevious quarter results."
                                }
                            }
                        }
                    }
                }
            }
        }
        
        # Golden answers（转换为新格式）
        golden_answers = [
            ["file_system-cd(folder='document')", "file_system-mkdir(dir_name='temp')", "file_system-mv(source='final_report.pdf',destination='temp')"],
            ["file_system-cd(folder='temp')", "file_system-grep(file_name='final_report.pdf',pattern='budget analysis')"],
            ["file_system-sort()"],
            ["file_system-cd(folder='../document')", "file_system-mv(source='previous_report.pdf',destination='temp')", "file_system-cd(folder='temp')", "file_system-diff(file_name1='final_report.pdf',file_name2='previous_report.pdf')"]
        ]
        
        # 问题列表
        questions = [
            "Move 'final_report.pdf' within document directory to 'temp' directory in document. Make sure to create the directory",
            "Perform a detailed search using grep to identify sections in the file pertaining to 'budget analysis'.",
            "Upon identifying the requisite 'budget analysis' content, sort the 'final_report.pdf' by line for improved clarity and comprehension.",
            "Move 'previous_report.pdf' in document directory to temp as well and having final report also there, proceed to juxtapose it with 'previous_report.pdf' to detect any critical alterations."
        ]
        
        print("="*60)
        print("处理document PDF多轮场景")
        print("="*60)
        
        # 模拟执行
        execution_history = self.simulate_multi_turn_execution(scenario_data, golden_answers)
        
        # 生成增强的单轮数据
        enhanced_data = []
        current_scenario = scenario_data  # 初始场景
        
        for turn_idx, question in enumerate(questions):
            # 如果不是第一轮，尝试从前一轮的scenario_after更新场景
            if turn_idx > 0 and turn_idx-1 < len(execution_history):
                prev_turn = execution_history[turn_idx-1]
                if 'scenario_after' in prev_turn and prev_turn['scenario_after']:
                    updated_scenario = self.extract_scenario_from_save_result(prev_turn['scenario_after'])
                    if updated_scenario:
                        current_scenario = updated_scenario
                        print(f"  第{turn_idx+1}轮使用更新后的场景数据")
            
            # 构建真实的工具调用轨迹（现在使用标准对话格式，包含历史）
            tool_trace = ""
            if turn_idx > 0:
                tool_trace = self.generate_realistic_tool_trace(execution_history, turn_idx, questions) + "\n"
            
            # 创建prompt
            prompt_parts = []
            prompt_parts.append("System: # Tools\nYou may call one or more functions to assist with the user query.\nYou are provided with function signatures within <tools></tools> XML tags:\n<tools>\n{\"name\": \"get_weather\", \"description\": \"Get the weather of a city for a specific date.\", \"parameters\": {\" type\": \"object\", \"properties\": {\"city\": {\"type\": \"string\", \"description\": \"The city to get weather for,\nin Chinese.\"}, \"date\": {\"type\": \"string\", \"description\": \"The date in YYYY-MM-DD format.\"}}, \"required\": [\"city\"]}}\n</tools>\nFor each function call, output the function name and arguments within the following XML format:\n<tool_call>{\"name\": \"get_weather\", \"arguments\": {\"city\": \"Beijing\", \"date\": \"2025-08-24\"}}</tool_call>\nYou are a helpful assistant.")
            
            if tool_trace:
                prompt_parts.append(tool_trace)
            
            prompt_parts.append(f"User: {question}")
            
            # 获取当前轮的golden answers
            converted_golden_answers = []
            if turn_idx < len(golden_answers):
                for action_call in golden_answers[turn_idx]:
                    converted_golden_answers.append(action_call)
            
            enhanced_item = {
                "id": f"document_pdf_scenario_turn_{turn_idx}_0_enhanced",
                "question": question,
                "golden_answers": converted_golden_answers,
                "data_source": ["FileSystem"],
                "prompt": "\n".join(prompt_parts),
                "ability": "tool_use",
                "reward_model": "{'final state': {}, 'style': 'rule'}",
                "extra_info": {
                    "initial_config": {"FileSystem": current_scenario},
                    "path": ["GorillaFileSystem.cd", "GorillaFileSystem.mkdir", "GorillaFileSystem.mv", "GorillaFileSystem.grep", "GorillaFileSystem.sort", "GorillaFileSystem.diff"],
                    "original_id": "document_pdf_scenario",
                    "turn_index": turn_idx,
                    "question_index": 0,
                    "execution_history": execution_history[turn_idx] if turn_idx < len(execution_history) else None,
                    "realistic_trace": True
                }
            }
            
            enhanced_data.append(enhanced_item)
        
        return {
            'scenario_data': scenario_data,
            'execution_history': execution_history,
            'enhanced_data': enhanced_data
        }
    
    def process_multi_turn_base_1(self) -> dict:
        """处理multi_turn_base_1示例"""
        # multi_turn_base_1的场景数据
        scenario_data = {
            "root": {
                "alex": {
                    "type": "directory",
                    "contents": {
                        "workspace": {
                            "type": "directory",
                            "contents": {
                                "log.txt": {
                                    "type": "file",
                                    "content": "This is a log file. No errors found. Another line. Yet another line. Error: Something went wrong. Final line."
                                },
                                "archive": {
                                    "type": "directory",
                                    "contents": {}
                                },
                                ".hidden_file": {
                                    "type": "file",
                                    "content": "This is a hidden file."
                                }
                            }
                        }
                    }
                }
            }
        }
        
        # Golden answers（原始格式）
        golden_answers = [
            ["ls(a=True)"],  # Turn 0
            ["cd(folder='workspace')", "mv(source='log.txt',destination='archive')"],  # Turn 1
            ["cd(folder='archive')", "grep(file_name='log.txt',pattern='Error')"],  # Turn 2
            ["tail(file_name='log.txt',lines=20)"]  # Turn 3
        ]
        
        # 问题列表
        questions = [
            "I am alex. Check if the current directory is under my name and list all the visible and hidden contents in the current directory now, please.",
            "Go to workspace directory and move one of the 'log.txt' files into a new directory 'archive'.",
            "Investigate within 'log.txt' for the occurrence of the keyword 'Error'.",
            "Finally, show the last 20 lines the file."
        ]
        
        print("="*60)
        print("处理multi_turn_base_1示例")
        print("="*60)
        
        # 模拟执行
        execution_history = self.simulate_multi_turn_execution(scenario_data, golden_answers)
        
        # 生成增强的单轮数据
        enhanced_data = []
        current_scenario = scenario_data  # 初始场景
        
        for turn_idx, question in enumerate(questions):
            # 如果不是第一轮，尝试从前一轮的scenario_after更新场景
            if turn_idx > 0 and turn_idx-1 < len(execution_history):
                prev_turn = execution_history[turn_idx-1]
                if 'scenario_after' in prev_turn and prev_turn['scenario_after']:
                    updated_scenario = self.extract_scenario_from_save_result(prev_turn['scenario_after'])
                    if updated_scenario:
                        current_scenario = updated_scenario
                        print(f"  第{turn_idx+1}轮使用更新后的场景数据")
            
            # 构建真实的工具调用轨迹（现在使用标准对话格式，包含历史）
            tool_trace = ""
            if turn_idx > 0:
                tool_trace = self.generate_realistic_tool_trace(execution_history, turn_idx, questions) + "\n"
            
            # 创建prompt
            prompt_parts = []
            prompt_parts.append("System: # Tools\nYou may call one or more functions to assist with the user query.\nYou are provided with function signatures within <tools></tools> XML tags:\n<tools>\n{\"name\": \"get_weather\", \"description\": \"Get the weather of a city for a specific date.\", \"parameters\": {\" type\": \"object\", \"properties\": {\"city\": {\"type\": \"string\", \"description\": \"The city to get weather for,\nin Chinese.\"}, \"date\": {\"type\": \"string\", \"description\": \"The date in YYYY-MM-DD format.\"}}, \"required\": [\"city\"]}}\n</tools>\nFor each function call, output the function name and arguments within the following XML format:\n<tool_call>{\"name\": \"get_weather\", \"arguments\": {\"city\": \"Beijing\", \"date\": \"2025-08-24\"}}</tool_call>\nYou are a helpful assistant.")
            
            if tool_trace:
                prompt_parts.append(tool_trace)
            
            prompt_parts.append(f"User: {question}")
            
            # 转换golden answers到新格式
            converted_golden_answers = []
            if turn_idx < len(golden_answers):
                for old_call in golden_answers[turn_idx]:
                    new_func_name, new_params = self.convert_function_call(old_call)
                    converted_golden_answers.append(f"{new_func_name}({json.dumps(new_params, separators=(',', ':'))})")
            
            enhanced_item = {
                "id": f"multi_turn_base_1_turn_{turn_idx}",
                "question": question,
                "golden_answers": converted_golden_answers,
                "data_source": ["FileSystem"],
                "prompt": "\n".join(prompt_parts),
                "ability": "tool_use",
                "reward_model": "{'final state': {}, 'style': 'rule'}",
                "extra_info": {
                    "initial_config": {"FileSystem": current_scenario},
                    "original_id": "multi_turn_base_1",
                    "turn_index": turn_idx,
                }
            }
            
            enhanced_data.append(enhanced_item)
        
        return {
            'scenario_data': scenario_data,
            'execution_history': execution_history,
            'enhanced_data': enhanced_data
        }
    
    def save_enhanced_data(self, enhanced_result: dict, output_file: str):
        """保存增强数据到文件"""
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in enhanced_result['enhanced_data']:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        print(f"增强数据已保存到: {output_file}")
    
    def save_execution_history(self, execution_history: List[dict], output_file: str):
        """保存执行历史到文件"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(execution_history, f, indent=2, ensure_ascii=False)
        
        print(f"执行历史已保存到: {output_file}")

def fix_split_multiturn_to_single():
    """修正split_multiturn_to_single.py中的函数调用格式"""
    print("修正split_multiturn_to_single.py中的函数调用格式...")
    
    # 读取原文件
    with open('/home/ma-user/work/RL-Factory/data/bfcl_data/split_multiturn_to_single.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 定义需要修正的映射
    corrections = {
        # 系统提示词中的工具格式修正
        'Tools\\nYou may call one or more functions': '# Tools\\nYou may call one or more functions',
        
        # 添加正确的系统提示词模板
        '"# You are a helpful assistant."': '''"""# Tools
You may call one or more functions to assist with the user query.
You are provided with function signatures within <tools></tools> XML tags:
<tools>
{"name": "get_weather", "description": "Get the weather of a city for a specific date.", "parameters": {" type": "object", "properties": {"city": {"type": "string", "description": "The city to get weather for,\\nin Chinese."}, "date": {"type": "string", "description": "The date in YYYY-MM-DD format."}}, "required": ["city"]}}
</tools>
For each function call, output the function name and arguments within the following XML format:
<tool_call>{"name": "get_weather", "arguments": {"city": "Beijing", "date": "2025-08-24"}}</tool_call>
You are a helpful assistant."""'''
    }
    
    # 应用修正
    for old, new in corrections.items():
        content = content.replace(old, new)
    
    # 保存修正后的文件
    backup_file = '/home/ma-user/work/RL-Factory/data/bfcl_data/split_multiturn_to_single.py.backup'
    with open(backup_file, 'w', encoding='utf-8') as f:
        with open('/home/ma-user/work/RL-Factory/data/bfcl_data/split_multiturn_to_single.py', 'r', encoding='utf-8') as orig:
            f.write(orig.read())
    
    with open('/home/ma-user/work/RL-Factory/data/bfcl_data/split_multiturn_to_single.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"已修正split_multiturn_to_single.py，备份保存在: {backup_file}")

def main():
    """主函数"""
    print("🚀 启动增强的多轮对话处理器")
    print("="*80)
    
    # 创建处理器
    processor = EnhancedMultiTurnProcessor()
    
    try:
        # 处理document PDF场景
        print("\n1. 处理document PDF多轮场景...")
        pdf_result = processor.process_document_pdf_scenario()
        
        # 保存PDF场景结果
        output_dir = Path('/home/ma-user/work/RL-Factory/data/enhanced_multiturn')
        output_dir.mkdir(exist_ok=True)
        
        pdf_enhanced_file = output_dir / 'document_pdf_scenario_enhanced.json'
        pdf_history_file = output_dir / 'document_pdf_scenario_execution_history.json'
        
        processor.save_enhanced_data(pdf_result, str(pdf_enhanced_file))
        processor.save_execution_history(pdf_result['execution_history'], str(pdf_history_file))
        
        # 显示PDF场景示例
        print("\n2. PDF场景增强数据示例:")
        if pdf_result['enhanced_data']:
            example = pdf_result['enhanced_data'][1]  # 显示第二轮（有历史记录）
            print(f"ID: {example['id']}")
            print(f"Question: {example['question']}")
            print(f"Golden Answers: {example['golden_answers']}")
            print("真实工具调用轨迹预览:")
            if 'Previous tool calls:' in example['prompt']:
                trace_start = example['prompt'].find('Previous tool calls:')
                trace_part = example['prompt'][trace_start:trace_start+800]
                print(trace_part + "..." if len(trace_part) >= 800 else trace_part)
        
        # 处理multi_turn_base_1示例
        print("\n3. 处理multi_turn_base_1示例...")
        enhanced_result = processor.process_multi_turn_base_1()
        
        enhanced_file = output_dir / 'multi_turn_base_1_enhanced.json'
        history_file = output_dir / 'multi_turn_base_1_execution_history.json'
        
        processor.save_enhanced_data(enhanced_result, str(enhanced_file))
        processor.save_execution_history(enhanced_result['execution_history'], str(history_file))
        
        # 修正split_multiturn_to_single.py
        print("\n4. 修正split_multiturn_to_single.py...")
        fix_split_multiturn_to_single()
        
        print("\n✅ 处理完成！")
        print(f"PDF场景增强数据文件: {pdf_enhanced_file}")
        print(f"PDF场景执行历史文件: {pdf_history_file}")
        print(f"Base1增强数据文件: {enhanced_file}")
        print(f"Base1执行历史文件: {history_file}")
        
    except Exception as e:
        print(f"❌ 处理过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
