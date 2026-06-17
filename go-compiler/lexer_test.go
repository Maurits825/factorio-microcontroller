package main

import (
	"bufio"
	"os"
	"strings"
	"testing"
)

func testToken(t *testing.T, s string, i int, expectedToken token) {
	statements := runLexer(bufio.NewReader(strings.NewReader(s)))
	tokens := statements[0].tokens
	if len(tokens) <= i {
		t.Errorf("FAIL: i=%d is outside of tokens size:%d", i, len(tokens))
		t.Errorf("Expected token: %v", expectedToken)
		t.Errorf("Got tokens: %v", tokens)
		t.FailNow()
	}

	if tokens[i].value != expectedToken.value {
		t.Errorf("FAIL: expected value %q, got %q", expectedToken.value, tokens[i].value)
	}
	if tokens[i].tokenType != expectedToken.tokenType {
		t.Errorf("FAIL: expected %v, got %v", tokenTypeName[expectedToken.tokenType], tokenTypeName[tokens[i].tokenType])
	}
}

func TestLexerFile(t *testing.T) {
	filename := "lexer.go"
	file, err := os.Open(filename)
	if err != nil {
		panic(err)
	}

	defer file.Close()

	reader := bufio.NewReader(file)

	tokens := runLexer(reader)
	if len(tokens) <= 0 {
		t.Error("FAIL: lexer.go failed, no tokens?")
	}
}

func TestLexerEscapeChar(t *testing.T) {
	testToken(t, `sempty1 := "" `, 2, token{tokenType: tokenStrLiteral, value: ""})
	testToken(t, `sempty2 := ""`, 2, token{tokenType: tokenStrLiteral, value: ""})
	testToken(t, `sempty4 := ""
	`, 2, token{tokenType: tokenStrLiteral, value: ""})
	testToken(t, "s4 := 1234", 2, token{tokenType: tokenIntLiteral, value: "1234"})
	testToken(t, `s1n:= "s1r"`, 2, token{tokenType: tokenStrLiteral, value: "s1r"})
	testToken(t, `s2n:= "s2r\""`, 2, token{tokenType: tokenStrLiteral, value: `s2r"`})
	testToken(t, `s3n:= "s3.0r\"a"`, 2, token{tokenType: tokenStrLiteral, value: `s3.0r"a`})
	testToken(t, `s3n:= "s3r\"a"`, 2, token{tokenType: tokenStrLiteral, value: `s3r"a`})
	testToken(t, `s3n:= "s4r\"a"`, 2, token{tokenType: tokenStrLiteral, value: `s4r"a`})
	testToken(t, `if c1 == "\\" {`, 3, token{tokenType: tokenStrLiteral, value: `\`})
	testToken(t, `if c1 == "\\\"\\\\" {`, 3, token{tokenType: tokenStrLiteral, value: `\"\\`})
}

func TestBasicOps(t *testing.T) {
	testToken(t, `[]string{ "=", "!"}`, 4, token{tokenType: tokenStrLiteral, value: `=`})
	testToken(t, `a:=b&&c`, 3, token{tokenType: tokenLogicalOperator, value: `&&`})
	testToken(t, `a:=b>=c`, 3, token{tokenType: tokenComparisonOperator, value: `>=`})
	testToken(t, `a:=*c`, 2, token{tokenType: tokenOperator, value: `*`})
}
