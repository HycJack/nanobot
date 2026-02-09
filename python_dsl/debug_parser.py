#!/usr/bin/env python3
"""
调试脚本 - 查看解析结果
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import ParserInterface, AlgebraProcessor


def test_parser():
    """测试解析器"""
    print("=" * 60)
    print("测试解析器")
    print("=" * 60)
    
    parser = ParserInterface()
    
    test_cases = [
        "Length(Line(Point(1,1), Point(2,2)))",
        "Point(1, 2)",
        "A = Point(1, 2)",
        "B = Point(3, 4)",
        "Line((1, 2), (3, 4))"
    ]
    
    for test_case in test_cases:
        print(f"\n解析: {test_case}")
        try:
            parsed = parser.parse_geogebra_expression(test_case)
            print(f"  类型: {parsed.type}")
            print(f"  值: {parsed.value}")
            print(f"  标签: {parsed.label}")
            print(f"  子节点: {parsed.children}")
        except Exception as e:
            print(f"  错误: {e}")
            import traceback
            traceback.print_exc()
    
    print()


def test_processor():
    """测试处理器"""
    print("=" * 60)
    print("测试处理器")
    print("=" * 60)
    
    processor = AlgebraProcessor()
    
    test_cases = [
        "Point(1, 2)",
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
            print(f"  错误: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    print()


if __name__ == "__main__":
    test_parser()
    test_processor()