from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .commands import Commands


class CommandFilter(ABC):
    @abstractmethod
    def is_command_allowed(self, command: 'Commands') -> bool:
        pass


class CommandArgumentFilter(ABC):
    @abstractmethod
    def check_allowed(self, command_name: str, arguments: list) -> None:
        pass


class ExamModeFilter(CommandFilter):
    def __init__(self, allowed_commands: list):
        self.allowed_commands = allowed_commands
    
    def is_command_allowed(self, command: 'Commands') -> bool:
        return command in self.allowed_commands


class CASFilter(CommandFilter):
    def __init__(self, cas_allowed: bool = False):
        self.cas_allowed = cas_allowed
    
    def is_command_allowed(self, command: 'Commands') -> bool:
        if not self.cas_allowed:
            return command.category.name != "CAS"
        return True


class ArgumentCountFilter(CommandArgumentFilter):
    def __init__(self, min_args: int = 0, max_args: int = None):
        self.min_args = min_args
        self.max_args = max_args
    
    def check_allowed(self, command_name: str, arguments: list) -> None:
        arg_count = len(arguments)
        if arg_count < self.min_args:
            from .commands import ArgumentNumberError
            raise ArgumentNumberError(command_name, self.min_args, arg_count)
        
        if self.max_args is not None and arg_count > self.max_args:
            from .commands import ArgumentNumberError
            raise ArgumentNumberError(command_name, self.max_args, arg_count)


class ArgumentTypeFilter(CommandArgumentFilter):
    def __init__(self, expected_types: list):
        self.expected_types = expected_types
    
    def check_allowed(self, command_name: str, arguments: list) -> None:
        from .commands import ArgumentError
        
        for i, (arg, expected_type) in enumerate(zip(arguments, self.expected_types)):
            if not isinstance(arg, expected_type):
                raise ArgumentError(command_name, str(type(arg)), 
                               f"Argument {i} expected {expected_type.__name__}, got {type(arg).__name__}")


class CompositeCommandFilter(CommandFilter):
    def __init__(self, filters: list):
        self.filters = filters
    
    def is_command_allowed(self, command: 'Commands') -> bool:
        return all(f.is_command_allowed(command) for f in self.filters)


class CompositeArgumentFilter(CommandArgumentFilter):
    def __init__(self, filters: list):
        self.filters = filters
    
    def check_allowed(self, command_name: str, arguments: list) -> None:
        for f in self.filters:
            f.check_allowed(command_name, arguments)