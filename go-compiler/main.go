package main

import (
	"bufio"
	"fmt"
	"os"
)

func main() {
	// filename := "./testrunner/testrunner.go"
	filename := "lexer.go"

	fmt.Println("Reading: " + filename)
	file, err := os.Open(filename)
	if err != nil {
		panic(err)
	}

	defer file.Close()

	reader := bufio.NewReader(file)

	statements := runLexer(reader)
	// printStatements(statements)
	functions := runParser(statements)
	println("Functions:")
	println(functions)
}

func printStatements(statements []statement) {

	for _, s := range statements {
		fmt.Printf("\nLine %d\n", s.lineNumber)
		fmt.Printf("Raw: %q\n", s.rawLine)
		fmt.Print("Tokens: ")
		printTokens(s.tokens)
	}
}
