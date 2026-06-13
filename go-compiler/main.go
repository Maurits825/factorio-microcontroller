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

	tokens := runLexer(reader)
	fmt.Printf("Total tokens: %d\n", len(tokens))
	printTokens(tokens)
}
