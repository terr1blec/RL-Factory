#!/usr/bin/env python3
"""
多轮对话数据转换为单轮训练格式的脚本
将BFCL_v3_multi_turn_base.json转换为指定的训练格式
"""

import json
import csv
from typing import Dict, List, Any, Optional
from pathlib import Path

class MultiTurnToSingleConverter:
    """多轮对话转单轮对话转换器"""
    
    def __init__(self):
        # 类名映射
        self.class_map: Dict[str, str] = {
            "GorillaFileSystem": "FileSystem",
            "TwitterAPI": "SocialMedia",
            "TicketAPI": "Ticket",
            "TravelAPI": "Travel",
            "TradingAPI": "Trading",
            "VehicleAPI": "Vehicle",
            "MathAPI": "Math",
            "MessageAPI": "Message",
        }
        
        # 默认系统提示词
        self.default_system_prompt = "你是一个智能助手，可以使用各种工具来帮助用户完成任务。请根据用户的请求调用相应的工具。"
    
    def load_data(self, original_file: str, golden_answer_file: str) -> tuple:
        """加载原始数据和golden answer数据"""
        with open(original_file, 'r', encoding='utf-8') as f:
            original_data = []
            for line in f:
                line = line.strip()
                if line:
                    original_data.append(json.loads(line))
        
        with open(golden_answer_file, 'r', encoding='utf-8') as f:
            golden_data = []
            for line in f:
                line = line.strip()
                if line:
                    golden_data.append(json.loads(line))
        
        return original_data, golden_data
    
    def map_involved_classes(self, involved_classes: List[str]) -> List[str]:
        """映射involved_classes到新的名称"""
        return [self.class_map.get(cls, cls) for cls in involved_classes]
    
    def build_conversation_history(self, questions: List[List[Dict]], turn_index: int) -> str:
        """构建对话历史，用于prompt"""
        history = []
        for i in range(turn_index):
            turn_messages = questions[i]
            for msg in turn_messages:
                if msg['role'] == 'user':
                    history.append(f"User: {msg['content']}")
        
        if history:
            return "\n".join(history) + "\n"
        return ""
    
    def build_tool_call_trace(self, golden_answers: List[List[str]], turn_index: int) -> str:
        """构建工具调用轨迹（可扩展接口）"""
        # 这是一个可扩展的接口，用于根据前一轮的问题与golden_answer补充工具调用轨迹
        trace = []
        for i in range(turn_index):
            if i < len(golden_answers):
                turn_actions = golden_answers[i]
                trace.append(f"Turn {i+1} actions: {', '.join(turn_actions)}")
        
        if trace:
            return "\n".join(trace) + "\n"
        return ""
    
    def create_custom_prompt(self, 
                           system_prompt: str,
                           conversation_history: str,
                           tool_trace: str,
                           current_question: str) -> str:
        """创建自定义prompt"""
        prompt_parts = []
        
        # 系统提示词
        if system_prompt:
            prompt_parts.append(f"System: {system_prompt}")
        
        # 对话历史
        if conversation_history:
            prompt_parts.append("Previous conversation:")
            prompt_parts.append(conversation_history)
        
        # 工具调用轨迹
        if tool_trace:
            prompt_parts.append("Previous tool calls:")
            prompt_parts.append(tool_trace)
        
        # 当前问题
        prompt_parts.append(f"Current request: {current_question}")
        
        return "\n".join(prompt_parts)
    
    def convert_to_single_turn(self, 
                             original_data: List[Dict], 
                             golden_data: List[Dict],
                             custom_system_prompt: Optional[str] = None) -> List[Dict]:
        """转换多轮数据为单轮格式"""
        result = []
        system_prompt = custom_system_prompt or self.default_system_prompt
        
        # 创建golden_data的索引
        golden_map = {item['id']: item for item in golden_data}
        
        for original_item in original_data:
            item_id = original_item['id']
            questions = original_item['question']
            initial_config = original_item.get('initial_config', {})
            involved_classes = original_item.get('involved_classes', [])
            
            # 获取对应的golden answer
            golden_item = golden_map.get(item_id)
            if not golden_item:
                print(f"Warning: No golden answer found for {item_id}")
                continue
            
            golden_answers = golden_item['ground_truth']
            
            # 处理每一轮对话
            for turn_idx, turn_questions in enumerate(questions):
                for q_idx, question_msg in enumerate(turn_questions):
                    if question_msg['role'] == 'user':
                        # 构建对话历史
                        conversation_history = self.build_conversation_history(questions, turn_idx)
                        
                        # 构建工具调用轨迹
                        tool_trace = self.build_tool_call_trace(golden_answers, turn_idx)
                        
                        # 创建prompt
                        prompt = self.create_custom_prompt(
                            system_prompt,
                            conversation_history,
                            tool_trace,
                            question_msg['content']
                        )
                        
                        # 获取当前轮的golden answer
                        current_golden = golden_answers[turn_idx] if turn_idx < len(golden_answers) else []
                        
                        # 映射类名
                        mapped_classes = self.map_involved_classes(involved_classes)
                        
                        # 处理initial_config中的类名映射
                        mapped_initial_config = self.map_initial_config_classes(initial_config)
                        
                        # 创建单轮数据项
                        single_turn_item = {
                            "id": f"{item_id}_turn_{turn_idx}_{q_idx}",
                            "question": question_msg['content'],
                            "golden_answers": current_golden,
                            "data_source": mapped_classes,
                            "prompt": prompt,
                            "ability": "tool_use",
                            "reward_model": "{'final state': {}, 'style': 'rule'}",
                            "extra_info": {
                                "initial_config": mapped_initial_config,
                                "path": original_item.get('path', []),
                                "original_id": item_id,
                                "turn_index": turn_idx,
                                "question_index": q_idx
                            }
                        }
                        
                        result.append(single_turn_item)
        
        return result
    
    def map_initial_config_classes(self, initial_config: Dict) -> Dict:
        """映射initial_config中的类名"""
        mapped_config = {}
        for class_name, config in initial_config.items():
            mapped_name = self.class_map.get(class_name, class_name)
            mapped_config[mapped_name] = config
        return mapped_config
    
    def save_to_csv(self, data: List[Dict], output_file: str):
        """保存数据到CSV文件"""
        if not data:
            print("No data to save")
            return
        
        fieldnames = ["id", "question", "golden_answers", "data_source", "prompt", "ability", "reward_model", "extra_info"]
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for item in data:
                # 将复杂对象转换为JSON字符串
                row = {
                    "id": item["id"],
                    "question": item["question"],
                    "golden_answers": json.dumps(item["golden_answers"], ensure_ascii=False),
                    "data_source": json.dumps(item["data_source"], ensure_ascii=False),
                    "prompt": item["prompt"],
                    "ability": item["ability"],
                    "reward_model": item["reward_model"],
                    "extra_info": json.dumps(item["extra_info"], ensure_ascii=False)
                }
                writer.writerow(row)
    
    def save_to_json(self, data: List[Dict], output_file: str):
        """保存数据到JSON文件"""
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')

def main():
    """主函数"""
    # 文件路径
    original_file = "/root/zilin/RL-Factory/data/bfcl_data/multi-turn-original/BFCL_v3_multi_turn_base.json"
    golden_answer_file = "/root/zilin/RL-Factory/data/bfcl_data/possible_answer/BFCL_v3_multi_turn_base.json"
    
    # 输出文件路径
    output_csv = "/root/zilin/RL-Factory/data/bfcl_data/single_turn_training_data.csv"
    output_json = "/root/zilin/RL-Factory/data/bfcl_data/single_turn_training_data.json"
    
    # 创建转换器
    converter = MultiTurnToSingleConverter()
    
    print("Loading data...")
    original_data, golden_data = converter.load_data(original_file, golden_answer_file)
    print(f"Loaded {len(original_data)} original items and {len(golden_data)} golden answer items")
    
    print("Converting to single turn format...")
    # 自定义系统提示词（可以修改）
    custom_system = "# Tools\nYou may call one or more functions to assist with the user query.\nYou are provided with function signatures within <tools></tools> XML tags:\n<tools>\n{\"name\": \"get_weather\", \"description\": \"Get the weather of a city for a specific date.\", \"parameters\": {\" type\": \"object\", \"properties\": {\"city\": {\"type\": \"string\", \"description\": \"The city to get weather for,\nin Chinese.\"}, \"date\": {\"type\": \"string\", \"description\": \"The date in YYYY-MM-DD format.\"}}, \"required\": [\"city\"]}}\n</tools>\nFor each function call, output the function name and arguments within the following XML format:\n<tool_call>{\"name\": \"get_weather\", \"arguments\": {\"city\": \"Beijing\", \"date\": \"2025-08-24\"}}</tool_call>\nYou are a helpful assistant." 
    
    single_turn_data = converter.convert_to_single_turn(original_data, golden_data, custom_system)
    print(f"Converted to {len(single_turn_data)} single turn items")
    
    print("Saving results...")
    converter.save_to_csv(single_turn_data, output_csv)
    converter.save_to_json(single_turn_data, output_json)
    
    print(f"Conversion completed!")
    print(f"CSV output: {output_csv}")
    print(f"JSON output: {output_json}")
    
    # 显示一个示例
    if single_turn_data:
        print("\nExample output:")
        example = single_turn_data[0]
        print(f"ID: {example['id']}")
        print(f"Question: {example['question']}")
        print(f"Golden Answer: {example['golden_answers']}")
        print(f"Data Source: {example['data_source']}")
        print(f"Ability: {example['ability']}")
        print(f"Reward Model: {example['reward_model']}")

if __name__ == "__main__":
    main()
