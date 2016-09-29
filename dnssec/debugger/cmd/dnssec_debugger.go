// Binary dnssec_debugger analyzes a domain with VeriSign's DNSSEC debugger.
package main

import (
	"flag"
	"fmt"
	"log"
	"os"

	"github.com/StalkR/misc/dnssec/debugger"
)

var domain = flag.String("domain", "", "Domain name to check.")

func main() {
	flag.Parse()
	if *domain == "" {
		flag.PrintDefaults()
		os.Exit(1)
	}
	analysis, err := debugger.Analyze(*domain)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Print(analysis)
	if analysis.Status() != debugger.OK {
		os.Exit(1)
	}
}
