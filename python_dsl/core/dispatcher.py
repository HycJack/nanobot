from typing import Dict, List, Optional, TYPE_CHECKING, Any
from .commands import Commands, CommandError
from .filters import CommandFilter, CommandArgumentFilter
from .processor import CommandProcessor, EvalInfo


class CommandDispatcher:
    def __init__(self, kernel=None):
        self.kernel = kernel
        self._command_table: Dict[str, CommandProcessor] = {}
        self._command_filters: List[CommandFilter] = []
        self._argument_filters: List[CommandArgumentFilter] = []
        self._init_command_table()
    
    def _init_command_table(self):
        from .commands import Commands
        from .processor import BasicCommandProcessor
        
        basic_processor = BasicCommandProcessor(self.kernel)
        
        for cmd in Commands:
            if cmd.category.name in ["GEOMETRY", "STATISTICS", "ALGEBRA"]:
                self._command_table[cmd.cmdName] = basic_processor
    
    def add_command_filter(self, filter: 'CommandFilter') -> None:
        self._command_filters.append(filter)
    
    def remove_command_filter(self, filter: 'CommandFilter') -> None:
        if filter in self._command_filters:
            self._command_filters.remove(filter)
    
    def add_argument_filter(self, filter: 'CommandArgumentFilter') -> None:
        self._argument_filters.append(filter)
    
    def remove_argument_filter(self, filter: 'CommandArgumentFilter') -> None:
        if filter in self._argument_filters:
            self._argument_filters.remove(filter)
    
    def is_command_available(self, command_name: str) -> bool:
        return command_name in self._command_table
    
    def is_allowed_by_command_filters(self, command: 'Commands') -> bool:
        for filter in self._command_filters:
            if not filter.is_command_allowed(command):
                return False
        return True
    
    def check_allowed_by_argument_filters(self, command_name: str, 
                                       arguments: List[Any]) -> None:
        for filter in self._argument_filters:
            filter.check_allowed(command_name, arguments)
    
    def get_processor(self, command_name: str) -> Optional['CommandProcessor']:
        return self._command_table.get(command_name)
    
    def process_command(self, command_name: str, arguments: List[Any],
                     info: 'EvalInfo') -> List[Any]:
        from .commands import CommandNotFoundError
        
        command = Commands.get_by_name(command_name)
        if command is None:
            raise CommandNotFoundError(command_name)
        
        if not self.is_allowed_by_command_filters(command):
            from .commands import CommandError, ErrorType
            raise CommandError(
                error_type=ErrorType.ILLEGAL_ARGUMENT,
                command_name=command_name,
                message=f"Command '{command_name}' is not allowed"
            )
        
        processor = self.get_processor(command_name)
        if processor is None:
            raise CommandNotFoundError(command_name)
        
        self.check_allowed_by_argument_filters(command_name, arguments)
        
        return processor.process(command, arguments, info)
    
    def simplify_command(self, command_name: str, arguments: List[Any],
                        info: 'EvalInfo') -> Any:
        return self.process_command(command_name, arguments, info)
    
    def get_sub_command_set_name(self, category_name: str) -> str:
        category_names = {
            "GEOMETRY": "Geometry",
            "ALGEBRA": "Algebra",
            "STATISTICS": "Statistics",
            "PROBABILITY": "Probability",
            "FUNCTION": "Functions and Calculus",
            "CONIC": "Conic",
            "LIST": "List",
            "VECTOR": "Vector and Matrix",
            "TRANSFORMATION": "Transformation",
            "CHARTS": "Charts",
            "TEXT": "Text",
            "LOGICAL": "Logical",
            "SCRIPTING": "Scripting",
            "DISCRETE": "Discrete Math",
            "GEOGEBRA": "GeoGebra",
            "OPTIMIZATION": "Optimization",
            "CAS": "CAS",
            "THREE_D": "3D",
            "FINANCIAL": "Financial",
            "ENGLISH": "English"
        }
        return category_names.get(category_name, "Unknown")


class MacroProcessor(CommandProcessor):
    def __init__(self, kernel=None, macros: Dict[str, Any] = None):
        super().__init__(kernel)
        self.macros = macros or {}
    
    def add_macro(self, name: str, definition: Any) -> None:
        self.macros[name] = definition
    
    def remove_macro(self, name: str) -> None:
        if name in self.macros:
            del self.macros[name]
    
    def has_macro(self, name: str) -> bool:
        return name in self.macros
    
    def get_macro(self, name: str) -> Optional[Any]:
        return self.macros.get(name)
    
    def process(self, command: 'Commands', arguments: List[Any],
               info: 'EvalInfo') -> List[Any]:
        macro_name = command.name
        if not self.has_macro(macro_name):
            from .commands import CommandNotFoundError
            raise CommandNotFoundError(macro_name)
        
        macro_def = self.get_macro(macro_name)
        return self._execute_macro(macro_def, arguments, info)
    
    def _execute_macro(self, macro_def: Any, arguments: List[Any],
                      info: 'EvalInfo') -> List[Any]:
        if callable(macro_def):
            return macro_def(arguments, info)
        elif isinstance(macro_def, list):
            return macro_def
        else:
            return [macro_def]


class CommandProcessorFactory:
    def __init__(self, kernel=None):
        self.kernel = kernel
        self._processors: Dict[str, CommandProcessor] = {}
    
    def get_processor(self, command: 'Commands', 
                    kernel=None) -> 'CommandProcessor':
        processor = self._processors.get(command.name)
        if processor is None:
            processor = self._create_processor(command, kernel)
            self._processors[command.name] = processor
        return processor
    
    def _create_processor(self, command: 'Commands', 
                        kernel=None) -> 'CommandProcessor':
        from .processor import BasicCommandProcessor
        return BasicCommandProcessor(kernel or self.kernel)
    
    def register_processor(self, command_name: str, 
                         processor: 'CommandProcessor') -> None:
        self._processors[command_name] = processor