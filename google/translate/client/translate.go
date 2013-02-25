// Google Translate client.
package main

import (
	"fmt"
	"github.com/StalkR/misc/google/translate"
	"os"
	"strings"
)

func Supported(target, key string) {
	languages, err := translate.Languages(target, key)
	if err != nil {
		fmt.Println("Error:", err)
		os.Exit(1)
	}
	var langs []string
	for _, lang := range languages {
		langs = append(langs, lang.Language)
	}
	if target == "" {
		fmt.Println("Supported languages:", strings.Join(langs, ", "))
	} else {
		fmt.Printf("Supported languages for %s: %s\n", target,
			strings.Join(langs, ", "))
	}
}

func Translate(source, target, text, key string) {
	translated, err := translate.Translate(source, target, text, key)
	if err != nil {
		fmt.Println("Error:", err)
		os.Exit(1)
	}
	if source == "" {
		source = translated.DetectedSourceLanguage
	}
	fmt.Printf("%s->%s: %s\n", source, target, translated.TranslatedText)
}

func main() {
	switch {
	case len(os.Args) == 2:
		Supported("", os.Args[1])
	case len(os.Args) == 3:
		Supported(os.Args[2], os.Args[1])
	case len(os.Args) == 5:
		Translate(os.Args[2], os.Args[3], os.Args[4], os.Args[1])
	default:
		fmt.Println("Show all supported languages:")
		fmt.Println("	translate <key>")
		fmt.Println("Show supported languages for a given target language:")
		fmt.Println("	translate <key> <target>")
		fmt.Println("Translate text from source to target language:")
		fmt.Println("   translate <key> <source> <target> <text>")
		os.Exit(1)
	}
}
