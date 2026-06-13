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
}

type token struct {
	tokenType tokenType
	value     string
}

type lexer struct {
	reader       *bufio.Reader
	state        lexerState
	tokens       []token
	currentValue string
	lineNumber   int
}

func runLexer(reader *bufio.Reader) []token {
	l := lexer{
		reader: reader,
		state:  lexerStateReading,
		tokens: []token{},
	}

	for {
		c, err := l.readChar()
		l.proccessChar(c)

		if err != nil {
			break
		}
	}

	return l.tokens
}

func printTokens(tokens []token) {
	fmt.Printf("Line 1: ")
	lineNumber := 1
	for _, t := range tokens {
		fmt.Printf("%v(%q) ", tokenTypeName[t.tokenType], t.value)
		if t.tokenType == tokenNewLine {
			lineNumber += 1
			fmt.Printf("\nLine %v: ", lineNumber)
		}
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

	return string(r), nil
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
		condition: isString("\n"),
		tokenType: tokenNewLine,
	},
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
	//TODO meta data line number and such?
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
			l.tokens = append(l.tokens, token{tokenType: tokenNewLine, value: c1})
			l.lineNumber += 1
		} else if c1 == "/" && c2 == "/" {
			l.state = lexerStateComment
		} else if unicode.IsNumber(rune(c1[0])) {
			l.state = lexerStateIntLiteral
			l.proccessChar(c1)
		} else if unicode.IsLetter(rune(c1[0])) || c1 == "_" { //TODO extend, like _foo := 3
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
					l.tokens = append(l.tokens, token{tokenType: m.tokenType, value: doubleChar})
					l.state = lexerStateSkip
					return
				}
			}
			for _, m := range singleCharMatchers {
				if m.condition(c1) {
					l.tokens = append(l.tokens, token{tokenType: m.tokenType, value: c1})
					return
				}
			}
			err := fmt.Sprintf("unknown char: %v %v, line: %d", c1, c2, l.lineNumber)
			fmt.Println(err)
			l.tokens = append(l.tokens, token{tokenType: tokenUnknown, value: c1})
		}

	case lexerStateComment:
		if c1 == "\n" {
			l.tokens = append(l.tokens, token{tokenType: tokenNewLine, value: c1})
			l.state = lexerStateReading
			l.lineNumber += 1
		}

	//TODO dupe code, improve?
	case lexerStateIdentifier:
		l.currentValue += c1
		if !isAlphaNum(c2) {
			l.tokens = append(l.tokens, token{tokenType: tokenIdentifier, value: l.currentValue})
			l.state = lexerStateReading
			l.currentValue = ""
		}

	case lexerStateIntLiteral:
		l.currentValue += c1
		if !unicode.IsNumber(rune(c2[0])) {
			l.tokens = append(l.tokens, token{tokenType: tokenIntLiteral, value: l.currentValue})
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
			l.tokens = append(l.tokens, token{tokenType: tokenStrLiteral, value: l.currentValue})
			l.state = lexerStateSkip
			l.currentValue = ""
		} else if c2 == "\"" && c1 != "\\" {
			l.currentValue += c1
			l.tokens = append(l.tokens, token{tokenType: tokenStrLiteral, value: l.currentValue})
			l.state = lexerStateSkip
			l.currentValue = ""
		} else if c1 != "\"" {
			l.currentValue += c1
		}
	}
}

// TODO scuffed? should we have not char but byte?
func isAlphaNum(c string) bool {
	r := rune(c[0])
	return unicode.IsNumber(r) || unicode.IsLetter(r)
}
