// Google Custom Search client example.
package main

import (
	"fmt"
	"github.com/StalkR/misc/google/customsearch"
	"os"
)

func main() {
	if len(os.Args) < 4 {
		fmt.Println("Usage: search <key> <cx> <query>")
		os.Exit(1)
	}
	r, err := customsearch.Search(os.Args[3], os.Args[1], os.Args[2])
	if err != nil {
		fmt.Println("Error:", err)
		os.Exit(1)
	}
	for i, item := range r.Items {
		fmt.Printf("%2d. %s\n", i, item.String())
	}
}
