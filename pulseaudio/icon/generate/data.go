// Binary data converts a file into Go data.
package main

import (
	"bytes"
	"flag"
	"fmt"
	"io/ioutil"
	"log"
	"strings"
)

var (
	flagIn  = flag.String("in", "", "Input file.")
	flagOut = flag.String("out", "", "Output file.")
	flagPkg = flag.String("pkg", "", "Package name.")
	flagVar = flag.String("var", "", "Variable name.")
)

func main() {
	flag.Parse()
	if err := launch(); err != nil {
		log.Fatal(err)
	}
}

func launch() error {
	var buf bytes.Buffer
	fmt.Fprintf(&buf, "package %s\n", *flagPkg)
	fmt.Fprintln(&buf)
	data, err := ioutil.ReadFile(*flagIn)
	if err != nil {
		return err
	}
	var hex []string
	for _, b := range data {
		hex = append(hex, fmt.Sprintf("0x%02x", b))
	}
	fmt.Fprintln(&buf, "// automatically generated")
	fmt.Fprintf(&buf, "var %s = []byte{%s}\n", *flagVar, strings.Join(hex, ", "))
	return ioutil.WriteFile(*flagOut, buf.Bytes(), 0644)
}
