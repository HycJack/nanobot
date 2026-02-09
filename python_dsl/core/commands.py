from enum import Enum
from typing import Dict, List, Optional, Callable


class CommandCategory(Enum):
    ALGEBRA = "Algebra"
    GEOMETRY = "Geometry"
    STATISTICS = "Statistics"
    PROBABILITY = "Probability"
    FUNCTION = "Function"
    CONIC = "Conic"
    LIST = "List"
    VECTOR = "Vector"
    TRANSFORMATION = "Transformation"
    CHARTS = "Charts"
    TEXT = "Text"
    LOGICAL = "Logical"
    SCRIPTING = "Scripting"
    DISCRETE = "Discrete"
    GEOGEBRA = "GeoGebra"
    OPTIMIZATION = "Optimization"
    CAS = "CAS"
    THREE_D = "3D"
    FINANCIAL = "Financial"
    ENGLISH = "English"


class Commands(Enum):
    MOD = (CommandCategory.ALGEBRA, "Mod")
    DIV = (CommandCategory.ALGEBRA, "Div")
    MIN = (CommandCategory.ALGEBRA, "Min")
    MAX = (CommandCategory.ALGEBRA, "Max")
    LCM = (CommandCategory.ALGEBRA, "LCM")
    GCD = (CommandCategory.ALGEBRA, "GCD")
    EXPAND = (CommandCategory.ALGEBRA, "Expand")
    FACTOR = (CommandCategory.ALGEBRA, "Factor")
    SIMPLIFY = (CommandCategory.ALGEBRA, "Simplify")
    
    LINE = (CommandCategory.GEOMETRY, "Line")
    RAY = (CommandCategory.GEOMETRY, "Ray")
    ANGULAR_BISECTOR = (CommandCategory.GEOMETRY, "AngularBisector")
    ORTHOGONAL_LINE = (CommandCategory.GEOMETRY, "OrthogonalLine")
    TANGENT = (CommandCategory.GEOMETRY, "Tangent")
    SEGMENT = (CommandCategory.GEOMETRY, "Segment")
    SLOPE = (CommandCategory.GEOMETRY, "Slope")
    ANGLE = (CommandCategory.GEOMETRY, "Angle")
    POINT = (CommandCategory.GEOMETRY, "Point")
    MIDPOINT = (CommandCategory.GEOMETRY, "Midpoint")
    LINE_BISECTOR = (CommandCategory.GEOMETRY, "LineBisector")
    INTERSECT = (CommandCategory.GEOMETRY, "Intersect")
    DISTANCE = (CommandCategory.GEOMETRY, "Distance")
    LENGTH = (CommandCategory.GEOMETRY, "Length")
    RADIUS = (CommandCategory.GEOMETRY, "Radius")
    CIRCLE_ARC = (CommandCategory.GEOMETRY, "CircleArc")
    ARC = (CommandCategory.GEOMETRY, "Arc")
    SECTOR = (CommandCategory.GEOMETRY, "Sector")
    POLYGON = (CommandCategory.GEOMETRY, "Polygon")
    AREA = (CommandCategory.GEOMETRY, "Area")
    CIRCUMFERENCE = (CommandCategory.GEOMETRY, "Circumference")
    PERIMETER = (CommandCategory.GEOMETRY, "Perimeter")
    LOCUS = (CommandCategory.GEOMETRY, "Locus")
    CENTROID = (CommandCategory.GEOMETRY, "Centroid")
    
    SUM = (CommandCategory.STATISTICS, "Sum")
    MEAN = (CommandCategory.STATISTICS, "Mean")
    VARIANCE = (CommandCategory.STATISTICS, "Variance")
    SD = (CommandCategory.STATISTICS, "SD")
    MEDIAN = (CommandCategory.STATISTICS, "Median")
    MODE = (CommandCategory.STATISTICS, "Mode")
    
    RANDOM = (CommandCategory.PROBABILITY, "Random")
    RANDOM_NORMAL = (CommandCategory.PROBABILITY, "RandomNormal")
    NORMAL = (CommandCategory.PROBABILITY, "Normal")
    BINOMIAL = (CommandCategory.PROBABILITY, "Binomial")
    
    ROOT = (CommandCategory.FUNCTION, "Root")
    ROOTS = (CommandCategory.FUNCTION, "Roots")
    POLYNOMIAL = (CommandCategory.FUNCTION, "Polynomial")
    FUNCTION = (CommandCategory.FUNCTION, "Function")
    EXTREMUM = (CommandCategory.FUNCTION, "Extremum")
    DERIVATIVE = (CommandCategory.FUNCTION, "Derivative")
    INTEGRAL = (CommandCategory.FUNCTION, "Integral")
    LIMIT = (CommandCategory.FUNCTION, "Limit")
    
    ELLIPSE = (CommandCategory.CONIC, "Ellipse")
    HYPERBOLA = (CommandCategory.CONIC, "Hyperbola")
    CONIC = (CommandCategory.CONIC, "Conic")
    CIRCLE = (CommandCategory.CONIC, "Circle")
    PARABOLA = (CommandCategory.CONIC, "Parabola")
    FOCUS = (CommandCategory.CONIC, "Focus")
    CENTER = (CommandCategory.CONIC, "Center")
    
    SORT = (CommandCategory.LIST, "Sort")
    FIRST = (CommandCategory.LIST, "First")
    LAST = (CommandCategory.LIST, "Last")
    TAKE = (CommandCategory.LIST, "Take")
    ELEMENT = (CommandCategory.LIST, "Element")
    APPEND = (CommandCategory.LIST, "Append")
    JOIN = (CommandCategory.LIST, "Join")
    SEQUENCE = (CommandCategory.LIST, "Sequence")
    
    VECTOR = (CommandCategory.VECTOR, "Vector")
    UNIT_VECTOR = (CommandCategory.VECTOR, "UnitVector")
    INVERT = (CommandCategory.VECTOR, "Invert")
    TRANSPOSE = (CommandCategory.VECTOR, "Transpose")
    DETERMINANT = (CommandCategory.VECTOR, "Determinant")
    
    MIRROR = (CommandCategory.TRANSFORMATION, "Mirror")
    DILATE = (CommandCategory.TRANSFORMATION, "Dilate")
    ROTATE = (CommandCategory.TRANSFORMATION, "Rotate")
    TRANSLATE = (CommandCategory.TRANSFORMATION, "Translate")
    
    TEXT = (CommandCategory.TEXT, "Text")
    
    IF = (CommandCategory.LOGICAL, "If")
    COUNT_IF = (CommandCategory.LOGICAL, "CountIf")
    DEFINED = (CommandCategory.LOGICAL, "Defined")
    
    SET_COLOR = (CommandCategory.SCRIPTING, "SetColor")
    SET_LINE_THICKNESS = (CommandCategory.SCRIPTING, "SetLineThickness")
    SET_POINT_SIZE = (CommandCategory.SCRIPTING, "SetPointSize")
    DELETE = (CommandCategory.SCRIPTING, "Delete")
    
    def __init__(self, category: CommandCategory, name: str):
        self.category = category
        self.cmdName = name
    
    def __str__(self) -> str:
        return self.cmdName
    
    @classmethod
    def get_by_name(cls, name: str) -> Optional['Commands']:
        for cmd in cls:
            if cmd.cmdName == name:
                return cmd
        return None


class ErrorType(Enum):
    UNKNOWN_COMMAND = "UnknownCommand"
    ILLEGAL_ARGUMENT = "IllegalArgument"
    ILLEGAL_ARGUMENT_NUMBER = "IllegalArgumentNumber"
    ILLEGAL_BOOLEAN = "IllegalBoolean"
    ILLEGAL_COMPARISON = "IllegalComparison"
    ILLEGAL_LIST_OPERATION = "IllegalListOperation"
    ILLEGAL_ASSIGNMENT = "IllegalAssignment"
    UNBALANCED_BRACKETS = "UnbalancedBrackets"
    CIRCULAR_DEFINITION = "CircularDefinition"
    INVALID_INPUT = "InvalidInput"
    UNDEFINED_VARIABLE = "UndefinedVariable"
    NAME_USED = "NameUsed"
    CHANGE_DEPENDENT = "ChangeDependent"
    NUMBER_EXPECTED = "NumberExpected"
    FUNCTION_EXPECTED = "FunctionExpected"
    INVALID_EQUATION = "InvalidEquation"
    INVALID_FUNCTION = "InvalidFunction"


class CommandError(Exception):
    def __init__(self, error_type: ErrorType, command_name: Optional[str] = None, 
                 message: Optional[str] = None, args: Optional[List[str]] = None):
        self.error_type = error_type
        self.command_name = command_name
        self.message = message
        self.args = args or []
        super().__init__(self.get_error_message())
    
    def get_error_message(self) -> str:
        base_message = self.error_type.value
        if self.message:
            return self.message
        if self.command_name:
            return f"{base_message}: {self.command_name}"
        if self.args:
            return f"{base_message}: {', '.join(self.args)}"
        return base_message
    
    def __str__(self) -> str:
        return self.get_error_message()


class CommandNotFoundError(CommandError):
    def __init__(self, command_name: str):
        super().__init__(ErrorType.UNKNOWN_COMMAND, command_name)


class ArgumentError(CommandError):
    def __init__(self, command_name: str, arg_value: str, message: Optional[str] = None):
        super().__init__(ErrorType.ILLEGAL_ARGUMENT, command_name, message, [arg_value])


class ArgumentNumberError(CommandError):
    def __init__(self, command_name: str, expected: int, actual: int):
        message = f"Expected {expected} arguments, got {actual}"
        super().__init__(ErrorType.ILLEGAL_ARGUMENT_NUMBER, command_name, message)


class CircularDefinitionError(CommandError):
    def __init__(self, message: str = "Circular definition detected"):
        super().__init__(ErrorType.CIRCULAR_DEFINITION, message=message)


class InvalidInputError(CommandError):
    def __init__(self, message: str = "Invalid input"):
        super().__init__(ErrorType.INVALID_INPUT, message=message)
