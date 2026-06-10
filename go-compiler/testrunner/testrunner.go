package main

func main() {
	for i := range 10 {
		writeOut(i)
	}
}

func writeOut(v int) {
	asm("WOUTF,2", v)
}
