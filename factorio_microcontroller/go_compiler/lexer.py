from dataclasses import dataclass
from enum import Enum


class LexerState(Enum):
    READING = 0
    COMMENT = 1
    FUNCTION = 2
    IDENTIFIER = 4
    SKIP = 5
    INT_LITERAL = 6
    STR_LITERAL = 7


class Keywords(Enum):
    FUNCTION = "func"
    MAIN_FN = "main"


class TokenType(Enum):
    IDENTIFIER = 0  # function and variable names?
    DEFINE = 1  #
    FUNCTION = 2
    FOR = 3
    # TODO how precise? do we need scope start/end, arglist ...?
    SCOPE = 4
    INT_LITERAL = 5
    STR_LITERAL = 6
    OPERATOR = 7
    NEW_LINE = 8


# TODO also meta data? line number and stuff
@dataclass
class Token:
    type: TokenType
    value: str

    def is_equal(self, t_type, value):
        return self.type == t_type and self.value == value


class Lexer:
    def __init__(self):
        self.state = LexerState.READING
        self.token_value = ""
        self.tokens = []

    # the point of this lexer is to output some list of tokens
    # maybe grouped by function also or scopes like for loops??
    def run(self, filename):
        self.__init__()

        print("reading: " + filename)

        with open(filename, encoding="utf-8") as f:
            # scuffed look ahead
            c1 = f.read(1)
            while c2 := f.read(1):
                # print(c1, c2)
                self.process_c(c1, c2)
                c1 = c2

        for t in self.tokens:
            print(str(t.type) + ": " + t.value)

        return self.tokens

    def tokenize_str(self, s: str):
        self.__init__()

        # s += "\n"

        i = 0
        while i < len(s) - 1:
            c1 = s[i]
            c2 = s[i + 1]
            self.process_c(c1, c2)
            i += 1

        return self.tokens

    def process_c(self, c1, c2):
        match self.state:
            case LexerState.SKIP:
                self.state = LexerState.READING
                return

            case LexerState.READING:
                if c1 == " ":
                    return

                if c1 == "\n":
                    self.tokens.append(Token(TokenType.NEW_LINE, "\\n"))

                elif c1 == "/" and c2 == "/":
                    self.state = LexerState.COMMENT

                elif c1.isdigit():
                    self.state = LexerState.INT_LITERAL
                    self.process_c(c1, c2)

                elif c1.isalnum():
                    self.state = LexerState.IDENTIFIER
                    self.process_c(c1, c2)

                elif c1 in ["(", ")", "{", "}"]:
                    self.tokens.append(Token(TokenType.SCOPE, c1))

                elif c1 == ":" and c2 == "=":
                    self.tokens.append(Token(TokenType.DEFINE, c1 + c2))
                    self.state = LexerState.SKIP

                elif c1 == "\"":
                    self.state = LexerState.STR_LITERAL

                elif c1 in ["+", "-", "*", "/"]:
                    self.tokens.append(Token(TokenType.OPERATOR, c1))
                else:
                    raise ValueError("Unknow char: " + c1)

            case LexerState.COMMENT:
                if c1 == "\n":
                    self.state = LexerState.READING

            case LexerState.IDENTIFIER:
                self.token_value += c1
                if not c2.isalnum():
                    t = self.tokenize(self.token_value)
                    self.tokens.append(t)
                    self.state = LexerState.READING
                    self.token_value = ""

            case LexerState.INT_LITERAL:
                self.token_value += c1
                if not c2.isdigit():
                    self.tokens.append(Token(TokenType.INT_LITERAL, self.token_value))
                    self.state = LexerState.READING
                    self.token_value = ""

            case LexerState.STR_LITERAL:
                if c1 == "\"":
                    self.tokens.append(Token(TokenType.STR_LITERAL, self.token_value))
                    self.state = LexerState.READING
                    self.token_value = ""
                else:
                    self.token_value += c1

    def tokenize(self, s):
        # figure out if its a keyword or something?
        # todo do this here or later
        # could just say its identifier, later we figure out
        # if its keyword?
        if s == "func":
            return Token(TokenType.FUNCTION, s)
        elif s == "for":
            return Token(TokenType.FOR, s)
        else:
            return Token(TokenType.IDENTIFIER, s)
