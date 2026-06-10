package main

import (
	"bufio"
	"fmt"
	"io"
	"os"
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
	tokenIdentifier tokenType = iota
	tokenIntLiteral
	tokenStrLiteral
	tokenNewLine
	tokenScope
	tokenDefine
	tokenOperator
	tokenComma
)

var tokenTypeName = map[tokenType]string{
	tokenIdentifier: "Identifier",
	tokenIntLiteral: "Int literal",
	tokenStrLiteral: "Str literal",
	tokenNewLine:    "New line",
	tokenScope:      "Scope",
	tokenDefine:     "Define",
	tokenOperator:   "Operator",
	tokenComma:      "Comma",
}

type token struct {
	tokenType tokenType
	value     string
}

type lexer struct {
	state        lexerState
	tokens       []token
	currentValue string
}

func runLexer(filename string) {
	file, err := os.Open(filename)
	if err != nil {
		panic(err)
	}

	defer file.Close()

	reader := bufio.NewReader(file)

	fmt.Println("Reading: " + filename)

	l := lexer{
		state:  lexerStateReading,
		tokens: []token{},
	}

	c1, _ := readChar(reader)
	for {
		c2, err := readChar(reader)
		if err != nil {
			break
		}

		l.proccessChar(c1, c2)
		c1 = c2
	}

	for _, t := range l.tokens {
		fmt.Printf("Type: %v, value: %q \n", tokenTypeName[t.tokenType], t.value)
	}

	fmt.Println("Done")
}

func readChar(reader *bufio.Reader) (string, error) {
	r, _, err := reader.ReadRune()
	if err == io.EOF {
		return "", err
	}

	if err != nil {
		panic(err)
	}

	return string(r), nil
}

func (l *lexer) proccessChar(c1, c2 string) {
	//TODO meta data line number and such?
	switch l.state {
	case lexerStateSkip:
		l.state = lexerStateReading
	case lexerStateReading:
		if c1 == " " || c1 == "\r" || c1 == "\t" {
			return
		}
		if c1 == "\n" {
			l.tokens = append(l.tokens, token{tokenType: tokenNewLine, value: c1})
		} else if c1 == "/" && c2 == "/" {
			l.state = lexerStateComment
		} else if unicode.IsNumber(rune(c1[0])) {
			l.state = lexerStateIntLiteral
			l.proccessChar(c1, c2)
		} else if unicode.IsLetter(rune(c1[0])) { //TODO extend, like _foo := 3
			l.state = lexerStateIdentifier
			l.proccessChar(c1, c2)
		} else if slices.Contains([]string{"(", ")", "{", "}"}, c1) {
			l.tokens = append(l.tokens, token{tokenType: tokenScope, value: c1})
		} else if c1 == ":" && c2 == "=" {
			l.tokens = append(l.tokens, token{tokenType: tokenDefine, value: c1 + c2})
			l.state = lexerStateSkip
		} else if c1 == "\"" {
			l.state = lexerStateStrLiteral
		} else if slices.Contains([]string{"+", "-", "*", "/"}, c1) {
			l.tokens = append(l.tokens, token{tokenType: tokenOperator, value: c1})
		} else if c1 == "," {
			l.tokens = append(l.tokens, token{tokenType: tokenComma, value: c1})
		} else {
			panic("unknow char: " + c1)
		}

	case lexerStateComment:
		if c1 == "\n" {
			l.state = lexerStateReading
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
		if c1 == "\"" {
			l.tokens = append(l.tokens, token{tokenType: tokenStrLiteral, value: l.currentValue})
			l.state = lexerStateReading
			l.currentValue = ""
		} else {
			l.currentValue += c1
		}
	}
}

// TODO scuffed? should we have not char but byte?
func isAlphaNum(c string) bool {
	r := rune(c[0])
	return unicode.IsNumber(r) || unicode.IsLetter(r)
}
