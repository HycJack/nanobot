import re
from typing import List, Optional, Dict, Tuple, Any, TYPE_CHECKING
from dataclasses import dataclass
from .commands import Commands, CommandError


@dataclass
class ParsedExpression:
    type: str
    value: Any = None
    label: Optional[str] = None
    children: List['ParsedExpression'] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []


@dataclass
class ParsedCommand:
    name: str
    arguments: List[Any]
    label: Optional[str] = None
    
    def __str__(self) -> str:
        args_str = ', '.join(str(arg) for arg in self.arguments)
        if self.label:
            return f"{self.label} = {self.name}({args_str})"
        return f"{self.name}({args_str})"


class ParserInterface:
    def __init__(self, kernel=None):
        self.kernel = kernel
        self._variable_map: Dict[str, Any] = {}
    
    def parse_geogebra_expression(self, input_str: str) -> ParsedExpression:
        input_str = input_str.strip()
        
        if not input_str:
            from .commands import InvalidInputError
            raise InvalidInputError("Empty input")
        
        if '=' in input_str:
            return self._parse_assignment(input_str)
        elif self._is_command(input_str):
            return self._parse_command(input_str)
        else:
            return self._parse_simple_expression(input_str)
    
    def _is_command(self, input_str: str) -> bool:
        command_pattern = r'^([A-Za-z_][A-Za-z0-9_]*)\s*\('
        return bool(re.match(command_pattern, input_str))
    
    def _parse_assignment(self, input_str: str) -> ParsedExpression:
        parts = input_str.split('=', 1)
        if len(parts) != 2:
            from .commands import InvalidInputError
            raise InvalidInputError(f"Invalid assignment: {input_str}")
        
        label = parts[0].strip()
        expression = parts[1].strip()
        
        parsed_expr = self.parse_geogebra_expression(expression)
        parsed_expr.label = label
        
        return parsed_expr
    
    def _parse_command(self, input_str: str) -> ParsedExpression:
        command_pattern = r'^([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*(.*?)\s*\)\s*$'
        match = re.match(command_pattern, input_str)
        
        if not match:
            from .commands import InvalidInputError
            raise InvalidInputError(f"Invalid command syntax: {input_str}")
        
        command_name = match.group(1)
        args_str = match.group(2)
        
        arguments = self._parse_arguments(args_str)
        
        return ParsedExpression(
            type='command',
            value=command_name,
            children=[ParsedExpression(type='argument', value=arg) for arg in arguments]
        )
    
    def _parse_arguments(self, args_str: str) -> List[Any]:
        if not args_str.strip():
            return []
        
        arguments = []
        current_arg = []
        paren_level = 0
        bracket_level = 0
        in_string = False
        string_char = None
        
        i = 0
        while i < len(args_str):
            char = args_str[i]
            
            if in_string:
                current_arg.append(char)
                if char == string_char:
                    in_string = False
                    string_char = None
            elif char in ['"', "'"]:
                in_string = True
                string_char = char
                current_arg.append(char)
            elif char == '(':
                paren_level += 1
                current_arg.append(char)
            elif char == ')':
                paren_level -= 1
                current_arg.append(char)
            elif char == '[':
                bracket_level += 1
                current_arg.append(char)
            elif char == ']':
                bracket_level -= 1
                current_arg.append(char)
            elif char == ',' and paren_level == 0 and bracket_level == 0:
                arg_str = ''.join(current_arg).strip()
                if arg_str:
                    arguments.append(self._parse_single_argument(arg_str))
                current_arg = []
            else:
                current_arg.append(char)
            
            i += 1
        
        if current_arg:
            arg_str = ''.join(current_arg).strip()
            if arg_str:
                arguments.append(self._parse_single_argument(arg_str))
        
        return arguments
    
    def _parse_single_argument(self, arg_str: str) -> Any:
        arg_str = arg_str.strip()
        
        if not arg_str:
            return None
        
        if self._is_number(arg_str):
            return float(arg_str) if '.' in arg_str else int(arg_str)
        
        if self._is_point(arg_str):
            return self._parse_point(arg_str)
        
        if self._is_list(arg_str):
            return self._parse_list(arg_str)
        
        if self._is_command(arg_str):
            return self._parse_command(arg_str)
        
        if arg_str in self._variable_map:
            return self._variable_map[arg_str]
        
        return arg_str
    
    def _is_number(self, s: str) -> bool:
        try:
            float(s)
            return True
        except ValueError:
            return False
    
    def _is_point(self, s: str) -> bool:
        return s.startswith('(') and s.endswith(')')
    
    def _parse_point(self, point_str: str) -> Tuple[float, ...]:
        content = point_str[1:-1].strip()
        coords = [c.strip() for c in content.split(',')]
        
        try:
            if len(coords) == 2:
                return (float(coords[0]), float(coords[1]))
            elif len(coords) == 3:
                return (float(coords[0]), float(coords[1]), float(coords[2]))
        except ValueError:
            pass
        
        return point_str
    
    def _is_list(self, s: str) -> bool:
        return s.startswith('[') and s.endswith(']')
    
    def _parse_list(self, list_str: str) -> List[Any]:
        content = list_str[1:-1].strip()
        if not content:
            return []
        
        items = []
        current_item = []
        paren_level = 0
        bracket_level = 0
        
        i = 0
        while i < len(content):
            char = content[i]
            
            if char == '(':
                paren_level += 1
                current_item.append(char)
            elif char == ')':
                paren_level -= 1
                current_item.append(char)
            elif char == '[':
                bracket_level += 1
                current_item.append(char)
            elif char == ']':
                bracket_level -= 1
                current_item.append(char)
            elif char == ',' and paren_level == 0 and bracket_level == 0:
                item_str = ''.join(current_item).strip()
                if item_str:
                    items.append(self._parse_single_argument(item_str))
                current_item = []
            else:
                current_item.append(char)
            
            i += 1
        
        if current_item:
            item_str = ''.join(current_item).strip()
            if item_str:
                items.append(self._parse_single_argument(item_str))
        
        return items
    
    def _parse_simple_expression(self, input_str: str) -> ParsedExpression:
        if self._is_number(input_str):
            return ParsedExpression(
                type='number',
                value=float(input_str) if '.' in input_str else int(input_str)
            )
        
        if self._is_point(input_str):
            return ParsedExpression(
                type='point',
                value=self._parse_point(input_str)
            )
        
        if self._is_list(input_str):
            return ParsedExpression(
                type='list',
                value=self._parse_list(input_str)
            )
        
        if input_str in self._variable_map:
            return ParsedExpression(
                type='variable',
                value=self._variable_map[input_str],
                label=input_str
            )
        
        return ParsedExpression(
            type='identifier',
            value=input_str
        )
    
    def set_variable(self, name: str, value: Any) -> None:
        self._variable_map[name] = value
    
    def get_variable(self, name: str) -> Optional[Any]:
        return self._variable_map.get(name)
    
    def clear_variables(self) -> None:
        self._variable_map.clear()


class ExpressionValidator:
    def __init__(self, parser: ParserInterface):
        self.parser = parser
    
    def validate(self, expression: ParsedExpression) -> List[str]:
        errors = []
        
        if expression.type == 'command':
            errors.extend(self._validate_command(expression))
        elif expression.type == 'identifier':
            errors.extend(self._validate_identifier(expression))
        
        for child in expression.children:
            errors.extend(self.validate(child))
        
        return errors
    
    def _validate_command(self, expr: ParsedExpression) -> List[str]:
        errors = []
        command_name = expr.value
        
        from .commands import Commands
        try:
            Commands[command_name]
        except KeyError:
            errors.append(f"Unknown command: {command_name}")
        
        return errors
    
    def _validate_identifier(self, expr: ParsedExpression) -> List[str]:
        errors = []
        
        if expr.value not in self.parser._variable_map:
            errors.append(f"Undefined variable: {expr.value}")
        
        return errors