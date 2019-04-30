// Binary data converts a file into Go data.
package main

import (
	"compress/zlib"
	"encoding/base64"
	"flag"
	"fmt"
	"io"
	"log"
	"os"
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
	in, err := os.Open(*flagIn)
	if err != nil {
		return err
	}
	defer in.Close()
	var encoded strings.Builder
	encoder := base64.NewEncoder(base64.StdEncoding, &encoded)
	w := zlib.NewWriter(encoder)
	if _, err = io.Copy(w, in); err != nil {
		return err
	}
	if err := w.Close(); err != nil {
		return err
	}
	if err := encoder.Close(); err != nil {
		return err
	}
	out, err := os.OpenFile(*flagOut, os.O_WRONLY|os.O_CREATE|os.O_TRUNC, 0644)
	if err != nil {
		return err
	}
	fmt.Fprintf(out, `package %s

// %s contains the contents of: %s
var %s []byte

func init() {
	%s = decode(zlib_%s)
}

const zlib_%s = "%s"
`, *flagPkg, *flagVar, *flagIn, *flagVar, *flagVar, *flagVar, *flagVar, encoded.String())
	return out.Close()
}
