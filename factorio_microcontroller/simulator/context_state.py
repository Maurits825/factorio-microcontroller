from dataclasses import dataclass


@dataclass()
class ContextState:
    line_number: int
    line: str

    scope: str
    variables: dict
