package main

import (
	"bufio"
	"fmt"
	"io"
	"slices"
	"unicode"
)

type lexerState int

const (
	lexerStateReading lexerState = iota
	lexerStateIdentifier
	lexerStateComment
	lexerStateIntLiteral
	lexerStateStrLiteral
	lexerStateSkip
)

type tokenType int

const (
	tokenUnknown tokenType = iota
	tokenIdentifier
	tokenIntLiteral
	tokenStrLiteral
	tokenNewLine
	tokenBracket
	tokenDefine
	tokenOperator
	tokenLogicalOperator
	tokenComparisonOperator
	tokenComma
	tokenColon
	tokenPeriod
	tokenAmpersand

	tokenIf
	tokenElse
	tokenRange
	tokenFunc
	tokenReturn
	tokenPackage
	tokenSwitch
	tokenCase
)

var tokenTypeName = map[tokenType]string{
	tokenUnknown:            "Unknown",
	tokenIdentifier:         "Identifier",
	tokenIntLiteral:         "Int literal",
	tokenStrLiteral:         "Str literal",
	tokenNewLine:            "New line",
	tokenBracket:            "Bracket",
	tokenDefine:             "Define",
	tokenOperator:           "Operator",
	tokenComma:              "Comma",
	tokenColon:              "Colon",
	tokenPeriod:             "Period",
	tokenLogicalOperator:    "Logical op",
	tokenComparisonOperator: "Comparison op",
	tokenAmpersand:          "Ampersand",

	tokenIf:      "If",
	tokenElse:    "Else",
	tokenRange:   "Range",
	tokenFunc:    "Function",
	tokenReturn:  "Return",
	tokenPackage: "Package",
	tokenSwitch:  "Switch",
	tokenCase:    "Case",
}

var reseverdIdentifiers = map[string]tokenType{
	"if":      tokenIf,
	"else":    tokenElse,
	"range":   tokenRange,
	"func":    tokenFunc,
	"return":  tokenReturn,
	"package": tokenPackage,
	"switch":  tokenSwitch,
	"case":    tokenCase,
}

type statement struct {
	tokens     []token
	lineNumber int
	rawLine    string
}

type token struct {
	tokenType tokenType
	value     string
	column    int
}

type lexer struct {
	reader           *bufio.Reader
	state            lexerState
	currentStatement *statement
	statements       []statement
	currentValue     string
	lineNumber       int
	column           int
}

func runLexer(reader *bufio.Reader) []statement {
	l := lexer{
		reader:     reader,
		state:      lexerStateReading,
		statements: []statement{{tokens: []token{}, lineNumber: 1}},
		lineNumber: 1,
	}
	l.currentStatement = &l.statements[0]

	for {
		c, err := l.readChar()
		l.proccessChar(c)

		if err != nil {
			break
		}
	}

	if len(l.statements[len(l.statements)-1].tokens) == 0 {
		l.statements = l.statements[:len(l.statements)-1]
	}

	return l.statements

}

func printTokens(tokens []token) {
	for _, t := range tokens {
		fmt.Printf("%v(%q) ", tokenTypeName[t.tokenType], t.value)
	}
	fmt.Println()
}

func (l *lexer) readChar() (string, error) {
	r, _, err := l.reader.ReadRune()
	if err == io.EOF {
		return " ", err
	}

	if err != nil {
		panic(err)
	}

	c := string(r)
	l.currentStatement.rawLine += c
	l.column += 1

	return c, nil
}

func (l *lexer) PeekChar() string {
	b, err := l.reader.Peek(1)

	if err == io.EOF {
		return " "
	}

	if err != nil {
		panic(err)
	}

	return string(b)
}

type stringMatcher struct {
	condition func(c string) bool
	tokenType tokenType
}

func isString(v string) func(c string) bool {
	return func(c string) bool {
		return c == v
	}
}

func isAnyString(vs []string) func(c string) bool {
	return func(c string) bool {
		return slices.Contains(vs, c)
	}
}

var singleCharMatchers = []stringMatcher{
	{
		condition: isString(","),
		tokenType: tokenComma,
	},
	{
		condition: isString("."),
		tokenType: tokenPeriod,
	},
	{
		condition: isString(":"),
		tokenType: tokenColon,
	},
	{
		condition: isString("&"),
		tokenType: tokenAmpersand,
	},
	{
		condition: isAnyString([]string{"+", "-", "*", "/", "=", "!"}),
		tokenType: tokenOperator,
	},
	{ // TODO maybe split this to bracket and scope, or token for each?
		condition: isAnyString([]string{"(", ")", "{", "}", "[", "]"}),
		tokenType: tokenBracket,
	},
	{
		condition: isAnyString([]string{">", "<"}),
		tokenType: tokenComparisonOperator,
	},
}

var doubleCharMatchers = []stringMatcher{
	{
		condition: isString(":="),
		tokenType: tokenDefine,
	},
	{
		condition: isAnyString([]string{"==", ">=", "<=", "!="}),
		tokenType: tokenComparisonOperator,
	},
	{
		condition: isAnyString([]string{"&&", "||"}),
		tokenType: tokenLogicalOperator,
	},
}

func (l *lexer) proccessChar(c1 string) {
	c2 := l.PeekChar()

	switch l.state {
	case lexerStateSkip:
		l.state = lexerStateReading
	case lexerStateReading:
		if c1 == " " || c1 == "\r" || c1 == "\t" {
			return
		}
		//TODO maybe can have a more generic way for this? like a dict or something, at least for the basic comma,colon,ops...
		if c1 == "\n" {
			l.lineNumber += 1
			l.column = 0
			if len(l.currentStatement.tokens) > 0 {
				l.addToken(tokenNewLine, c1)
				l.statements = append(l.statements, statement{tokens: []token{}, lineNumber: l.lineNumber})
				l.currentStatement = &l.statements[len(l.statements)-1]
			} else {
				l.currentStatement.lineNumber = l.lineNumber
				l.currentStatement.rawLine = ""
			}
		} else if c1 == "/" && c2 == "/" {
			l.state = lexerStateComment
		} else if unicode.IsNumber(rune(c1[0])) {
			l.state = lexerStateIntLiteral
			l.proccessChar(c1)
		} else if unicode.IsLetter(rune(c1[0])) || c1 == "_" { //TODO this catches all valid var names?
			l.state = lexerStateIdentifier
			l.proccessChar(c1)
		} else if c1 == "\"" {
			l.state = lexerStateStrLiteral
			c1, _ := l.readChar()
			l.proccessChar(c1)
		} else {
			doubleChar := c1 + c2
			for _, m := range doubleCharMatchers {
				if m.condition(doubleChar) {
					l.addToken(m.tokenType, doubleChar)
					l.state = lexerStateSkip
					return
				}
			}
			for _, m := range singleCharMatchers {
				if m.condition(c1) {
					l.addToken(m.tokenType, c1)
					return
				}
			}
			err := fmt.Sprintf("Error: unexpect char %q\n", c1)
			fmt.Print(err)
			fmt.Printf("Line %d: %q\n", l.lineNumber, l.currentStatement.rawLine)
			panic(err)
		}

	case lexerStateComment:
		if c1 == "\n" {
			l.state = lexerStateReading
			l.proccessChar(c1)
		}

	//TODO dupe code, improve?
	case lexerStateIdentifier:
		l.currentValue += c1
		if !isAlphaNum(c2) {
			t, exists := reseverdIdentifiers[l.currentValue]
			if !exists {
				t = tokenIdentifier
			}
			l.addToken(t, l.currentValue)
			l.state = lexerStateReading
			l.currentValue = ""
		}

	case lexerStateIntLiteral:
		l.currentValue += c1
		if !unicode.IsNumber(rune(c2[0])) {
			l.addToken(tokenIntLiteral, l.currentValue)
			l.state = lexerStateReading
			l.currentValue = ""
		}

	case lexerStateStrLiteral:
		//TODO string escaping hell
		if c1 == "\\" && c2 == "\"" {
			l.currentValue += c2
			l.readChar()
		} else if c1 == "\\" && c2 == "\\" {
			l.currentValue += c1
			l.readChar()
		} else if c1 == "\"" {
			l.addToken(tokenStrLiteral, l.currentValue)
			l.state = lexerStateSkip
			l.currentValue = ""
		} else if c2 == "\"" && c1 != "\\" {
			l.currentValue += c1
			l.addToken(tokenStrLiteral, l.currentValue)
			l.state = lexerStateSkip
			l.currentValue = ""
		} else if c1 != "\"" {
			l.currentValue += c1
		}
	}
}

func (l *lexer) addToken(ttype tokenType, value string) {
	t := token{tokenType: ttype, value: value, column: l.column}
	l.currentStatement.tokens = append(l.currentStatement.tokens, t)
}

// TODO scuffed? should we have not char but byte?
func isAlphaNum(c string) bool {
	r := rune(c[0])
	return unicode.IsNumber(r) || unicode.IsLetter(r)
}
