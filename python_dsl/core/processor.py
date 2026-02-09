from abc import ABC, abstractmethod
from typing import List, Optional, TYPE_CHECKING, Any
import re

if TYPE_CHECKING:
    from .commands import Commands, CommandError


class EvalInfo:
    def __init__(self, label_output: bool = True, allow_redefinition: bool = False,
                 autocreate_sliders: bool = False, symbolic_mode: str = "NONE"):
        self.label_output = label_output
        self.allow_redefinition = allow_redefinition
        self.autocreate_sliders = autocreate_sliders
        self.symbolic_mode = symbolic_mode
    
    def with_labels(self, label_output: bool) -> 'EvalInfo':
        return EvalInfo(label_output, self.allow_redefinition, 
                     self.autocreate_sliders, self.symbolic_mode)
    
    def with_sliders(self, autocreate_sliders: bool) -> 'EvalInfo':
        return EvalInfo(self.label_output, self.allow_redefinition,
                     autocreate_sliders, self.symbolic_mode)


class CommandProcessor(ABC):
    def __init__(self, kernel=None):
        self.kernel = kernel
        self._construction = None
    
    @property
    def construction(self):
        if self._construction is None and self.kernel:
            self._construction = self.kernel.get_construction()
        return self._construction
    
    @abstractmethod
    def process(self, command: 'Commands', arguments: List[Any], 
               info: EvalInfo) -> List[Any]:
        pass
    
    def res_args(self, arguments: List[Any], info: EvalInfo) -> List[Any]:
        resolved_args = []
        for arg in arguments:
            resolved = self._resolve_arg(arg, info)
            resolved_args.append(resolved)
        return resolved_args
    
    def _resolve_arg(self, arg: Any, info: EvalInfo) -> Any:
        if isinstance(arg, str):
            return self._parse_string_arg(arg, info)
        elif isinstance(arg, (int, float)):
            return arg
        elif isinstance(arg, list):
            return [self._resolve_arg(a, info) for a in arg]
        else:
            return arg
    
    def _parse_string_arg(self, arg: str, info: EvalInfo) -> Any:
        if arg.startswith('(') and arg.endswith(')'):
            return self._parse_point(arg)
        elif arg.replace('.', '', 1).replace('-', '', 1).isdigit():
            return float(arg) if '.' in arg else int(arg)
        else:
            return arg
    
    def _parse_point(self, point_str: str) -> tuple:
        content = point_str[1:-1]
        coords = [c.strip() for c in content.split(',')]
        try:
            if len(coords) == 2:
                return (float(coords[0]), float(coords[1]))
            elif len(coords) == 3:
                return (float(coords[0]), float(coords[1]), float(coords[2]))
        except ValueError:
            pass
        return point_str
    
    def arg_err(self, command_name: str, arg_value: Any, 
                message: Optional[str] = None) -> 'CommandError':
        from .commands import ArgumentError
        return ArgumentError(command_name, str(arg_value), message)
    
    def arg_num_err(self, command_name: str, expected: int, actual: int) -> 'CommandError':
        from .commands import ArgumentNumberError
        return ArgumentNumberError(command_name, expected, actual)
    
    def validate_arg_count(self, command_name: str, arguments: List[Any],
                         min_count: int, max_count: Optional[int] = None) -> None:
        actual_count = len(arguments)
        if actual_count < min_count:
            raise self.arg_num_err(command_name, min_count, actual_count)
        
        if max_count is not None and actual_count > max_count:
            raise self.arg_num_err(command_name, max_count, actual_count)
    
    def validate_arg_types(self, command_name: str, arguments: List[Any],
                         expected_types: List[type]) -> None:
        from .commands import ArgumentError
        
        for i, (arg, expected_type) in enumerate(zip(arguments, expected_types)):
            if not isinstance(arg, expected_type):
                raise ArgumentError(command_name, str(arg),
                               f"Argument {i} expected {expected_type.__name__}, "
                               f"got {type(arg).__name__}")
    
    def check_dependency(self, args: List[Any], command_name: str, 
                      i: int, j: int) -> None:
        if i < len(args) and j < len(args):
            if args[i] == args[j]:
                from .commands import CircularDefinitionError
                raise CircularDefinitionError(
                    f"Circular dependency in {command_name}: argument {i} depends on {j}")
    
    def wrap_in_list(self, items: List[Any], item_type: type = None) -> List[Any]:
        if item_type is None:
            return items
        
        filtered = [item for item in items if isinstance(item, item_type)]
        return filtered

from .processor import CommandProcessor
class BasicCommandProcessor(CommandProcessor):
    def process(self, command: 'Commands', arguments: List[Any], 
               info: EvalInfo) -> List[Any]:
        self.validate_arg_count(command.name, arguments, 1, 10)
        resolved_args = self.res_args(arguments, info)
        return self._execute_command(command, resolved_args, info)
    
    def _execute_command(self, command: 'Commands', arguments: List[Any],
                       info: EvalInfo) -> List[Any]:
        from .commands import Commands
        
        if command == Commands.POINT:
            return self._process_point(arguments)
        elif command == Commands.LINE:
            return self._process_line(arguments)
        elif command == Commands.SEGMENT:
            return self._process_segment(arguments)
        elif command == Commands.CIRCLE:
            return self._process_circle(arguments)
        elif command == Commands.INTERSECT:
            return self._process_intersect(arguments)
        elif command == Commands.DISTANCE:
            return self._process_distance(arguments)
        elif command == Commands.LENGTH:
            return self._process_length(arguments)
        elif command == Commands.ANGLE:
            return self._process_angle(arguments)
        elif command == Commands.MIDPOINT:
            return self._process_midpoint(arguments)
        elif command == Commands.SUM:
            return self._process_sum(arguments)
        elif command == Commands.MEAN:
            return self._process_mean(arguments)
        else:
            raise NotImplementedError(f"Command {command.name} not implemented")
    
    def _process_point(self, args: List[Any]) -> List[Any]:
        if len(args) == 2 and all(isinstance(a, (int, float)) for a in args):
            return [{'type': 'Point', 'x': args[0], 'y': args[1]}]
        elif len(args) == 1 and isinstance(args[0], tuple):
            x, y = args[0]
            return [{'type': 'Point', 'x': x, 'y': y}]
        else:
            raise self.arg_err("Point", args)
    
    def _process_line(self, args: List[Any]) -> List[Any]:
        if len(args) == 2:
            return [{'type': 'Line', 'point1': args[0], 'point2': args[1]}]
        else:
            raise self.arg_err("Line", args)
    
    def _process_segment(self, args: List[Any]) -> List[Any]:
        if len(args) == 2:
            return [{'type': 'Segment', 'point1': args[0], 'point2': args[1]}]
        else:
            raise self.arg_err("Segment", args)
    
    def _process_circle(self, args: List[Any]) -> List[Any]:
        if len(args) == 2:
            return [{'type': 'Circle', 'center': args[0], 'radius': args[1]}]
        else:
            raise self.arg_err("Circle", args)
    
    def _process_intersect(self, args: List[Any]) -> List[Any]:
        if len(args) == 2:
            return [{'type': 'Intersection', 'obj1': args[0], 'obj2': args[1]}]
        else:
            raise self.arg_err("Intersect", args)
    
    def _process_distance(self, args: List[Any]) -> List[Any]:
        if len(args) == 2:
            return [{'type': 'Distance', 'obj1': args[0], 'obj2': args[1]}]
        else:
            raise self.arg_err("Distance", args)
    
    def _process_length(self, args: List[Any]) -> List[Any]:
        if len(args) == 1:
            return [{'type': 'Length', 'obj': args[0]}]
        else:
            raise self.arg_err("Length", args)
    
    def _process_angle(self, args: List[Any]) -> List[Any]:
        if len(args) == 3:
            return [{'type': 'Angle', 'point1': args[0], 'vertex': args[1], 'point2': args[2]}]
        else:
            raise self.arg_err("Angle", args)
    
    def _process_midpoint(self, args: List[Any]) -> List[Any]:
        if len(args) == 2:
            return [{'type': 'Midpoint', 'point1': args[0], 'point2': args[1]}]
        else:
            raise self.arg_err("Midpoint", args)
    
    def _process_sum(self, args: List[Any]) -> List[Any]:
        if all(isinstance(a, (int, float)) for a in args):
            return [{'type': 'Number', 'value': sum(args)}]
        else:
            raise self.arg_err("Sum", args)
    
    def _process_mean(self, args: List[Any]) -> List[Any]:
        if all(isinstance(a, (int, float)) for a in args):
            return [{'type': 'Number', 'value': sum(args) / len(args)}]
        else:
            raise self.arg_err("Mean", args)