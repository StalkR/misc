/*
Binary gorwi rewrites imports.

Example:
  $ go run gorwi.go -r '"flag" -> "other/flag"' test.go
*/
package main

import (
	"bytes"
	"flag"
	"fmt"
	"go/ast"
	"go/parser"
	"go/printer"
	"go/token"
	"io/ioutil"
	"os"
	"path/filepath"
	"regexp"
	"strings"
)

var rule = flag.String("r", "", "Import rewrite rule a -> b.")

var rewrite func(s string) string

func main() {
	flag.Parse()
	r := strings.Split(*rule, " -> ")
	if flag.NArg() == 0 || len(r) != 2 {
		fmt.Fprintf(os.Stderr, "usage: gorwi [flags] [path ...]\n")
		flag.PrintDefaults()
		os.Exit(1)
	}
	pattern, err := regexp.Compile(r[0])
	if err != nil {
		fmt.Fprintf(os.Stderr, "Invalid pattern: %v\n", err)
		os.Exit(1)
	}
	rewrite = func(s string) string {
		return pattern.ReplaceAllString(s, r[1])
	}
	if err := processArgs(); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
}

func processArgs() error {
	for i := 0; i < flag.NArg(); i++ {
		path := flag.Arg(i)
		switch dir, err := os.Stat(path); {
		case err != nil:
			return err
		case dir.IsDir():
			if err := processDir(path); err != nil {
				return err
			}
		default:
			if err := processFile(path); err != nil {
				return err
			}
		}
	}
	return nil
}

func processFile(file string) error {
	fset := token.NewFileSet()
	f, err := parser.ParseFile(fset, file, nil, parser.ParseComments)
	if err != nil {
		return fmt.Errorf("%s: %v", file, err)
	}
	var changed bool
	for _, d := range f.Decls {
		d, ok := d.(*ast.GenDecl)
		if !ok || d.Tok != token.IMPORT {
			// Not an import declaration, so we're done.
			// Imports are always first.
			break
		}
		for _, s := range d.Specs {
			s, ok := s.(*ast.ImportSpec)
			if !ok || s.Path.Kind != token.STRING {
				continue
			}
			old := s.Path.Value
			s.Path.Value = rewrite(s.Path.Value)
			if s.Path.Value != old {
				changed = true
			}
		}
	}
	if !changed {
		return nil
	}
	var buf bytes.Buffer
	if err := printer.Fprint(&buf, fset, f); err != nil {
		return err
	}
	return ioutil.WriteFile(file, buf.Bytes(), 0)
}

func processDir(path string) error {
	return filepath.Walk(path, visitFile)
}

func visitFile(path string, f os.FileInfo, err error) error {
	if err != nil {
		return err
	}
	if !isGoFile(f) {
		return nil
	}
	return processFile(path)
}

func isGoFile(f os.FileInfo) bool {
	// ignore non-Go files
	name := f.Name()
	return !f.IsDir() && !strings.HasPrefix(name, ".") && strings.HasSuffix(name, ".go")
}
