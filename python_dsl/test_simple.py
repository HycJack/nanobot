#!/usr/bin/env python3
"""
简单测试脚本 - 验证命令查找是否正常工作
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import AlgebraProcessor, Commands


def test_command_lookup():
    """测试命令查找"""
    print("=" * 60)
    print("测试1：命令查找")
    print("=" * 60)
    
    # 测试get_by_name方法
    point_cmd = Commands.get_by_name("Point")
    print(f"Commands.get_by_name('Point') = {point_cmd}")
    print(f"  类型: {type(point_cmd)}")
    print(f"  名称: {point_cmd.cmdName}")
    print(f"  类别: {point_cmd.category}")
    
    line_cmd = Commands.get_by_name("Line")
    print(f"\nCommands.get_by_name('Line') = {line_cmd}")
    print(f"  类型: {type(line_cmd)}")
    print(f"  名称: {line_cmd.cmdName}")
    print(f"  类别: {line_cmd.category}")
    
    unknown_cmd = Commands.get_by_name("UnknownCommand")
    print(f"\nCommands.get_by_name('UnknownCommand') = {unknown_cmd}")
    
    print()


def test_basic_commands():
    """测试基本命令执行"""
    print("=" * 60)
    print("测试2：基本命令执行")
    print("=" * 60)
    
    processor = AlgebraProcessor()
    
    test_cases = [
        "Point(1, 2)",
        "Line((1, 2), (3, 4))",
        "Sum(1, 2, 3)",
        "Mean(10, 20, 30)"
    ]
    
    for test_case in test_cases:
        print(f"\n执行: {test_case}")
        try:
            result = processor.process_algebra_command(test_case)
            print(f"  结果: {result}")
        except Exception as e:
            print(f"  错误: {e}")
            import traceback
            traceback.print_exc()
    
    print()


def test_assignments():
    """测试变量赋值"""
    print("=" * 60)
    print("测试3：变量赋值")
    print("=" * 60)
    
    processor = AlgebraProcessor()
    
    test_cases = [
        "A = Point(1, 2)",
        "B = Point(3, 4)",
        "Line(A, B)"
    ]
    
    for test_case in test_cases:
        print(f"\n执行: {test_case}")
        try:
            result = processor.process_algebra_command(test_case)
            print(f"  结果: {result}")
        except Exception as e:
            print(f"  错误: {e}")
            import traceback
            traceback.print_exc()
    
    print()


def test_error_handling():
    """测试错误处理"""
    print("=" * 60)
    print("测试4：错误处理")
    print("=" * 60)
    
    processor = AlgebraProcessor()
    
    test_cases = [
        "UnknownCommand(1, 2)",
        "Point(1)",
        "Point(1, 2, 3, 4)"
    ]
    
    for test_case in test_cases:
        print(f"\n执行: {test_case}")
        try:
            result = processor.process_algebra_command(test_case)
            print(f"  结果: {result}")
        except Exception as e:
            print(f"  错误: {type(e).__name__}: {e}")
    
    print()


def test_command_categories():
    """测试命令分类"""
    print("=" * 60)
    print("测试5：命令分类")
    print("=" * 60)
    
    geometry_commands = [
        "Point", "Line", "Segment", "Circle", "Intersect", "Distance", "Length",
        "Angle", "Midpoint", "Polygon", "Area", "Centroid"
    ]
    
    algebra_commands = [
        "Sum", "Mean", "Min", "Max", "Mod", "GCD", "LCM"
    ]
    
    print("\n几何命令:")
    for cmd_name in geometry_commands:
        cmd = Commands.get_by_name(cmd_name)
        if cmd:
            print(f"  {cmd_name}: {cmd.category.name}")
        else:
            print(f"  {cmd_name}: 未找到")
    
    print("\n代数命令:")
    for cmd_name in algebra_commands:
        cmd = Commands.get_by_name(cmd_name)
        if cmd:
            print(f"  {cmd_name}: {cmd.category.name}")
        else:
            print(f"  {cmd_name}: 未找到")
    
    print()


if __name__ == "__main__":
    test_command_lookup()
    test_basic_commands()
    test_assignments()
    test_error_handling()
    test_command_categories()
    
    print("=" * 60)
    print("所有测试完成")
    print("=" * 60)