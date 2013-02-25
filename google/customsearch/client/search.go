// Google Custom Search client example.
package main

import (
	"fmt"
	"github.com/StalkR/misc/google/customsearch"
	"os"
	"strings"
)

func main() {
	if len(os.Args) < 4 {
		fmt.Println("Usage: search <key> <cx> <query>")
		os.Exit(1)
	}
	term := strings.TrimSpace(os.Args[3])
	if len(term) == 0 {
		return
	}
	r, err := customsearch.Search(term, os.Args[1], os.Args[2])
	if err != nil {
		fmt.Println("Error:", err)
		os.Exit(1)
	}
	for i, item := range r.Items {
		fmt.Printf("%2d. %s\n", i, item.String())
	}
}
