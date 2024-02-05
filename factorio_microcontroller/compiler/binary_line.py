from dataclasses import dataclass

from compiler.assembly_line import AssemblyLine


@dataclass()
class BinaryLine:
    binary: str
    assembly_line: AssemblyLine
