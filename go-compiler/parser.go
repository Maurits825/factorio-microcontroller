package main

import (
	"fmt"
	"strings"
)

type parser struct {
	statements []statement

	statementIndex   int
	tokenIndex       int
	currentStatement *statement
	currentToken     *token

	functions map[string]function
}

type variable struct {
	name  string
	vtype string
}

type function struct {
	name string
	args []variable
}

func initParser(statements []statement) *parser {
	return &parser{
		statements:       statements,
		currentStatement: &statements[0],
		currentToken:     &statements[0].tokens[0],
		functions:        make(map[string]function),
	}
}

func runParser(statements []statement) map[string]function {
	fmt.Println("Running parser")

	p := initParser(statements)

	for p.peek() != nil {
		switch p.currentToken.tokenType {
		case tokenFunc:
			p.handleFuncDeclaration()
		default:
			p.next() //TODO
		}
	}

	return p.functions
}

func (p *parser) peek() *token {
	if p.tokenIndex+1 >= len(p.currentStatement.tokens) {
		if p.statementIndex+1 >= len(p.statements) {
			return nil
		}
		return &p.statements[p.statementIndex+1].tokens[0]
	}

	return &p.currentStatement.tokens[p.tokenIndex+1]
}

func (p *parser) next() {
	if p.tokenIndex+1 >= len(p.currentStatement.tokens) {
		if p.statementIndex+1 >= len(p.statements) {
			p.currentToken = nil
			return
		}
		p.statementIndex += 1
		p.tokenIndex = 0
		p.currentStatement = &p.statements[p.statementIndex]
	} else {
		p.tokenIndex += 1
	}

	p.currentToken = &p.currentStatement.tokens[p.tokenIndex]
}

func (p *parser) expect(ttype tokenType) *token {
	if p.currentToken.tokenType != ttype {
		lineNumber := fmt.Sprintf("Line %d: ", p.currentStatement.lineNumber)
		offset := len(lineNumber)
		tokenIndicator := strings.Repeat(" ", offset+p.currentToken.column)
		tokenIndicator += "v"
		err := fmt.Sprintf("Error: expected %v, got %v\n%s\n%s%q",
			tokenTypeName[ttype], tokenTypeName[p.currentToken.tokenType],
			tokenIndicator,
			lineNumber,
			p.currentStatement.rawLine)
		panic(err)
	}

	t := p.currentToken
	p.next()
	return t
}

func (p *parser) handleFuncDeclaration() {
	p.expect(tokenFunc)
	fName := p.expect(tokenIdentifier).value

	args := []variable{}

	//ptr receiver
	p.expect(tokenBracket)
	for {
		if p.currentToken.tokenType == tokenBracket {
			break
		}
		if p.currentToken.tokenType == tokenComma || p.currentToken.tokenType == tokenNewLine {
			p.next()
			continue
		}

		varName := p.expect(tokenIdentifier).value
		//TODO proper typing, just stringify now
		varType := ""
		for {
			if p.currentToken.tokenType == tokenComma || p.currentToken.tokenType == tokenBracket {
				break
			}

			varType += p.currentToken.value
			p.next()
		}
		args = append(args, variable{name: varName, vtype: varType})
	}

	p.functions[fName] = function{name: fName, args: args}
}
