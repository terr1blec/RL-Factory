#!/usr/bin/env python3
"""
增强的多轮对话转换器 - 结合拆分功能和真实执行轨迹生成
基于QwenManager执行工具调用，生成真实的历史轨迹数据
"""

import json
import csv
import re
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from omegaconf import OmegaConf
from envs.tool_manager.qwen3_manager import QwenManager
import pandas as pd

class EnhancedMultiTurnConverter:
    """增强的多轮对话转换器，结合拆分和真实执行功能"""
    
    def __init__(self):
        # 类名映射
        self.class_map: Dict[str, str] = {
            "GorillaFileSystem": "file_system",
            "TwitterAPI": "posting", 
            "TicketAPI": "ticket",
            "TravelAPI": "travel",
            "TradingAPI": "trading",
            "VehicleAPI": "vehicle",
            "MathAPI": "math",
            "MessageAPI": "message",
        }
        
        # 工具前缀到类名的映射
        self.tool_prefix_to_class = {
            "file_system": "file_system",
            "math": "math", 
            "posting": "posting",
            "ticket": "ticket",
            "trading": "trading",
            "travel": "travel",
            "vehicle": "vehicle",
            "message": "message",
        }
        
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
            
            # Math相关
            'logarithm': 'math-logarithm',
            'mean': 'math-mean',
            'standard_deviation': 'math-standard_deviation',
            'si_unit_conversion': 'math-si_unit_conversion',
            'imperial_si_conversion': 'math-imperial_si_conversion',
            'add': 'math-add',
            'subtract': 'math-subtract',
            'multiply': 'math-multiply',
            'divide': 'math-divide',
            'power': 'math-power',
            'square_root': 'math-square_root',
            'absolute_value': 'math-absolute_value',
            'round_number': 'math-round_number',
            'percentage': 'math-percentage',
            'min_value': 'math-min_value',
            'max_value': 'math-max_value',
            'sum_values': 'math-sum_values',
            
            # posting/Posting相关
            'authenticate_twitter': 'posting-authenticate_twitter',
            'posting_get_login_status': 'posting-posting_get_login_status',
            'post_tweet': 'posting-post_tweet',
            'retweet': 'posting-retweet',
            'comment': 'posting-comment',
            'mention': 'posting-mention',
            'follow_user': 'posting-follow_user',
            'list_all_following': 'posting-list_all_following',
            'unfollow_user': 'posting-unfollow_user',
            'get_tweet': 'posting-get_tweet',
            'get_user_tweets': 'posting-get_user_tweets',
            'search_tweets': 'posting-search_tweets',
            'get_tweet_comments': 'posting-get_tweet_comments',
            'get_user_stats': 'posting-get_user_stats',
            
            # Ticket相关
            'create_ticket': 'ticket-create_ticket',
            'get_ticket': 'ticket-get_ticket',
            'close_ticket': 'ticket-close_ticket',
            'resolve_ticket': 'ticket-resolve_ticket',
            'edit_ticket': 'ticket-edit_ticket',
            'ticket_login': 'ticket-ticket_login',
            'ticket_get_login_status': 'ticket-ticket_get_login_status',
            'logout': 'ticket-logout',
            'get_user_tickets': 'ticket-get_user_tickets',
            
            # Trading相关
            'get_current_time': 'trading-get_current_time',
            'update_market_status': 'trading-update_market_status',
            'get_symbol_by_name': 'trading-get_symbol_by_name',
            'get_stock_info': 'trading-get_stock_info',
            'get_order_details': 'trading-get_order_details',
            'cancel_order': 'trading-cancel_order',
            'place_order': 'trading-place_order',
            'make_transaction': 'trading-make_transaction',
            'get_account_info': 'trading-get_account_info',
            'trading_login': 'trading-trading_login',
            'trading_get_login_status': 'trading-trading_get_login_status',
            'trading_logout': 'trading-trading_logout',
            'fund_account': 'trading-fund_account',
            'remove_stock_from_watchlist': 'trading-remove_stock_from_watchlist',
            'get_watchlist': 'trading-get_watchlist',
            'get_order_history': 'trading-get_order_history',
            'get_transaction_history': 'trading-get_transaction_history',
            'update_stock_price': 'trading-update_stock_price',
            'get_available_stocks': 'trading-get_available_stocks',
            'filter_stocks_by_price': 'trading-filter_stocks_by_price',
            'add_to_watchlist': 'trading-add_to_watchlist',
            'notify_price_change': 'trading-notify_price_change',
            
            # Travel相关
            'authenticate_travel': 'travel-authenticate_travel',
            'travel_get_login_status': 'travel-travel_get_login_status',
            'get_budget_fiscal_year': 'travel-get_budget_fiscal_year',
            'register_credit_card': 'travel-register_credit_card',
            'get_flight_cost': 'travel-get_flight_cost',
            'get_credit_card_balance': 'travel-get_credit_card_balance',
            'book_flight': 'travel-book_flight',
            'retrieve_invoice': 'travel-retrieve_invoice',
            'list_all_airports': 'travel-list_all_airports',
            'cancel_booking': 'travel-cancel_booking',
            'compute_exchange_rate': 'travel-compute_exchange_rate',
            'verify_traveler_information': 'travel-verify_traveler_information',
            'set_budget_limit': 'travel-set_budget_limit',
            'get_nearest_airport_by_city': 'travel-get_nearest_airport_by_city',
            'purchase_insurance': 'travel-purchase_insurance',
            'contact_customer_support': 'travel-contact_customer_support',
            'get_all_credit_cards': 'travel-get_all_credit_cards',
            
            # Vehicle相关
            'startEngine': 'vehicle-startEngine',
            'fillFuelTank': 'vehicle-fillFuelTank',
            'lockDoors': 'vehicle-lockDoors',
            'adjustClimateControl': 'vehicle-adjustClimateControl',
            'get_outside_temperature_from_google': 'vehicle-get_outside_temperature_from_google',
            'get_outside_temperature_from_weather_com': 'vehicle-get_outside_temperature_from_weather_com',
            'setHeadlights': 'vehicle-setHeadlights',
            'displayCarStatus': 'vehicle-displayCarStatus',
            'activateParkingBrake': 'vehicle-activateParkingBrake',
            'pressBrakePedal': 'vehicle-pressBrakePedal',
            'releaseBrakePedal': 'vehicle-releaseBrakePedal',
            'setCruiseControl': 'vehicle-setCruiseControl',
            'get_current_speed': 'vehicle-get_current_speed',
            'estimate_drive_feasibility_by_mileage': 'vehicle-estimate_drive_feasibility_by_mileage',
            'liter_to_gallon': 'vehicle-liter_to_gallon',
            'gallon_to_liter': 'vehicle-gallon_to_liter',
            'estimate_distance': 'vehicle-estimate_distance',
            'get_zipcode_based_on_city': 'vehicle-get_zipcode_based_on_city',
            'set_navigation': 'vehicle-set_navigation',
            'check_tire_pressure': 'vehicle-check_tire_pressure',
            'find_nearest_tire_shop': 'vehicle-find_nearest_tire_shop',
            
            # Message相关
            'list_users': 'message-list_users',
            'get_user_id': 'message-get_user_id',
            'message_login': 'message-message_login',
            'message_get_login_status': 'message-message_get_login_status',
            'send_message': 'message-send_message',
            'delete_message': 'message-delete_message',
            'view_messages_sent': 'message-view_messages_sent',
            'add_contact': 'message-add_contact',
            'search_messages': 'message-search_messages',
            'get_message_stats': 'message-get_message_stats',
        }
        
        # 参数名映射
        self.param_mapping = {
            # FileSystem相关
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
            'wc': {'file_name': 'file_name'},
            'sort': {'file_name': 'file_name'},
            'du': {'path': 'path'},
            'rmdir': {'dir_name': 'dir_name'},
            'load_scenario': {'scenario': 'scenario'},
            'save_scenario': {},
            
            # Math相关
            'logarithm': {'number': 'number', 'base': 'base'},
            'mean': {'numbers': 'numbers'},
            'standard_deviation': {'numbers': 'numbers'},
            'si_unit_conversion': {'value': 'value', 'from_unit': 'from_unit', 'to_unit': 'to_unit'},
            'imperial_si_conversion': {'value': 'value', 'from_unit': 'from_unit', 'to_unit': 'to_unit'},
            'add': {'a': 'a', 'b': 'b'},
            'subtract': {'a': 'a', 'b': 'b'},
            'multiply': {'a': 'a', 'b': 'b'},
            'divide': {'a': 'a', 'b': 'b'},
            'power': {'base': 'base', 'exponent': 'exponent'},
            'square_root': {'number': 'number'},
            'absolute_value': {'number': 'number'},
            'round_number': {'number': 'number', 'decimals': 'decimals'},
            'percentage': {'part': 'part', 'whole': 'whole'},
            'min_value': {'numbers': 'numbers'},
            'max_value': {'numbers': 'numbers'},
            'sum_values': {'numbers': 'numbers'},
            
            # posting/Posting相关
            'authenticate_twitter': {'username': 'username', 'password': 'password'},
            'posting_get_login_status': {},
            'post_tweet': {'content': 'content'},
            'retweet': {'tweet_id': 'tweet_id'},
            'comment': {'tweet_id': 'tweet_id', 'comment': 'comment'},
            'mention': {'username': 'username', 'content': 'content'},
            'follow_user': {'username': 'username'},
            'list_all_following': {},
            'unfollow_user': {'username': 'username'},
            'get_tweet': {'tweet_id': 'tweet_id'},
            'get_user_tweets': {'username': 'username'},
            'search_tweets': {'query': 'query'},
            'get_tweet_comments': {'tweet_id': 'tweet_id'},
            'get_user_stats': {'username': 'username'},
            
            # Ticket相关
            'create_ticket': {'title': 'title', 'description': 'description', 'priority': 'priority'},
            'get_ticket': {'ticket_id': 'ticket_id'},
            'close_ticket': {'ticket_id': 'ticket_id'},
            'resolve_ticket': {'ticket_id': 'ticket_id'},
            'edit_ticket': {'ticket_id': 'ticket_id', 'title': 'title', 'description': 'description'},
            'ticket_login': {'username': 'username', 'password': 'password'},
            'ticket_get_login_status': {},
            'logout': {},
            'get_user_tickets': {},
            
            # Trading相关
            'get_current_time': {},
            'update_market_status': {'status': 'status'},
            'get_symbol_by_name': {'name': 'name'},
            'get_stock_info': {'symbol': 'symbol'},
            'get_order_details': {'order_id': 'order_id'},
            'cancel_order': {'order_id': 'order_id'},
            'place_order': {'symbol': 'symbol', 'side': 'side', 'quantity': 'quantity', 'order_type': 'order_type'},
            'make_transaction': {'symbol': 'symbol', 'side': 'side', 'quantity': 'quantity'},
            'get_account_info': {},
            'trading_login': {'username': 'username', 'password': 'password'},
            'trading_get_login_status': {},
            'trading_logout': {},
            'fund_account': {'amount': 'amount'},
            'remove_stock_from_watchlist': {'symbol': 'symbol'},
            'get_watchlist': {},
            'get_order_history': {},
            'get_transaction_history': {},
            'update_stock_price': {'symbol': 'symbol', 'price': 'price'},
            'get_available_stocks': {},
            'filter_stocks_by_price': {'min_price': 'min_price', 'max_price': 'max_price'},
            'add_to_watchlist': {'symbol': 'symbol'},
            'notify_price_change': {'symbol': 'symbol', 'price': 'price'},
            
            # Travel相关
            'authenticate_travel': {'username': 'username', 'password': 'password'},
            'travel_get_login_status': {},
            'get_budget_fiscal_year': {},
            'register_credit_card': {'card_number': 'card_number', 'expiry_date': 'expiry_date'},
            'get_flight_cost': {'departure': 'departure', 'destination': 'destination', 'date': 'date'},
            'get_credit_card_balance': {'card_id': 'card_id'},
            'book_flight': {'flight_id': 'flight_id', 'card_id': 'card_id'},
            'retrieve_invoice': {'booking_id': 'booking_id'},
            'list_all_airports': {},
            'cancel_booking': {'booking_id': 'booking_id'},
            'compute_exchange_rate': {'from_currency': 'from_currency', 'to_currency': 'to_currency'},
            'verify_traveler_information': {'passport_number': 'passport_number'},
            'set_budget_limit': {'amount': 'amount'},
            'get_nearest_airport_by_city': {'city': 'city'},
            'purchase_insurance': {'booking_id': 'booking_id', 'insurance_type': 'insurance_type'},
            'contact_customer_support': {'message': 'message'},
            'get_all_credit_cards': {},
            
            # Vehicle相关
            'startEngine': {},
            'fillFuelTank': {'amount': 'amount'},
            'lockDoors': {},
            'adjustClimateControl': {'temperature': 'temperature', 'fan_speed': 'fan_speed'},
            'get_outside_temperature_from_google': {'location': 'location'},
            'get_outside_temperature_from_weather_com': {'location': 'location'},
            'setHeadlights': {'mode': 'mode'},
            'displayCarStatus': {},
            'activateParkingBrake': {},
            'pressBrakePedal': {'force': 'force'},
            'releaseBrakePedal': {},
            'setCruiseControl': {'speed': 'speed'},
            'get_current_speed': {},
            'estimate_drive_feasibility_by_mileage': {'destination': 'destination'},
            'liter_to_gallon': {'liters': 'liters'},
            'gallon_to_liter': {'gallons': 'gallons'},
            'estimate_distance': {'origin': 'origin', 'destination': 'destination'},
            'get_zipcode_based_on_city': {'city': 'city'},
            'set_navigation': {'destination': 'destination'},
            'check_tire_pressure': {},
            'find_nearest_tire_shop': {'location': 'location'},
            
            # Message相关
            'list_users': {},
            'get_user_id': {'username': 'username'},
            'message_login': {'username': 'username', 'password': 'password'},
            'message_get_login_status': {},
            'send_message': {'recipient': 'recipient', 'message': 'message'},
            'delete_message': {'message_id': 'message_id'},
            'view_messages_sent': {},
            'add_contact': {'username': 'username'},
            'search_messages': {'query': 'query'},
            'get_message_stats': {},
        }
        
        self.manager = None
    
    def create_qwen_manager(self):
        """创建QwenManager实例"""
        if self.manager is None:
            # 确保工作目录正确
            import os
            original_cwd = os.getcwd()
            os.chdir("/home/ma-user/work/RL-Factory")
            
            config = {
                'config_path': "/home/ma-user/work/RL-Factory/envs/configs/data_process.pydata",
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
            
            # 恢复原工作目录
            os.chdir(original_cwd)
        
        return self.manager
    
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
    
    def parse_function_call(self, call_str: str) -> Tuple[str, dict]:
        """解析函数调用字符串，返回函数名和参数"""
        # 处理类似 "ls(a=True)" 或 "sort('file.txt')" 的格式
        if '(' in call_str and ')' in call_str:
            func_name = call_str.split('(')[0].strip()
            params_str = call_str[call_str.find('(')+1:call_str.rfind(')')]
            
            # 解析参数
            params = {}
            if params_str.strip():
                # 检查是否是键值对格式 (key=value)
                if '=' in params_str:
                    # 使用正则表达式解析参数，支持引号内的逗号
                    param_pattern = r"(\w+)\s*=\s*([^,]+(?:,[^=]*)*?)(?=\s*,\s*\w+\s*=|\s*$)"
                    matches = re.findall(param_pattern, params_str)
                    
                    for key, value in matches:
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
                else:
                    # 处理位置参数格式，如 sort('file.txt')
                    value = params_str.strip()
                    if value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    elif value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    
                    # 根据函数名推断参数名
                    if func_name == 'sort':
                        params['file_name'] = value
                    elif func_name == 'cat':
                        params['file_name'] = value
                    elif func_name == 'rm':
                        params['file_name'] = value
                    elif func_name == 'tail':
                        params['file_name'] = value
                    else:
                        # 默认使用第一个参数名
                        if func_name in self.param_mapping:
                            param_keys = list(self.param_mapping[func_name].keys())
                            if param_keys:
                                params[param_keys[0]] = value
            
            return func_name, params
        else:
            return call_str, {}
    
    def convert_function_call(self, old_call: str) -> Tuple[str, dict]:
        """将旧格式的函数调用转换为新格式"""
        func_name, params = self.parse_function_call(old_call)
        
        # 映射函数名
        new_func_name = self.function_mapping.get(func_name, func_name)
        
        # 如果没有直接映射，尝试根据上下文推断
        if new_func_name == func_name and '-' not in new_func_name:
            # 尝试根据函数名推断工具类型
            inferred_name = self.infer_tool_name(func_name)
            if inferred_name:
                new_func_name = inferred_name
        
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
    
    def infer_tool_name(self, func_name: str) -> Optional[str]:
        """根据函数名推断完整的工具名称"""
        # 数学函数推断
        math_functions = ['add', 'subtract', 'multiply', 'divide', 'power', 'sqrt', 'abs', 'round', 'log', 'mean', 'std']
        if any(math_func in func_name.lower() for math_func in math_functions):
            return f"math-{func_name}"
        
        # 社交媒体函数推断
        social_functions = ['tweet', 'post', 'follow', 'unfollow', 'retweet', 'comment', 'mention']
        if any(social_func in func_name.lower() for social_func in social_functions):
            return f"posting-{func_name}"
        
        # 票务函数推断
        ticket_functions = ['ticket', 'create_ticket', 'close_ticket', 'resolve']
        if any(ticket_func in func_name.lower() for ticket_func in ticket_functions):
            return f"ticket-{func_name}"
        
        # 交易函数推断
        trading_functions = ['order', 'trade', 'stock', 'buy', 'sell', 'watchlist', 'account']
        if any(trading_func in func_name.lower() for trading_func in trading_functions):
            return f"trading-{func_name}"
        
        # 旅行函数推断
        travel_functions = ['flight', 'book', 'travel', 'airport', 'credit_card', 'budget']
        if any(travel_func in func_name.lower() for travel_func in travel_functions):
            return f"travel-{func_name}"
        
        # 车辆函数推断
        vehicle_functions = ['engine', 'fuel', 'door', 'brake', 'tire', 'headlight', 'climate']
        if any(vehicle_func in func_name.lower() for vehicle_func in vehicle_functions):
            return f"vehicle-{func_name}"
        
        # 消息函数推断
        message_functions = ['message', 'send', 'delete', 'contact', 'user']
        if any(message_func in func_name.lower() for message_func in message_functions):
            return f"message-{func_name}"
        
        return None
    
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
    
    def prepare_scenario_for_loading(self, scenario_data: dict) -> dict:
        """准备场景数据用于加载，确保使用正确的键名"""
        # 如果场景数据包含映射后的类名，需要转换回原始格式用于加载
        mapped_classes = ['file_system', 'posting', 'ticket', 'travel', 'trading', 'vehicle', 'math', 'message']
        
        if any(key in scenario_data for key in mapped_classes):
            # 创建一个副本并转换键名
            prepared_scenario = {}
            for key, value in scenario_data.items():
                if key in mapped_classes:
                    # 转换回原始类名
                    original_key = None
                    for orig, mapped in self.class_map.items():
                        if mapped == key:
                            original_key = orig
                            break
                    if original_key:
                        prepared_scenario[original_key] = value
                    else:
                        prepared_scenario[key] = value
                else:
                    prepared_scenario[key] = value
            return prepared_scenario
        return scenario_data

    def simulate_multi_turn_execution(self, scenario_data: dict, golden_answers: List[List[str]]) -> List[dict]:
        """模拟多轮执行过程，生成真实的调用轨迹 - 连续执行所有轮次"""
        manager = self.create_qwen_manager()
        
        # 加载所有类型的初始场景
        print(f"加载初始场景...")
        
        # 准备场景数据用于加载
        prepared_scenario = self.prepare_scenario_for_loading(scenario_data)
        
        # 根据可用的类型加载场景
        load_results = []
        
        # file_system
        if 'GorillaFileSystem' in prepared_scenario or 'file_system' in prepared_scenario:
            fs_scenario = prepared_scenario.get('GorillaFileSystem') or prepared_scenario.get('file_system')
            load_result = self.execute_tool('file_system-load_scenario', {'scenario': fs_scenario})
            load_results.append(('file_system', load_result))
        
        # math - 不需要加载场景
        if 'MathAPI' in prepared_scenario or 'math' in prepared_scenario:
            load_results.append(('math', {'success': True, 'result': 'math tools ready'}))
        
        # posting/Posting
        if 'TwitterAPI' in prepared_scenario or 'posting' in prepared_scenario:
            sm_scenario = prepared_scenario.get('TwitterAPI') or prepared_scenario.get('posting')
            load_result = self.execute_tool('posting-load_scenario', {'scenario': sm_scenario})
            load_results.append(('posting', load_result))
        
        # ticket
        if 'TicketAPI' in prepared_scenario or 'ticket' in prepared_scenario:
            ticket_scenario = prepared_scenario.get('TicketAPI') or prepared_scenario.get('ticket')
            load_result = self.execute_tool('ticket-load_scenario', {'scenario': ticket_scenario})
            load_results.append(('ticket', load_result))
        
        # trading
        if 'TradingAPI' in prepared_scenario or 'trading' in prepared_scenario:
            trading_scenario = prepared_scenario.get('TradingAPI') or prepared_scenario.get('trading')
            load_result = self.execute_tool('trading-load_scenario', {'scenario': trading_scenario})
            load_results.append(('trading', load_result))
        
        # travel
        if 'TravelAPI' in prepared_scenario or 'travel' in prepared_scenario:
            travel_scenario = prepared_scenario.get('TravelAPI') or prepared_scenario.get('travel')
            load_result = self.execute_tool('travel-load_scenario', {'scenario': travel_scenario})
            load_results.append(('travel', load_result))
        
        # vehicle
        if 'VehicleAPI' in prepared_scenario or 'vehicle' in prepared_scenario:
            vehicle_scenario = prepared_scenario.get('VehicleAPI') or prepared_scenario.get('vehicle')
            load_result = self.execute_tool('vehicle-load_scenario', {'scenario': vehicle_scenario})
            load_results.append(('vehicle', load_result))
        
        # message
        if 'MessageAPI' in prepared_scenario or 'message' in prepared_scenario:
            message_scenario = prepared_scenario.get('MessageAPI') or prepared_scenario.get('message')
            load_result = self.execute_tool('message-load_scenario', {'scenario': message_scenario})
            load_results.append(('message', load_result))
        
        # 检查加载结果并跟踪成功加载的场景类型
        successful_loads = 0
        self._loaded_scenario_types = set()
        
        for class_name, result in load_results:
            if result['success']:
                print(f"{class_name}场景加载成功")
                successful_loads += 1
                self._loaded_scenario_types.add(class_name)
            else:
                print(f"{class_name}场景加载失败: {result.get('error', 'Unknown error')}")
        
        if successful_loads == 0:
            print(f"所有场景加载都失败")
            return []
        else:
            print(f"成功加载{successful_loads}个场景: {list(self._loaded_scenario_types)}")
        
        execution_history = []
        
        # 连续执行所有轮次，不重新加载场景
        for turn_idx, turn_actions in enumerate(golden_answers):
            print(f"\n执行第{turn_idx + 1}轮操作...")
            
            # 保存当前轮开始前的场景状态（尝试保存所有类型）
            scenario_before = self.save_all_scenarios()
                
            turn_history = {
                'turn_index': turn_idx,
                'actions': [],
                'scenario_before': scenario_before,
                'scenario_after': None
            }
            
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
            
            # 保存当前轮结束后的场景状态（用于记录）
            scenario_after = self.save_all_scenarios()
            turn_history['scenario_after'] = scenario_after
            if scenario_after:
                print(f"  第{turn_idx + 1}轮结束，场景快照已保存")
            else:
                print(f"  第{turn_idx + 1}轮结束，场景保存失败")
            
            execution_history.append(turn_history)
        
        print(f"所有{len(golden_answers)}轮操作连续执行完成")
        return execution_history
    
    def generate_conversation_history(self, questions: List[List[Dict]], execution_history: List[dict], current_turn: int) -> List[Dict]:
        """生成标准对话格式的历史记录"""
        conversation = []
        
        for turn_idx in range(current_turn):
            if turn_idx < len(questions):
                turn_messages = questions[turn_idx]
                
                # 添加用户消息
                for msg in turn_messages:
                    if msg['role'] == 'user':
                        conversation.append({
                            "role": "user",
                            "content": msg['content']
                        })
                
                # 添加助手的工具调用和结果
                if turn_idx < len(execution_history):
                    turn_data = execution_history[turn_idx]
                    
                    # 构建助手响应（包含工具调用）
                    assistant_calls = []
                    for action in turn_data['actions']:
                        func_name = action['function_name']
                        params = action['parameters']
                        tool_call = f'<tool_call>{{"name": "{func_name}", "arguments": {json.dumps(params, ensure_ascii=False)}}}</tool_call>'
                        assistant_calls.append(tool_call)
                    
                    if assistant_calls:
                        conversation.append({
                            "role": "assistant",
                            "content": ' '.join(assistant_calls)
                        })
                    
                    # 添加工具执行结果
                    for action in turn_data['actions']:
                        result = action['execution_result']
                        
                        if result['success'] and 'result' in result:
                            result_content = result['result']
                            if isinstance(result_content, list) and len(result_content) > 0:
                                tool_result = result_content[0]
                                if isinstance(tool_result, dict) and 'content' in tool_result:
                                    content = tool_result['content']
                                    # 限制内容长度以保持可读性
                                    if len(content) > 500:
                                        content = content[:500] + "..."
                                    conversation.append({
                                        "role": "tool",
                                        "content": content
                                    })
                        else:
                            conversation.append({
                                "role": "tool", 
                                "content": f"Error: {result.get('error', 'Unknown error')}"
                            })
        
        return conversation
    
    def save_all_scenarios(self) -> dict:
        """保存已加载的场景状态"""
        all_scenarios = {}
        
        # 只保存已经成功加载的场景类型
        # 我们需要跟踪哪些场景类型已经被成功加载
        if not hasattr(self, '_loaded_scenario_types'):
            # 如果没有跟踪信息，返回None
            return None
        
        # 定义场景保存工具映射
        save_tool_mapping = {
            'file_system': 'file_system-save_scenario',
            'posting': 'posting-save_scenario',
            'ticket': 'ticket-save_scenario',
            'trading': 'trading-save_scenario',
            'travel': 'travel-save_scenario',
            'vehicle': 'vehicle-save_scenario',
            'message': 'message-save_scenario',
        }
        
        # 只保存已加载的场景类型
        for class_name in self._loaded_scenario_types:
            if class_name == 'math':
                # Math不需要保存场景
                all_scenarios['math'] = {'status': 'ready'}
                continue
                
            save_tool = save_tool_mapping.get(class_name)
            if not save_tool:
                continue
                
            try:
                result = self.execute_tool(save_tool, {})
                if result['success']:
                    scenario_data = self.extract_scenario_from_save_result(result)
                    if scenario_data:
                        all_scenarios[class_name] = scenario_data
                    else:
                        # 如果无法提取场景数据，保存原始结果
                        all_scenarios[class_name] = result
                else:
                    print(f"保存{class_name}场景失败: {result.get('error', 'Unknown error')}")
            except Exception as e:
                print(f"保存{class_name}场景失败: {e}")
                continue
        
        return all_scenarios if all_scenarios else None
    
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
    
    def map_involved_classes(self, involved_classes: List[str]) -> List[str]:
        """映射involved_classes到新的名称"""
        return [self.class_map.get(cls, cls) for cls in involved_classes]
    
    def map_initial_config_classes(self, initial_config: Dict) -> Dict:
        """映射initial_config中的类名"""
        mapped_config = {}
        for class_name, config in initial_config.items():
            mapped_name = self.class_map.get(class_name, class_name)
            mapped_config[mapped_name] = config
        return mapped_config
    
    def convert_golden_answers(self, golden_answers: List[str]) -> List[str]:
        """转换golden answers中的函数调用格式"""
        converted = []
        for call in golden_answers:
            new_func_name, new_params = self.convert_function_call(call)
            if new_params:
                param_strs = []
                for key, value in new_params.items():
                    if isinstance(value, str):
                        param_strs.append(f"{key}='{value}'")
                    else:
                        param_strs.append(f"{key}={value}")
                converted_call = f"{new_func_name}({', '.join(param_strs)})"
            else:
                converted_call = f"{new_func_name}()"
            converted.append(converted_call)
        return converted
    
    def split_train_test(self, data: List[Dict], test_nums: int) -> Tuple[List[Dict], List[Dict]]:
        """将数据划分为训练集和测试集
        
        Args:
            data: 原始数据列表
            test_nums: 测试集数量
            
        Returns:
            Tuple[train_data, test_data]: 训练集和测试集
        """
        if test_nums >= len(data):
            print(f"警告：测试集数量({test_nums})大于等于总数据量({len(data)})，将所有数据作为测试集")
            return [], data
        
        if test_nums <= 0:
            print(f"警告：测试集数量({test_nums})小于等于0，将所有数据作为训练集")
            return data, []
        
        # 简单的顺序划分：前面的作为训练集，后面的作为测试集
        train_data = data[:-test_nums] if test_nums > 0 else data
        test_data = data[-test_nums:] if test_nums > 0 else []
        
        print(f"数据划分完成：训练集 {len(train_data)} 项，测试集 {len(test_data)} 项")
        return train_data, test_data

    def convert_to_enhanced_single_turn(self, 
                                       original_data: List[Dict], 
                                       golden_data: List[Dict],
                                       split_type: str = "train",
                                       enable_execution: bool = False) -> List[Dict]:
        """转换多轮数据为增强的单轮格式，包含真实执行轨迹"""
        result = []
        
        # 创建golden_data的索引
        golden_map = {item['id']: item for item in golden_data}
        
        for idx, original_item in enumerate(original_data):
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
            
            print(f"\n处理项目 {item_id} ({idx+1}/{len(original_data)})")
            
            # 如果有initial_config，使用它模拟执行
            execution_history = []
            if initial_config and enable_execution:
                try:
                    execution_history = self.simulate_multi_turn_execution(initial_config, golden_answers)
                except Exception as e:
                    print(f"执行模拟失败: {e}")
                    execution_history = []
            elif not enable_execution:
                print(f"  跳过真实执行（enable_execution=False）")
            
            # 处理每一轮对话
            for turn_idx, turn_questions in enumerate(questions):
                for q_idx, question_msg in enumerate(turn_questions):
                    if question_msg['role'] == 'user':
                        
                        # 生成对话历史
                        conversation_history = self.generate_conversation_history(questions, execution_history, turn_idx)
                        
                        # 构建prompt内容
                        prompt_content = "You are a helpful assistant that can use tools to help users."
                        if conversation_history:
                            # 将历史对话添加到prompt中
                            history_text = "\n\nPrevious conversation:\n"
                            for msg in conversation_history:
                                if msg['role'] == 'user':
                                    history_text += f"User: {msg['content']}\n"
                                elif msg['role'] == 'assistant':
                                    history_text += f"Assistant: {msg['content']}\n"
                                elif msg['role'] == 'tool':
                                    history_text += f"Tool Result: {msg['content']}\n"
                            prompt_content += history_text
                        
                        prompt_content += f"\n\nCurrent request: {question_msg['content']}"
                        
                        # 获取当前轮的golden answer并转换格式
                        current_golden = golden_answers[turn_idx] if turn_idx < len(golden_answers) else []
                        current_golden = self.convert_golden_answers(current_golden)
                        
                        # 映射类名
                        mapped_classes = self.map_involved_classes(involved_classes)
                        
                        # 获取当前轮的initial_config
                        if turn_idx < len(execution_history) and execution_history[turn_idx]['scenario_before']:
                            # 使用真实执行中保存的场景状态
                            current_scenario = execution_history[turn_idx]['scenario_before']
                        else:
                            # 使用原始initial_config
                            current_scenario = initial_config
                        
                        mapped_initial_config = self.map_initial_config_classes(current_scenario)
                        
                        # 创建符合要求的数据格式
                        single_turn_item = {
                            "id": f"{item_id}_turn_{turn_idx}_{q_idx}",
                            "question": question_msg['content'],
                            "golden_answers": current_golden,
                            "data_source": "BFCL_multi_turn_base",
                            "prompt": [
                                {
                                    "content": prompt_content,
                                    "role": "user"
                                }
                            ],
                            "ability": "tool_use",
                            "reward_model": {
                                "ground_truth": json.dumps(current_golden, ensure_ascii=False),
                                "style": "rule"
                            },
                            "extra_info": {
                                "index": len(result),
                                "split": split_type,
                                "involved_class": mapped_classes,
                                "initial_config": mapped_initial_config,
                            #     "original_id": item_id,
                            #     "turn_index": turn_idx,
                            #     "question_index": q_idx,
                            #     "execution_history": execution_history[turn_idx] if turn_idx < len(execution_history) else None,
                            #     "realistic_trace": len(execution_history) > 0
                            }
                        }
                        
                        result.append(single_turn_item)
        
        return result
    
    def save_to_json(self, data: List[Dict], output_file: str):
        """保存数据到JSON文件"""
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    def save_to_csv(self, data: List[Dict], output_file: str):
        """保存数据到CSV文件 - 保持JSON字段为原始格式"""
        if not data:
            print("No data to save")
            return
        
        fieldnames = ["id", "question", "golden_answers", "data_source", "prompt", "ability", "reward_model", "extra_info"]
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for item in data:
                # 直接使用原始数据，不转换为JSON字符串
                row = {
                    "id": item["id"],
                    "question": item["question"],
                    "golden_answers": item["golden_answers"],  # 保持原始list格式
                    "data_source": item["data_source"],
                    "prompt": item["prompt"],  # 保持原始list格式
                    "ability": item["ability"],
                    "reward_model": item["reward_model"],  # 保持原始dict格式
                    "extra_info": item["extra_info"]  # 保持原始dict格式
                }
                writer.writerow(row)
    
    def save_to_parquet(self, data: List[Dict], output_file: str):
        """保存数据到Parquet文件 - 为了兼容性，复杂对象转换为JSON字符串"""
        if not data:
            print("No data to save")
            return
        
        try:
            # 创建DataFrame - 为了Parquet兼容性，将复杂对象转换为JSON字符串
            df_data = []
            for item in data:
                row = {
                    "id": item["id"],
                    "question": item["question"],
                    "golden_answers": json.dumps(item["golden_answers"], ensure_ascii=False),
                    "data_source": item["data_source"],
                    "prompt": json.dumps(item["prompt"], ensure_ascii=False),
                    "ability": item["ability"],
                    "reward_model": json.dumps(item["reward_model"], ensure_ascii=False),
                    "extra_info": json.dumps(item["extra_info"], ensure_ascii=False)
                }
                df_data.append(row)
            
            df = pd.DataFrame(df_data)
            df.to_parquet(output_file, index=False)
            print(f"已保存 {len(data)} 条数据到 {output_file}")
            
        except ImportError:
            print("警告：缺少pyarrow依赖，无法保存Parquet文件。请安装：pip install pyarrow")
        except Exception as e:
            print(f"保存Parquet文件时出错: {e}")
    
    def save_to_parquet_with_native_types(self, data: List[Dict], output_file: str):
        """保存数据到Parquet文件 - 使用PyArrow结构化类型保持原生格式"""
        if not data:
            print("No data to save")
            return
        
        try:
            # 使用pyarrow的结构化类型来保存复杂数据
            import pyarrow as pa
            import pyarrow.parquet as pq
            
            # 数据清理：确保类型一致性
            cleaned_data = []
            for item in data:
                cleaned_item = item.copy()
                
                # 修复空的golden_answers列表 - 添加占位符以保持类型一致
                if not cleaned_item['golden_answers']:
                    cleaned_item['golden_answers'] = [""]  # 空字符串而不是空列表
                
                # 确保prompt不为空
                if not cleaned_item['prompt']:
                    cleaned_item['prompt'] = [{"content": "", "role": "user"}]
                
                # 确保reward_model结构完整
                if not isinstance(cleaned_item['reward_model'], dict):
                    cleaned_item['reward_model'] = {"ground_truth": "", "style": "rule"}
                
                # 处理extra_info结构，将复杂的initial_config转换为JSON字符串
                if not isinstance(cleaned_item['extra_info'], dict):
                    cleaned_item['extra_info'] = {
                        "index": 0, 
                        "split": "unknown", 
                        "involved_class": [], 
                        "initial_config": "{}"  # 空JSON字符串
                    }
                else:
                    # 将initial_config转换为JSON字符串，保持数据完整性
                    initial_config = cleaned_item['extra_info'].get('initial_config', {})
                    if isinstance(initial_config, dict):
                        initial_config_str = json.dumps(initial_config, ensure_ascii=False)
                    else:
                        initial_config_str = str(initial_config)
                    
                    processed_extra_info = {
                        "index": cleaned_item['extra_info'].get('index', 0),
                        "split": cleaned_item['extra_info'].get('split', 'unknown'),
                        "involved_class": cleaned_item['extra_info'].get('involved_class', []),
                        "initial_config": initial_config_str  # 转换为JSON字符串
                    }
                    cleaned_item['extra_info'] = processed_extra_info
                
                cleaned_data.append(cleaned_item)
            
            print(f"数据清理完成：处理了 {len(cleaned_data)} 条记录")
            
            # 创建DataFrame
            df = pd.DataFrame(cleaned_data)
            
            # 让PyArrow自动推断schema，这样可以保持原生类型
            # 这与nq_search文件使用的方法类似
            table = pa.Table.from_pandas(df, preserve_index=False)
            
            # 保存到Parquet
            pq.write_table(table, output_file)
            print(f"已保存 {len(data)} 条数据到 {output_file} (原生类型格式)")
            
            # 验证保存的数据
            df_read = pd.read_parquet(output_file)
            sample_row = df_read.iloc[0] if len(df_read) > 0 else None
            if sample_row is not None:
                print(f"验证 - golden_answers类型: {type(sample_row['golden_answers'])}")
                print(f"验证 - extra_info类型: {type(sample_row['extra_info'])}")
            
        except ImportError:
            print("警告：缺少pyarrow依赖，回退到标准方法")
            self.save_to_parquet(data, output_file)
        except Exception as e:
            print(f"原生类型保存失败，回退到标准方法: {e}")
            print(f"错误详情: {str(e)}")
            self.save_to_parquet(data, output_file)
    
    def save_train_test_separately(self, train_data: List[Dict], test_data: List[Dict], output_dir: Path):
        """分别保存训练数据和测试数据为Parquet文件"""
        if train_data:
            train_parquet = output_dir / 'train.parquet'
            self.save_to_parquet_with_native_types(train_data, str(train_parquet))
        
        if test_data:
            test_parquet = output_dir / 'test.parquet'
            self.save_to_parquet_with_native_types(test_data, str(test_parquet))
    

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='增强的多轮对话转换器')
    parser.add_argument('--enable-execution', action='store_true', 
                       help='启用真实工具执行以生成历史轨迹（需要更多时间）')
    parser.add_argument('--num-items', type=int, default=500,
                       help='处理的数据项数量（默认500个）')
    parser.add_argument('--test-nums', type=int, default=30,
                       help='测试集数量，从总数据中划分出指定数量作为测试集（默认0，全部作为训练集）')
    
    args = parser.parse_args()
    
    print("🚀 启动增强的多轮对话转换器")
    print("="*80)
    
    # 文件路径
    original_file = "/home/ma-user/work/RL-Factory/data/BFCL/multi-turn-original/BFCL_v3_multi_turn_base.json"
    golden_answer_file = "/home/ma-user/work/RL-Factory/data/BFCL/possible_answer/BFCL_v3_multi_turn_base.json"
    
    # 输出文件路径
    output_dir = Path('/home/ma-user/work/RL-Factory/data/BFCL/multi-turn')
    output_dir.mkdir(exist_ok=True)
    
    # 根据参数构建输出文件名
    base_name = 'enhanced_single_turn_data'
    if args.enable_execution:
        base_name += '_with_execution'
    if args.test_nums > 0:
        base_name += f'_train{args.num_items - args.test_nums}_test{args.test_nums}'
    else:
        base_name += f'_train{args.num_items}'
    
    output_json = output_dir / f'{base_name}.json'
    output_csv = output_dir / f'{base_name}.csv'
    
    # 创建转换器
    converter = EnhancedMultiTurnConverter()
    
    try:
        print("加载数据...")
        original_data, golden_data = converter.load_data(original_file, golden_answer_file)
        print(f"加载了 {len(original_data)} 个原始项目和 {len(golden_data)} 个golden answer项目")
        
        if args.enable_execution:
            print(f"\n⚠️  启用真实执行模式，这将需要更多时间...")
            print(f"正在处理前 {args.num_items} 个项目...")
        else:
            print(f"\n快速模式：跳过真实执行，处理前 {args.num_items} 个项目...")
        
        print("\n转换为增强的单轮格式...")
        # 可以指定处理前N个项目进行测试
        process_data = original_data[:args.num_items]
        
        # 划分训练测试集
        if args.test_nums > 0:
            train_data, test_data = converter.split_train_test(process_data, args.test_nums)
            print(f"将处理 {len(train_data)} 个训练项目和 {len(test_data)} 个测试项目")
        else:
            train_data = process_data
            test_data = []
            print(f"将处理 {len(train_data)} 个训练项目（无测试集）")
        
        # 转换训练数据
        train_single_turn = []
        test_single_turn = []
        
        if train_data:
            print("正在转换训练数据...")
            train_single_turn = converter.convert_to_enhanced_single_turn(
                train_data, golden_data, "train", enable_execution=args.enable_execution)
            print(f"训练数据转换完成，生成了 {len(train_single_turn)} 个单轮训练数据项")
        
        # 转换测试数据
        if test_data:
            print("正在转换测试数据...")
            test_single_turn = converter.convert_to_enhanced_single_turn(
                test_data, golden_data, "test", enable_execution=args.enable_execution)
            print(f"测试数据转换完成，生成了 {len(test_single_turn)} 个单轮测试数据项")
        
        # 合并所有数据用于传统格式保存
        single_turn_data = train_single_turn + test_single_turn
        
        print(f"\n转换完成，生成了 {len(single_turn_data)} 个单轮数据项")
        
        print("保存结果...")
        # 保存传统格式（包含所有数据）
        converter.save_to_json(single_turn_data, str(output_json))
        converter.save_to_csv(single_turn_data, str(output_csv))
        
        # 分别保存训练集和测试集为Parquet格式
        print("保存Parquet格式...")
        converter.save_train_test_separately(train_single_turn, test_single_turn, output_dir)
        
        print(f"\n✅ 转换完成！")
        print(f"JSON输出: {output_json}")
        print(f"CSV输出: {output_csv}")
        if train_single_turn:
            print(f"训练集Parquet: {output_dir / 'train.parquet'}")
        if test_single_turn:
            print(f"测试集Parquet: {output_dir / 'test.parquet'}")
        
        # 显示示例
        if single_turn_data:
            print("\n📋 示例输出:")
            example = single_turn_data[0]
            print(f"ID: {example['id']}")
            print(f"Question: {example['question']}")
            print(f"Golden Answers: {example['golden_answers']}")
            print(f"Data Source: {example['data_source']}")
            print(f"Ability: {example['ability']}")
            print(f"Reward Model: {example['reward_model']}")
            print(f"Extra Info Keys: {list(example['extra_info'].keys())}")
        
        # 显示使用说明
        print(f"\n📖 使用说明:")
        print(f"基础模式（快速）: python {__file__}")
        print(f"执行模式（慢速）: python {__file__} --enable-execution")
        print(f"处理更多项目: python {__file__} --num-items 100")
        print(f"划分测试集: python {__file__} --num-items 100 --test-nums 20")
        print(f"完整执行: python {__file__} --enable-execution --num-items 10 --test-nums 2")
        
    except Exception as e:
        print(f"❌ 处理过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
