# GeoGebra DSL Python Implementation

这是一个基于GeoGebra DSL验证机制的Python实现，提供了完整的命令解析、验证和执行功能。

## 项目结构

```
python_dsl/
├── core/
│   ├── __init__.py          # 包初始化文件
│   ├── commands.py           # 命令定义和错误类型
│   ├── filters.py            # 命令过滤器接口和实现
│   ├── processor.py          # 命令处理器基类
│   ├── dispatcher.py         # 命令分发器
│   ├── parser.py             # 输入解析器
│   └── algebra.py           # 代数处理器
├── examples.py              # 示例和测试
└── README.md               # 本文件
```

## 核心组件

### 1. Commands (commands.py)

定义了所有支持的GeoGebra命令和错误类型。

**主要类：**
- `Commands`: 枚举类型，定义所有GeoGebra命令
- `CommandCategory`: 命令分类枚举
- `ErrorType`: 错误类型枚举
- `CommandError`: 命令错误基类
- `CommandNotFoundError`: 命令未找到错误
- `ArgumentError`: 参数错误
- `ArgumentNumberError`: 参数数量错误
- `CircularDefinitionError`: 循环定义错误
- `InvalidInputError`: 无效输入错误

**使用示例：**
```python
from core import Commands, CommandCategory

# 访问命令
point_cmd = Commands.POINT
print(point_cmd.name)  # "Point"
print(point_cmd.category)  # CommandCategory.GEOMETRY

# 检查命令是否可用
if Commands.POINT in [Commands.POINT, Commands.LINE]:
    print("命令可用")
```

### 2. Filters (filters.py)

提供命令和参数过滤功能。

**主要类：**
- `CommandFilter`: 命令过滤器接口
- `CommandArgumentFilter`: 参数过滤器接口
- `ExamModeFilter`: 考试模式过滤器
- `CASFilter`: CAS命令过滤器
- `ArgumentCountFilter`: 参数数量过滤器
- `ArgumentTypeFilter`: 参数类型过滤器
- `CompositeCommandFilter`: 组合命令过滤器
- `CompositeArgumentFilter`: 组合参数过滤器

**使用示例：**
```python
from core import ExamModeFilter, ArgumentCountFilter, Commands

# 创建考试模式过滤器
allowed_commands = [Commands.POINT, Commands.LINE]
exam_filter = ExamModeFilter(allowed_commands)

# 创建参数数量过滤器
arg_count_filter = ArgumentCountFilter(min_args=2, max_args=3)

# 添加到分发器
processor.get_cmd_dispatcher().add_command_filter(exam_filter)
processor.get_cmd_dispatcher().add_argument_filter(arg_count_filter)
```

### 3. Processor (processor.py)

命令处理器基类，提供参数解析和验证功能。

**主要类：**
- `CommandProcessor`: 命令处理器抽象基类
- `BasicCommandProcessor`: 基本命令处理器实现
- `EvalInfo`: 评估信息类

**使用示例：**
```python
from core import BasicCommandProcessor, EvalInfo

# 创建处理器
processor = BasicCommandProcessor()

# 执行命令
info = EvalInfo(label_output=True, allow_redefinition=True)
result = processor.process(Commands.POINT, [1, 2], info)
```

### 4. Dispatcher (dispatcher.py)

命令分发器，负责将命令路由到正确的处理器。

**主要类：**
- `CommandDispatcher`: 命令分发器
- `MacroProcessor`: 宏命令处理器
- `CommandProcessorFactory`: 命令处理器工厂

**使用示例：**
```python
from core import CommandDispatcher

# 创建分发器
dispatcher = CommandDispatcher()

# 处理命令
result = dispatcher.process_command("Point", [1, 2], EvalInfo())
```

### 5. Parser (parser.py)

输入解析器，将用户输入解析为可执行的表达式。

**主要类：**
- `ParserInterface`: 解析器接口
- `ParsedExpression`: 解析后的表达式
- `ParsedCommand`: 解析后的命令
- `ExpressionValidator`: 表达式验证器

**使用示例：**
```python
from core import ParserInterface

# 创建解析器
parser = ParserInterface()

# 解析表达式
expr = parser.parse_geogebra_expression("Point(1, 2)")
print(expr.type)  # "command"
print(expr.value)  # "Point"
```

### 6. AlgebraProcessor (algebra.py)

代数处理器，提供完整的DSL验证和执行功能。

**主要类：**
- `Kernel`: 内核类
- `Construction`: 构造类
- `ErrorHandler`: 错误处理器
- `AlgebraProcessor`: 代数处理器主类

**使用示例：**
```python
from core import AlgebraProcessor

# 创建处理器
processor = AlgebraProcessor()

# 执行命令
result = processor.process_algebra_command("Point(1, 2)")
print(result)

# 变量赋值
result = processor.process_algebra_command("A = Point(1, 2)")
print(result)

# 使用变量
result = processor.process_algebra_command("Line(A, Point(3, 4))")
print(result)
```

## 完整使用流程

### 基本使用

```python
from core import AlgebraProcessor

# 创建处理器
processor = AlgebraProcessor()

# 执行简单命令
result = processor.process_algebra_command("Point(1, 2)")
print(f"结果: {result}")

# 变量赋值
processor.process_algebra_command("A = Point(1, 2)")
processor.process_algebra_command("B = Point(3, 4)")

# 使用变量
result = processor.process_algebra_command("Line(A, B)")
print(f"直线: {result}")
```

### 使用过滤器

```python
from core import AlgebraProcessor, ExamModeFilter, Commands

# 创建处理器
processor = AlgebraProcessor()

# 添加考试模式过滤器
allowed_commands = [Commands.POINT, Commands.LINE, Commands.SEGMENT]
exam_filter = ExamModeFilter(allowed_commands)
processor.get_cmd_dispatcher().add_command_filter(exam_filter)

# 执行命令
result = processor.process_algebra_command("Point(1, 2)")
print(f"结果: {result}")

# 移除过滤器
processor.get_cmd_dispatcher().remove_command_filter(exam_filter)
```

### 错误处理

```python
from core import AlgebraProcessor, CommandError

# 创建处理器
processor = AlgebraProcessor()

# 执行命令并处理错误
try:
    result = processor.process_algebra_command("UnknownCommand(1, 2)")
    print(f"结果: {result}")
except CommandError as e:
    print(f"命令错误: {e}")
```

### 表达式验证

```python
from core import AlgebraProcessor

# 创建处理器
processor = AlgebraProcessor()

# 验证表达式
errors = processor.validate_expression("Point(1, 2)")
if errors:
    print(f"验证错误: {errors}")
else:
    print("验证通过")
```

## 支持的命令

### 几何命令
- `Point(x, y)` - 创建点
- `Line(point1, point2)` - 创建直线
- `Segment(point1, point2)` - 创建线段
- `Circle(center, radius)` - 创建圆
- `Intersect(obj1, obj2)` - 计算交点
- `Distance(obj1, obj2)` - 计算距离
- `Length(obj)` - 计算长度
- `Angle(point1, vertex, point2)` - 计算角度
- `Midpoint(point1, point2)` - 计算中点
- `Polygon(...)` - 创建多边形
- `Area(...)` - 计算面积
- `Centroid(...)` - 计算重心

### 代数命令
- `Sum(...)` - 求和
- `Mean(...)` - 计算平均值
- `Min(...)` - 求最小值
- `Max(...)` - 求最大值
- `Mod(a, b)` - 取模
- `GCD(...)` - 最大公约数
- `LCM(...)` - 最小公倍数

### 统计命令
- `Sum(...)` - 求和
- `Mean(...)` - 计算平均值
- `Variance(...)` - 计算方差
- `SD(...)` - 计算标准差
- `Median(...)` - 计算中位数
- `Mode(...)` - 计算众数

## 运行示例

```bash
# 运行所有示例
python examples.py
```

## 架构特点

1. **分层验证**：语法层、命令层、参数层、过滤层
2. **类型安全**：使用枚举和类型注解
3. **可扩展性**：通过接口和工厂模式支持扩展
4. **错误友好**：详细的错误信息和本地化支持
5. **灵活过滤**：支持命令和参数级别的过滤

## 与GeoGebra Java版本的对应关系

| Java类 | Python类 | 功能 |
|--------|-----------|------|
| `Commands` | `Commands` | 命令定义 |
| `CommandDispatcher` | `CommandDispatcher` | 命令分发 |
| `CommandProcessor` | `CommandProcessor` | 命令处理 |
| `AlgebraProcessor` | `AlgebraProcessor` | 代数处理 |
| `ParserInterface` | `ParserInterface` | 输入解析 |
| `CommandFilter` | `CommandFilter` | 命令过滤 |
| `CommandArgumentFilter` | `CommandArgumentFilter` | 参数过滤 |
| `MyError` | `CommandError` | 错误处理 |

## 许可证

本项目基于GeoGebra的EUPL 1.2许可证。

## 作者

GeoGebra DSL Python Implementation Team

## 贡献

欢迎提交问题和拉取请求！