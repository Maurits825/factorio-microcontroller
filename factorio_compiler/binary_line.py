from dataclasses import dataclass

from factorio_compiler.assembly_line import AssemblyLine


@dataclass()
class BinaryLine:
    binary: str
    assembly_line: AssemblyLine
