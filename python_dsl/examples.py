#!/usr/bin/env python3
"""
GeoGebra DSL Python Implementation - Examples and Tests

这个文件展示了如何使用Python版本的GeoGebra DSL验证系统。
"""

from core import (
    AlgebraProcessor,
    Commands,
    CommandCategory,
    ExamModeFilter,
    CASFilter,
    ArgumentCountFilter,
    ArgumentTypeFilter,
    EvalInfo,
    CommandError,
    InvalidInputError
)


def example_1_basic_commands():
    """示例1：基本命令处理"""
    print("=" * 60)
    print("示例1：基本命令处理")
    print("=" * 60)
    
    processor = AlgebraProcessor()
    
    try:
        result = processor.process_algebra_command("Point(1, 2)")
        print(f"Point(1, 2) -> {result}")
        
        result = processor.process_algebra_command("Line((1, 2), (3, 4))")
        print(f"Line((1, 2), (3, 4)) -> {result}")
        
        result = processor.process_algebra_command("Sum(1, 2, 3, 4, 5)")
        print(f"Sum(1, 2, 3, 4, 5) -> {result}")
        
        result = processor.process_algebra_command("Mean(10, 20, 30)")
        print(f"Mean(10, 20, 30) -> {result}")
        
    except CommandError as e:
        print(f"命令错误: {e}")
    
    print()


def example_2_assignments():
    """示例2：变量赋值"""
    print("=" * 60)
    print("示例2：变量赋值")
    print("=" * 60)
    
    processor = AlgebraProcessor()
    
    try:
        result = processor.process_algebra_command("A = Point(1, 2)")
        print(f"A = Point(1, 2) -> {result}")
        
        result = processor.process_algebra_command("B = Point(3, 4)")
        print(f"B = Point(3, 4) -> {result}")
        
        result = processor.process_algebra_command("Line(A, B)")
        print(f"Line(A, B) -> {result}")
        
        elements = processor.get_all_elements()
        print(f"\n所有定义的元素: {list(elements.keys())}")
        
    except CommandError as e:
        print(f"命令错误: {e}")
    
    print()


def example_3_error_handling():
    """示例3：错误处理"""
    print("=" * 60)
    print("示例3：错误处理")
    print("=" * 60)
    
    processor = AlgebraProcessor()
    
    test_cases = [
        "UnknownCommand(1, 2)",
        "Point(1)",
        "Point(1, 2, 3, 4)",
        "Sum(1, 'abc')",
        "A = Point(1, 2)\nA = Point(3, 4)"
    ]
    
    for test_case in test_cases:
        print(f"测试: {test_case}")
        try:
            result = processor.process_algebra_command(test_case)
            print(f"  结果: {result}")
        except CommandError as e:
            print(f"  错误: {e}")
        print()


def example_4_command_filters():
    """示例4：命令过滤器"""
    print("=" * 60)
    print("示例4：命令过滤器")
    print("=" * 60)
    
    processor = AlgebraProcessor()
    
    allowed_commands = [Commands.POINT, Commands.LINE, Commands.SEGMENT]
    exam_filter = ExamModeFilter(allowed_commands)
    processor.get_cmd_dispatcher().add_command_filter(exam_filter)
    
    print("允许的命令: Point, Line, Segment")
    
    test_cases = [
        "Point(1, 2)",
        "Line((1, 2), (3, 4))",
        "Segment((1, 2), (3, 4))",
        "Circle((0, 0), 5)"
    ]
    
    for test_case in test_cases:
        print(f"测试: {test_case}")
        try:
            result = processor.process_algebra_command(test_case)
            print(f"  结果: {result}")
        except CommandError as e:
            print(f"  错误: {e}")
        print()
    
    processor.get_cmd_dispatcher().remove_command_filter(exam_filter)


def example_5_argument_filters():
    """示例5：参数过滤器"""
    print("=" * 60)
    print("示例5：参数过滤器")
    print("=" * 60)
    
    processor = AlgebraProcessor()
    
    arg_count_filter = ArgumentCountFilter(min_args=2, max_args=3)
    processor.get_cmd_dispatcher().add_argument_filter(arg_count_filter)
    
    print("参数数量限制: 2-3个参数")
    
    test_cases = [
        "Sum(1)",
        "Sum(1, 2)",
        "Sum(1, 2, 3)",
        "Sum(1, 2, 3, 4)"
    ]
    
    for test_case in test_cases:
        print(f"测试: {test_case}")
        try:
            result = processor.process_algebra_command(test_case)
            print(f"  结果: {result}")
        except CommandError as e:
            print(f"  错误: {e}")
        print()
    
    processor.get_cmd_dispatcher().remove_argument_filter(arg_count_filter)


def example_6_expression_validation():
    """示例6：表达式验证"""
    print("=" * 60)
    print("示例6：表达式验证")
    print("=" * 60)
    
    processor = AlgebraProcessor()
    
    test_cases = [
        "Point(1, 2)",
        "Line((1, 2), (3, 4))",
        "UnknownCommand(1, 2)",
        "Point(1, 2, 3, 4)",
        "Sum(1, 2, 3)"
    ]
    
    for test_case in test_cases:
        print(f"验证: {test_case}")
        errors = processor.validate_expression(test_case)
        if errors:
            print(f"  错误: {errors}")
        else:
            print(f"  验证通过")
        print()


def example_7_command_categories():
    """示例7：命令分类"""
    print("=" * 60)
    print("示例7：命令分类")
    print("=" * 60)
    
    processor = AlgebraProcessor()
    
    categories = processor.get_command_categories()
    print(f"所有命令类别: {categories}")
    
    print("\n几何命令:")
    geometry_commands = processor.list_available_commands("GEOMETRY")
    for cmd in geometry_commands[:10]:
        print(f"  - {cmd}")
    
    print("\n统计命令:")
    statistics_commands = processor.list_available_commands("STATISTICS")
    for cmd in statistics_commands[:10]:
        print(f"  - {cmd}")
    
    print()


def example_8_complex_construction():
    """示例8：复杂构造"""
    print("=" * 60)
    print("示例8：复杂构造")
    print("=" * 60)
    
    processor = AlgebraProcessor()
    
    try:
        A = processor.process_algebra_command("A = Point(0, 0)")
        B = processor.process_algebra_command("B = Point(4, 0)")
        C = processor.process_algebra_command("C = Point(2, 3)")
        
        triangle = processor.process_algebra_command("Polygon(A, B, C)")
        print(f"三角形: {triangle}")
        
        centroid = processor.process_algebra_command("Centroid(A, B, C)")
        print(f"重心: {centroid}")
        
        area = processor.process_algebra_command("Area(A, B, C)")
        print(f"面积: {area}")
        
        elements = processor.get_all_elements()
        print(f"\n所有定义的元素: {list(elements.keys())}")
        
    except CommandError as e:
        print(f"命令错误: {e}")
    
    print()


def example_9_cas_filter():
    """示例9：CAS过滤器"""
    print("=" * 60)
    print("示例9：CAS过滤器")
    print("=" * 60)
    
    processor = AlgebraProcessor()
    
    cas_filter = CASFilter(cas_allowed=False)
    processor.get_cmd_dispatcher().add_command_filter(cas_filter)
    
    print("CAS命令被禁用")
    
    print(f"Sum命令可用: {processor.is_command_available('Sum')}")
    
    processor.get_cmd_dispatcher().remove_command_filter(cas_filter)
    print("\nCAS过滤器已移除")
    
    print(f"Sum命令可用: {processor.is_command_available('Sum')}")
    
    print()


def example_10_expression_evaluation():
    """示例10：表达式求值"""
    print("=" * 60)
    print("示例10：表达式求值")
    print("=" * 60)
    
    processor = AlgebraProcessor()
    
    processor.process_algebra_command("x = 5")
    processor.process_algebra_command("y = 10")
    
    expressions = [
        "Sum(x, y)",
        "Mean(x, y)",
        "Point(x, y)"
    ]
    
    for expr in expressions:
        try:
            result = processor.evaluate_expression(expr)
            print(f"{expr} -> {result}")
        except Exception as e:
            print(f"{expr} -> 错误: {e}")
    
    print()


def run_all_examples():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("GeoGebra DSL Python Implementation - 示例演示")
    print("=" * 60 + "\n")
    
    example_1_basic_commands()
    example_2_assignments()
    example_3_error_handling()
    example_4_command_filters()
    example_5_argument_filters()
    example_6_expression_validation()
    example_7_command_categories()
    example_8_complex_construction()
    example_9_cas_filter()
    example_10_expression_evaluation()
    
    print("=" * 60)
    print("所有示例运行完成")
    print("=" * 60)


if __name__ == "__main__":
    run_all_examples()