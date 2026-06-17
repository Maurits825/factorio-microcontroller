package main

import (
	"slices"
	"testing"
)

func createFuncToken(name string, args []variable) []token {
	start := []token{
		{tokenType: tokenFunc},
		{tokenType: tokenIdentifier, value: name},
		{tokenType: tokenBracket, value: "("},
	}
	end := []token{
		{tokenType: tokenBracket, value: ")"},
		{tokenType: tokenBracket, value: "{"},
		{tokenType: tokenNewLine, value: "\n"},
	}

	argsTokens := make([]token, 0, 2*len(args))
	for _, arg := range args {
		tName := token{
			tokenType: tokenIdentifier,
			value:     arg.name,
		}
		tType := token{
			tokenType: tokenIdentifier,
			value:     arg.vtype,
		}

		argsTokens = append(argsTokens, tName)
		argsTokens = append(argsTokens, tType)
		argsTokens = append(argsTokens, token{tokenType: tokenComma, value: ","})
	}
	if len(argsTokens) > 0 {
		argsTokens = argsTokens[:len(argsTokens)-1]
	}

	return slices.Concat(start, argsTokens, end)
}

func checkFunc(t *testing.T, f function, name string, args []variable) {
	if f.name != name {
		t.Errorf("FAIL: expected function name %v, got %v", name, f.name)
	}

	if len(f.args) != len(args) {
		t.Errorf("FAIL: expected args count %v, got %v", len(args), len(f.args))
	}

	for i, arg := range args {
		actualName := f.args[i].name
		actualType := f.args[i].vtype

		if actualName != arg.name {
			t.Errorf("FAIL: expected arg name %v, got %v", arg.name, actualName)
		}
		if actualType != arg.vtype {
			t.Errorf("FAIL: expected arg type %v, got %v", arg.vtype, actualType)
		}
	}
}

func testFunc(t *testing.T, name string, args []variable) {
	tokens := createFuncToken(name, args)
	p := initParser([]statement{{tokens: tokens}})

	p.handleFuncDeclaration()
	f := p.functions[name]

	checkFunc(t, f, name, args)
}

func TestFuncDeclaration(t *testing.T) {
	name := ""
	args := []variable{}

	name = "myfunction"
	testFunc(t, name, nil)

	name = "checkScore"
	args = []variable{
		{name: "score", vtype: "int"},
	}
	testFunc(t, name, args)

	name = "doSomething"
	args = []variable{
		{name: "varA", vtype: "int"},
		{name: "varB", vtype: "string"},
		{name: "varC", vtype: "myType"},
	}
	testFunc(t, name, args)
}

func TestFuncDeclarationMultiLine(t *testing.T) {
	name := "myFunction"
	args := []variable{
		{name: "varA", vtype: "int"},
		{name: "varB", vtype: "string"},
		{name: "varC", vtype: "myType"},
	}
	tokens := createFuncToken(name, args)
	args = append(args, variable{name: "varD", vtype: "int"})
	statements := []statement{
		{tokens: slices.Concat(tokens[:11], []token{{tokenType: tokenComma, value: ","}, {tokenType: tokenNewLine, value: "\n"}})},
		{tokens: slices.Concat([]token{
			{tokenType: tokenIdentifier, value: "varD"},
			{tokenType: tokenIdentifier, value: "int"},
		}, tokens[11:])},
	}

	p := initParser(statements)

	p.handleFuncDeclaration()
	f := p.functions[name]

	checkFunc(t, f, name, args)
}
