#!/usr/bin/env python3
"""
简单测试 - 验证命令查找
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import Commands


def test_command_lookup():
    """测试命令查找"""
    print("=" * 60)
    print("测试命令查找")
    print("=" * 60)
    
    # 测试不同的命令名称
    test_names = [
        "Point",
        "POINT",
        "point",
        "Line",
        "LINE",
        "Sum",
        "SUM",
        "Mean"
    ]
    
    for name in test_names:
        cmd = Commands.get_by_name(name)
        if cmd:
            print(f"✓ '{name}' -> {cmd} (category: {cmd.category.name})")
        else:
            print(f"✗ '{name}' -> 未找到")
    
    print()
    
    # 打印所有命令
    print("=" * 60)
    print("所有命令列表")
    print("=" * 60)
    
    for cmd in Commands:
        print(f"  {cmd.cmdName} (category: {cmd.category.name})")
    
    print()


if __name__ == "__main__":
    test_command_lookup()