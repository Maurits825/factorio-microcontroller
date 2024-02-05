from dataclasses import dataclass

from compiler.token_type import TokenType


@dataclass()
class AssemblyToken:
    token_type: TokenType
    keyword: str
    arguments: list[str]


@dataclass()
class AssemblyLine:
    raw_line: str
    line_number: int

    line: str
    assembly_token: AssemblyToken
