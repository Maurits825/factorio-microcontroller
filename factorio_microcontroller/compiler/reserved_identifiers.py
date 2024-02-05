from enum import Enum


class ReservedIdentifier(Enum):
    FUNCTION = 'FN'
    FUNCTION_END = 'END'
    GOTO_LABEL = 'LABEL'


RESERVED_IDENTIFIERS = [identifier.value for identifier in ReservedIdentifier]
MAIN_FUNCTION_NAME = "__main__"
