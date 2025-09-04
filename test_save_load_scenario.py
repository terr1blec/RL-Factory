import json
import pprint
from ast import literal_eval
from omegaconf import OmegaConf
from envs.tool_manager.qwen3_manager import QwenManager

def create_qwen_manager():
    """创建QwenManager实例"""
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
    manager = QwenManager(verl_config)
    
    print(f"已加载工具数量: {len(manager.all_tools)}")
    return manager

def execute_tool(manager, tool_name, args):
    """执行单个工具"""
    response_content = f"""
<tool_call>
{{"name": "{tool_name}", "arguments": {json.dumps(args, ensure_ascii=False)}}}
</tool_call>
"""
    
    actions, results = manager.execute_actions([response_content])
    return results[0] if results else None

def test_scenario_1_workspace_project():
    """测试场景1：基于训练数据的workspace项目场景"""
    print("="*60)
    print("测试场景1：Workspace项目管理场景")
    print("="*60)
    
    manager = create_qwen_manager()
    
    # 1. 加载初始场景（参考训练数据）
    print("\n1. 加载初始workspace场景...")
    initial_scenario = {
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
    
    result = execute_tool(manager, 'file_system-load_scenario', {"scenario": initial_scenario})
    print(f"加载结果: {result}")
    
    # 2. 验证加载成功
    print("\n2. 验证场景加载成功...")
    pwd_result = execute_tool(manager, 'file_system-pwd', {})
    print(f"当前目录: {pwd_result}")
    
    ls_result = execute_tool(manager, 'file_system-ls', {'show_hidden': False})
    print(f"目录内容: {ls_result}")
    
    # 3. 进行一些文件操作
    print("\n3. 执行文件操作...")
    
    # 切换到document目录
    cd_result = execute_tool(manager, 'file_system-cd', {'folder': 'document'})
    print(f"切换目录: {cd_result}")
    
    # 创建temp目录
    mkdir_result = execute_tool(manager, 'file_system-mkdir', {'dir_name': 'temp'})
    print(f"创建temp目录: {mkdir_result}")
    
    # 移动文件到temp目录
    mv_result = execute_tool(manager, 'file_system-mv', {'source': 'final_report.pdf', 'destination': 'temp'})
    print(f"移动文件: {mv_result}")
    
    # 创建新文件
    touch_result = execute_tool(manager, 'file_system-touch', {'file_name': 'project_notes.txt'})
    print(f"创建文件: {touch_result}")
    
    # 写入内容
    echo_result = execute_tool(manager, 'file_system-echo', {
        'content': 'Project management notes:\n- Budget analysis completed\n- Reports organized\n- Archive system established',
        'file_name': 'project_notes.txt'
    })
    print(f"写入内容: {echo_result}")
    
    # 4. 保存当前场景
    print("\n4. 保存当前场景...")
    saved_scenario = execute_tool(manager, 'file_system-save_scenario', {})
    print("保存的场景结构:")
    if saved_scenario and len(saved_scenario) > 0:
        # 提取实际的场景数据
        scenario_content = saved_scenario[0]['content']
        if "The result is:" in scenario_content:
            scenario_str = scenario_content.split("The result is:\n", 1)[1]
            try:
                # 尝试解析为Python对象
                scenario_dict = eval(scenario_str)
                pprint.pprint(scenario_dict, width=80, depth=4)
                
                # 保存到文件以便后续加载
                with open('/home/ma-user/work/RL-Factory/tmp/saved_scenario.json', 'w', encoding='utf-8') as f:
                    json.dump(scenario_dict, f, indent=2, ensure_ascii=False)
                print("\n场景已保存到 /tmp/saved_scenario.json")
                
                return scenario_dict
            except:
                print(f"场景数据: {scenario_str}")
                return scenario_str
    
    return None

def test_scenario_2_alex_workspace():
    """测试场景2：基于Alex的workspace场景"""
    print("="*60)
    print("测试场景2：Alex的工作空间场景")
    print("="*60)
    
    manager = create_qwen_manager()
    
    # 1. 加载Alex的场景
    print("\n1. 加载Alex的workspace场景...")
    alex_scenario = {
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
    
    result = execute_tool(manager, 'file_system-load_scenario', {"scenario": alex_scenario})
    print(f"加载结果: {result}")
    
    # 2. 执行一系列操作（模拟训练数据中的操作序列）
    print("\n2. 执行文件操作序列...")
    
    # 列出所有文件（包括隐藏文件）
    ls_result = execute_tool(manager, 'file_system-ls', {'show_hidden': True})
    print(f"列出所有文件: {ls_result}")
    
    # 进入workspace
    cd_result = execute_tool(manager, 'file_system-cd', {'folder': 'workspace'})
    print(f"进入workspace: {cd_result}")
    
    # 移动log.txt到archive
    mv_result = execute_tool(manager, 'file_system-mv', {'source': 'log.txt', 'destination': 'archive'})
    print(f"移动log.txt: {mv_result}")
    
    # 进入archive目录
    cd_result = execute_tool(manager, 'file_system-cd', {'folder': 'archive'})
    print(f"进入archive: {cd_result}")
    
    # 在log.txt中搜索Error
    grep_result = execute_tool(manager, 'file_system-grep', {'file_name': 'log.txt', 'pattern': 'Error'})
    print(f"搜索Error: {grep_result}")
    
    # 显示文件最后20行
    tail_result = execute_tool(manager, 'file_system-tail', {'file_name': 'log.txt', 'lines': 20})
    print(f"显示最后20行: {tail_result}")
    
    # 3. 保存修改后的场景
    print("\n3. 保存修改后的场景...")
    saved_scenario = execute_tool(manager, 'file_system-save_scenario', {})
    print("保存的场景结构:")
    if saved_scenario and len(saved_scenario) > 0:
        scenario_content = saved_scenario[0]['content']
        if "The result is:" in scenario_content:
            scenario_str = scenario_content.split("The result is:\n", 1)[1]
            try:
                scenario_dict = eval(scenario_str)
                pprint.pprint(scenario_dict, width=80, depth=4)
                
                with open('/tmp/alex_saved_scenario.json', 'w', encoding='utf-8') as f:
                    json.dump(scenario_dict, f, indent=2, ensure_ascii=False)
                print("\n场景已保存到 /tmp/alex_saved_scenario.json")
                
                return scenario_dict
            except:
                print(f"场景数据: {scenario_str}")
                return scenario_str
    
    return None

def test_load_saved_scenario():
    """测试加载保存的场景"""
    print("="*60)
    print("测试场景3：加载之前保存的场景")
    print("="*60)
    
    try:
        # 读取保存的场景
        with open('/tmp/saved_scenario.json', 'r', encoding='utf-8') as f:
            saved_scenario = json.load(f)
        
        print("从文件加载的场景:")
        pprint.pprint(saved_scenario, width=80, depth=3)
        
        manager = create_qwen_manager()
        
        # 加载保存的场景
        print("\n加载保存的场景...")
        result = execute_tool(manager, 'file_system-load_scenario', {"scenario": saved_scenario})
        print(f"加载结果: {result}")
        
        # 验证场景恢复
        print("\n验证场景恢复...")
        pwd_result = execute_tool(manager, 'file_system-pwd', {})
        print(f"当前目录: {pwd_result}")
        
        ls_result = execute_tool(manager, 'file_system-ls', {'show_hidden': False})
        print(f"目录内容: {ls_result}")
        
        # 尝试访问之前创建的文件
        cat_result = execute_tool(manager, 'file_system-cat', {'file_name': 'project_notes.txt'})
        print(f"读取project_notes.txt: {cat_result}")
        
        # 检查temp目录
        cd_result = execute_tool(manager, 'file_system-cd', {'folder': 'temp'})
        print(f"进入temp目录: {cd_result}")
        
        ls_temp = execute_tool(manager, 'file_system-ls', {'show_hidden': False})
        print(f"temp目录内容: {ls_temp}")
        
        return True
        
    except FileNotFoundError:
        print("未找到保存的场景文件，请先运行test_scenario_1_workspace_project()")
        return False
    except Exception as e:
        print(f"加载场景时出错: {e}")
        return False

def test_data_integrity():
    """测试数据完整性"""
    print("="*60)
    print("测试场景4：数据完整性验证")
    print("="*60)
    
    manager = create_qwen_manager()
    
    # 创建复杂的场景用于测试
    complex_scenario = {
        "root": {
            "test_project": {
                "type": "directory",
                "contents": {
                    "src": {
                        "type": "directory",
                        "contents": {
                            "main.py": {
                                "type": "file",
                                "content": "#!/usr/bin/env python3\n\ndef main():\n    print('Hello, World!')\n\nif __name__ == '__main__':\n    main()"
                            },
                            "utils.py": {
                                "type": "file",
                                "content": "# Utility functions\n\ndef helper():\n    return 'Helper function'"
                            }
                        }
                    },
                    "docs": {
                        "type": "directory",
                        "contents": {
                            "README.md": {
                                "type": "file",
                                "content": "# Test Project\n\nThis is a test project for scenario saving/loading.\n\n## Features\n- File operations\n- Directory management\n- Content preservation"
                            }
                        }
                    },
                    "data": {
                        "type": "directory",
                        "contents": {
                            "config.json": {
                                "type": "file",
                                "content": '{\n  "name": "test_project",\n  "version": "1.0.0",\n  "description": "A test project for validation"\n}'
                            }
                        }
                    }
                }
            }
        }
    }
    
    print("\n1. 加载复杂场景...")
    result = execute_tool(manager, 'file_system-load_scenario', {"scenario": complex_scenario})
    print(f"加载结果: {result}")
    
    # 验证各个文件的内容
    print("\n2. 验证文件内容...")
    
    # 检查main.py
    cd_result = execute_tool(manager, 'file_system-cd', {'folder': 'src'})
    cat_result = execute_tool(manager, 'file_system-cat', {'file_name': 'main.py'})
    print(f"main.py内容: {cat_result}")
    
    # 检查config.json
    cd_result = execute_tool(manager, 'file_system-cd', {'folder': '..'})
    cd_result = execute_tool(manager, 'file_system-cd', {'folder': 'data'})
    cat_result = execute_tool(manager, 'file_system-cat', {'file_name': 'config.json'})
    print(f"config.json内容: {cat_result}")
    
    # 3. 保存场景
    print("\n3. 保存复杂场景...")
    saved_scenario = execute_tool(manager, 'file_system-save_scenario', {})
    
    if saved_scenario and len(saved_scenario) > 0:
        scenario_content = saved_scenario[0]['content']
        if "The result is:" in scenario_content:
            scenario_str = scenario_content.split("The result is:\n", 1)[1]
            try:
                scenario_dict = eval(scenario_str)
                
                # 保存到文件
                with open('/tmp/complex_scenario.json', 'w', encoding='utf-8') as f:
                    json.dump(scenario_dict, f, indent=2, ensure_ascii=False)
                
                print("复杂场景已保存")
                
                # 4. 重新加载并验证
                print("\n4. 重新加载并验证数据完整性...")
                manager2 = create_qwen_manager()
                
                reload_result = execute_tool(manager2, 'file_system-load_scenario', {"scenario": scenario_dict})
                print(f"重新加载结果: {reload_result}")
                
                # 验证文件内容是否保持一致
                cd_result = execute_tool(manager2, 'file_system-cd', {'folder': 'src'})
                cat_result = execute_tool(manager2, 'file_system-cat', {'file_name': 'main.py'})
                
                original_main_py = complex_scenario["root"]["test_project"]["contents"]["src"]["contents"]["main.py"]["content"]
                
                # 提取实际的文件内容
                if cat_result and len(cat_result) > 0:
                    result_content = cat_result[0]['content']
                    if "file_content" in result_content:
                        # 提取文件内容部分
                        try:
                            # 查找file_content字段
                            import re
                            match = re.search(r"'file_content': \"([^\"]*(?:\\.[^\"]*)*)\"", result_content)
                            if match:
                                loaded_content = match.group(1)
                                # 将转义的换行符还原
                                loaded_content = loaded_content.replace('\\n', '\n').replace("\\'", "'")
                                
                                print(f"原始内容:\n{repr(original_main_py)}")
                                print(f"加载后内容:\n{repr(loaded_content)}")
                                
                                if original_main_py == loaded_content:
                                    print("✅ 数据完整性验证通过！")
                                    return True
                                else:
                                    print("❌ 数据完整性验证失败！")
                                    print("内容不匹配")
                                    return False
                        except Exception as e:
                            print(f"解析文件内容时出错: {e}")
                            print(f"原始结果: {result_content}")
                            return False
                
                print("❌ 无法提取文件内容进行比较")
                return False
                    
            except Exception as e:
                print(f"处理保存的场景时出错: {e}")
                return False
    
    return False

def run_all_tests():
    """运行所有测试"""
    print("🚀 开始Save/Load场景功能完整测试")
    print("="*80)
    
    results = []
    
    try:
        # 测试1：基础workspace场景
        print("\n" + "🔄" * 20 + " 测试1 " + "🔄" * 20)
        result1 = test_scenario_1_workspace_project()
        results.append(("Workspace场景测试", result1 is not None))
        
        # 测试2：Alex场景
        print("\n" + "🔄" * 20 + " 测试2 " + "🔄" * 20)
        result2 = test_scenario_2_alex_workspace()
        results.append(("Alex场景测试", result2 is not None))
        
        # 测试3：加载保存的场景
        print("\n" + "🔄" * 20 + " 测试3 " + "🔄" * 20)
        result3 = test_load_saved_scenario()
        results.append(("加载保存场景测试", result3))
        
        # 测试4：数据完整性
        print("\n" + "🔄" * 20 + " 测试4 " + "🔄" * 20)
        result4 = test_data_integrity()
        results.append(("数据完整性测试", result4))
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    
    # 输出测试结果总结
    print("\n" + "📊" * 20 + " 测试结果总结 " + "📊" * 20)
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\n总结: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有测试都通过了！save_scenario和load_scenario功能工作正常。")
    else:
        print("⚠️ 部分测试失败，请检查相关功能。")

if __name__ == "__main__":
    run_all_tests()
