from enum import Enum


class TokenType(Enum):
    PREPROCESSOR = 0
    ASSEMBLY_INSTRUCTION = 1
    RESERVED_IDENTIFIER = 2
