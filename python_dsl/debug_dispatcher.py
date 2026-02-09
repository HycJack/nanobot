#!/usr/bin/env python3
"""
调试脚本 - 测试命令处理
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import Commands, CommandDispatcher


def test_dispatcher():
    """测试调度器"""
    print("=" * 60)
    print("测试调度器")
    print("=" * 60)
    
    dispatcher = CommandDispatcher()
    
    # 测试命令查找
    print("\n1. 测试命令查找:")
    cmd = Commands.get_by_name("Point")
    print(f"  Commands.get_by_name('Point') = {cmd}")
    
    # 测试调度器的命令表
    print("\n2. 测试调度器的命令表:")
    print(f"  'Point' in command_table: {'Point' in dispatcher._command_table}")
    print(f"  'Line' in command_table: {'Line' in dispatcher._command_table}")
    print(f"  'Sum' in command_table: {'Sum' in dispatcher._command_table}")
    
    # 打印命令表中的所有命令
    print("\n3. 命令表中的所有命令:")
    for cmd_name in sorted(dispatcher._command_table.keys()):
        print(f"  {cmd_name}")
    
    # 测试命令执行
    print("\n4. 测试命令执行:")
    test_cases = [
        ("Point", [1, 2]),
        ("Line", [(1, 2), (3, 4)]),
        ("Sum", [1, 2, 3])
    ]
    
    for cmd_name, args in test_cases:
        print(f"\n  执行: {cmd_name}{args}")
        try:
            from core import EvalInfo
            info = EvalInfo(label_output=True, allow_redefinition=True)
            result = dispatcher.process_command(cmd_name, args, info)
            print(f"    结果: {result}")
        except Exception as e:
            print(f"    错误: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    print()


if __name__ == "__main__":
    test_dispatcher()