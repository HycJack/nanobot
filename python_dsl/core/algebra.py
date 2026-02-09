from typing import List, Optional, Dict, Any, TYPE_CHECKING, Callable
import re
from .commands import Commands, CommandError
from .dispatcher import CommandDispatcher
from .parser import ParserInterface, ParsedExpression
from .processor import EvalInfo


class Kernel:
    def __init__(self):
        self._construction = Construction()
        self._parser = None
        self._dispatcher = None
    
    def get_construction(self):
        return self._construction
    
    def get_parser(self):
        if self._parser is None:
            self._parser = ParserInterface(self)
        return self._parser
    
    def get_dispatcher(self):
        if self._dispatcher is None:
            self._dispatcher = CommandDispatcher(self)
        return self._dispatcher
    
    def lookup_label(self, label: str) -> Optional[Any]:
        return self._construction.get_element(label)
    
    def add_element(self, label: str, element: Any) -> None:
        self._construction.add_element(label, element)


class Construction:
    def __init__(self):
        self._elements: Dict[str, Any] = {}
        self._suppress_labels = False
    
    def get_element(self, label: str) -> Optional[Any]:
        return self._elements.get(label)
    
    def add_element(self, label: str, element: Any) -> None:
        self._elements[label] = element
    
    def is_suppress_labels_active(self) -> bool:
        return self._suppress_labels
    
    def set_suppress_label_creation(self, suppress: bool) -> None:
        self._suppress_labels = suppress
    
    def is_free_label(self, label: str) -> bool:
        return label not in self._elements


class ErrorHandler:
    def __init__(self, silent: bool = False):
        self.silent = silent
        self.errors: List[str] = []
    
    def handle_error(self, error: Exception, context: str = "") -> None:
        error_msg = str(error)
        if context:
            error_msg = f"{context}: {error_msg}"
        
        self.errors.append(error_msg)
        
        if not self.silent:
            print(f"Error: {error_msg}")
    
    def show_error(self, error: Exception) -> None:
        self.handle_error(error)
    
    def on_undefined_variables(self, variables: str, 
                             callback: Callable) -> bool:
        if not self.silent:
            print(f"Undefined variables: {variables}")
            return True
        return False
    
    def get_errors(self) -> List[str]:
        return self.errors.copy()
    
    def clear_errors(self) -> None:
        self.errors.clear()


class AlgebraProcessor:
    def __init__(self, kernel: Kernel = None):
        self.kernel = kernel or Kernel()
        self.parser = self.kernel.get_parser()
        self.dispatcher = self.kernel.get_dispatcher()
        self.error_handler = ErrorHandler()
        self._input_filters: List[Callable] = []
        self._output_filters: List[Callable] = []
    
    def add_input_filter(self, filter: Callable) -> None:
        self._input_filters.append(filter)
    
    def remove_input_filter(self, filter: Callable) -> None:
        if filter in self._input_filters:
            self._input_filters.remove(filter)
    
    def add_output_filter(self, filter: Callable) -> None:
        self._output_filters.append(filter)
    
    def remove_output_filter(self, filter: Callable) -> None:
        if filter in self._output_filters:
            self._output_filters.remove(filter)
    
    def is_expression_allowed(self, expression: ParsedExpression, 
                            filters: List[Callable]) -> bool:
        for filter_func in filters:
            if not filter_func(expression):
                return False
        return True
    
    def process_algebra_command(self, cmd: str, store_undo: bool = False) -> List[Any]:
        try:
            return self.process_algebra_command_no_exception_handling(
                cmd, store_undo, self.error_handler, False, None
            )
        except Exception as e:
            self.error_handler.handle_error(e, cmd)
            return None
    
    def process_algebra_command_no_exception_handling(
        self, cmd: str, store_undo: bool, error_handler: ErrorHandler,
        autocreate_sliders: bool, callback: Optional[Callable]
    ) -> List[Any]:
        if not cmd.strip():
            from .commands import InvalidInputError
            raise InvalidInputError("Empty command")
        
        parsed_expr = self.parser.parse_geogebra_expression(cmd)
        
        if not self.is_expression_allowed(parsed_expr, self._input_filters):
            from .commands import InvalidInputError
            raise InvalidInputError("Expression not allowed by input filters")
        
        info = EvalInfo(
            label_output=True,
            allow_redefinition=True,
            autocreate_sliders=autocreate_sliders
        )
        
        result = self.process_valid_expression(parsed_expr, info)
        
        if result and not self.is_expression_allowed(
            ParsedExpression(type='result', value=result),
            self._output_filters
        ):
            from .commands import InvalidInputError
            raise InvalidInputError("Result not allowed by output filters")
        
        if callback:
            callback(result)
        
        return result
    
    def process_valid_expression(self, expr: ParsedExpression, 
                               info: EvalInfo) -> List[Any]:
        if expr.type == 'command':
            return self._process_command(expr, info)
        elif expr.type == 'assignment':
            return self._process_assignment(expr, info)
        else:
            return self._process_simple_expression(expr, info)
    
    def _process_command(self, expr: ParsedExpression, 
                        info: EvalInfo) -> List[Any]:
        command_name = expr.value
        arguments = [child.value for child in expr.children]
        
        try:
            result = self.dispatcher.process_command(command_name, arguments, info)
            
            if expr.label:
                self.kernel.add_element(expr.label, result)
            
            return result
        except Exception as e:
            from .commands import CommandError
            if isinstance(e, CommandError):
                raise
            from .commands import InvalidInputError
            raise InvalidInputError(f"Error executing command {command_name}: {e}")
    
    def _process_assignment(self, expr: ParsedExpression, 
                           info: EvalInfo) -> List[Any]:
        label = expr.label
        value_expr = expr.value
        
        if self.kernel.lookup_label(label):
            if not info.allow_redefinition:
                from .commands import CommandError, ErrorType
                raise CommandError(
                    error_type=ErrorType.NAME_USED,
                    command_name=label,
                    message=f"Label '{label}' already in use"
                )
        
        result = self.process_valid_expression(value_expr, info)
        self.kernel.add_element(label, result)
        
        return result
    
    def _process_simple_expression(self, expr: ParsedExpression,
                                 info: EvalInfo) -> List[Any]:
        if expr.type == 'number':
            return [{'type': 'Number', 'value': expr.value}]
        elif expr.type == 'point':
            return [{'type': 'Point', 'x': expr.value[0], 'y': expr.value[1]}]
        elif expr.type == 'list':
            return [{'type': 'List', 'items': expr.value}]
        elif expr.type == 'variable':
            return [expr.value]
        else:
            from .commands import InvalidInputError
            raise InvalidInputError(f"Unsupported expression type: {expr.type}")
    
    def process_command(self, command_name: str, arguments: List[Any],
                     info: EvalInfo) -> List[Any]:
        return self.dispatcher.process_command(command_name, arguments, info)
    
    def simplify_command(self, command_name: str, arguments: List[Any],
                      info: EvalInfo) -> Any:
        return self.dispatcher.simplify_command(command_name, arguments, info)
    
    def is_command_available(self, cmd: str) -> bool:
        return self.dispatcher.is_command_available(cmd)
    
    def get_sub_command_set_name(self, index: int) -> str:
        from .commands import CommandCategory
        category_names = {
            0: "Geometry",
            1: "Algebra",
            2: "Statistics",
            3: "Probability",
            4: "Functions and Calculus",
            5: "Conic",
            6: "List",
            7: "Vector and Matrix",
            8: "Transformation",
            9: "Charts",
            10: "Text",
            11: "Logical",
            12: "Scripting",
            13: "Discrete Math",
            14: "GeoGebra",
            15: "Optimization",
            16: "CAS",
            17: "3D",
            18: "Financial",
            19: "English"
        }
        return category_names.get(index, "Unknown")
    
    def change_geo_element(self, geo: Any, new_value: str,
                         redefine_independent: bool, store_undo: bool,
                         error_handler: ErrorHandler, callback: Optional[Callable]) -> None:
        info = EvalInfo(
            label_output=True,
            allow_redefinition=redefine_independent,
            autocreate_sliders=True
        )
        
        try:
            parsed_expr = self.parser.parse_geogebra_expression(new_value)
            result = self.process_valid_expression(parsed_expr, info)
            
            if callback:
                callback(result)
        except Exception as e:
            error_handler.handle_error(e, new_value)
            if callback:
                callback(None)
    
    def get_construction(self):
        return self.kernel.get_construction()
    
    def get_cmd_dispatcher(self):
        return self.dispatcher
    
    def get_error_handler(self) -> ErrorHandler:
        return self.error_handler
    
    def set_error_handler(self, handler: ErrorHandler) -> None:
        self.error_handler = handler
    
    def get_all_elements(self) -> Dict[str, Any]:
        return self.kernel.get_construction()._elements.copy()
    
    def clear_construction(self) -> None:
        self.kernel.get_construction()._elements.clear()
        self.parser.clear_variables()
    
    def get_element(self, label: str) -> Optional[Any]:
        return self.kernel.lookup_label(label)
    
    def add_element(self, label: str, element: Any) -> None:
        self.kernel.add_element(label, element)
    
    def remove_element(self, label: str) -> bool:
        construction = self.kernel.get_construction()
        if label in construction._elements:
            del construction._elements[label]
            return True
        return False
    
    def evaluate_expression(self, expr_str: str) -> Any:
        parsed = self.parser.parse_geogebra_expression(expr_str)
        info = EvalInfo(label_output=False, allow_redefinition=True)
        result = self.process_valid_expression(parsed, info)
        return result
    
    def validate_expression(self, expr_str: str) -> List[str]:
        try:
            parsed = self.parser.parse_geogebra_expression(expr_str)
            from .parser import ExpressionValidator
            validator = ExpressionValidator(self.parser)
            return validator.validate(parsed)
        except Exception as e:
            return [str(e)]
    
    def get_command_syntax(self, command_name: str) -> Optional[str]:
        from .commands import Commands
        try:
            cmd = Commands[command_name]
            return f"{cmd.name}(...)"
        except KeyError:
            return None
    
    def list_available_commands(self, category: Optional[str] = None) -> List[str]:
        from .commands import Commands
        if category:
            return [cmd.name for cmd in Commands if cmd.category.name == category]
        return [cmd.name for cmd in Commands]
    
    def get_command_categories(self) -> List[str]:
        from .commands import CommandCategory
        return [cat.name for cat in CommandCategory]