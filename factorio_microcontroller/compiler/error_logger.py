from factorio_compiler.assembly_line import AssemblyLine


class ErrorLogger:
    @staticmethod
    def format_error(error_msg, target,  assembly_line: AssemblyLine) -> str:
        return error_msg + ": " + target + ". Line number: " + str(assembly_line.line_number)
