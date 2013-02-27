// IMDb client.
package main

import (
	"fmt"
	"github.com/StalkR/misc/imdb"
	"os"
	"regexp"
)

// FindTitle searches for a title and presents up to 10 results.
func FindTitle(q string) {
	r, err := imdb.FindTitle(q)
	if err != nil {
		fmt.Println("FindTitle error", err)
		os.Exit(1)
	}
	if len(r) == 0 {
		fmt.Println("No results found.")
		return
	}
	max := len(r)
	if max > 10 {
		max = 10
	}
	for i, tt := range r[:max] {
		t, err := imdb.NewTitle(tt.Id)
		if err != nil {
			fmt.Println("NewTitle error", err)
			os.Exit(1)
		}
		fmt.Printf("%2d. %s\n", i+1, t.String())
	}
}

// Title obtains information on a title id and presents it.
func Title(id string) {
	t, err := imdb.NewTitle(id)
	if err != nil {
		fmt.Println("NewTitle error", err)
		os.Exit(1)
	}
	fmt.Println(t.String())
}

func main() {
	if len(os.Args) < 2 {
		fmt.Println("Usage: imdb <query|ttID>")
		os.Exit(1)
	}
	arg := os.Args[1]
	matched, err := regexp.Match("^tt\\w+$", []byte(arg))
	if err != nil {
		fmt.Println("Match error", err)
		os.Exit(1)
	}
	if matched {
		Title(arg)
		return
	}
	FindTitle(arg)
}
