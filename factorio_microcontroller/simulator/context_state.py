from dataclasses import dataclass

from compiler.assembly_line import AssemblyLine


@dataclass()
class ContextState:
    assembly_line: AssemblyLine

    scope: str
    variables: dict
