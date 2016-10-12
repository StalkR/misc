// Binary monitor monitors a domain with VeriSign's DNSSEC debugger.
package main

import (
	"flag"
	"fmt"
	"log"
	"os"
	"os/exec"
	"strings"
	"time"

	"github.com/StalkR/misc/dnssec/debugger"
)

var (
	flagDomain   = flag.String("domain", "", "Domain name to check.")
	flagDuration = flag.Duration("every", 12*time.Hour, "Check every duration.")
	flagFrom     = flag.String("from", "", "Email sender.")
	flagTo       = flag.String("to", "", "Email recipient.")
)

func main() {
	flag.Parse()
	if *flagDomain == "" || *flagFrom == "" || *flagTo == "" {
		flag.PrintDefaults()
		os.Exit(1)
	}
	var state debugger.Status
	var warnings int
	for ; ; time.Sleep(*flagDuration) {
		var result debugger.Status
		var details string
		analysis, err := debugger.Analyze(*flagDomain)
		if err != nil {
			log.Printf("[Analyze (%s)] Error: %v", state, err)
			result = debugger.WARNING
			details = err.Error()
		} else {
			log.Printf("[Analyze (%s)] Status: %s", state, analysis.Status())
			result = analysis.Status()
			details = analysis.String()
		}

		/*
			State machine:
			      +----> OK <--+
			      v            v
			  WARNING ------> ERROR

			- 3 successive warnings becomes an error
			- transitions in or out of error state generates an alert
		*/
		var newState debugger.Status
		switch state {
		case debugger.OK:
			switch result {
			case debugger.WARNING:
				newState = debugger.WARNING
			case debugger.ERROR:
				newState = debugger.ERROR
			}
		case debugger.WARNING:
			switch result {
			case debugger.OK:
				newState = debugger.OK
				warnings = 0
			case debugger.WARNING:
				warnings++
				if warnings > 3 {
					newState = debugger.ERROR
					warnings = 0
				}
			case debugger.ERROR:
				newState = debugger.ERROR
				warnings = 0
			}

		case debugger.ERROR:
			switch result {
			case debugger.OK:
				newState = debugger.OK
			}
		}

		if state == newState {
			continue
		}
		if state == debugger.ERROR || newState == debugger.ERROR {
			log.Printf("[Analyze (%s)] New state: %s", state, newState)
			if err := email(newState.String(), details); err != nil {
				log.Print(err)
			}
		}
		state = newState
	}
}

func email(state, body string) error {
	subject := fmt.Sprintf("DNSSEC monitor: %s [%s]", *flagDomain, state)
	return mail(*flagFrom, *flagTo, subject, body)
}

func mail(from, to, subject, body string) error {
	cmd := exec.Command("/usr/sbin/sendmail", "-t")
	msg := fmt.Sprintf("From: %s\nTo: %s\nSubject: %s\n\n%s", from, to, subject, body)
	cmd.Stdin = strings.NewReader(msg)
	out, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("mail error: %v; out: %q", err, out)
	}
	return nil
}
