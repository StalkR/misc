// Package debugger is an API to VeriSign's DNSSEC debugger.
package debugger

import (
	"bytes"
	"fmt"
	"io/ioutil"
	"net/http"
)

const baseURL = "http://dnssec-debugger.verisignlabs.com/"

// Analyze analyzes the full DNSSEC chain of a domain.
func Analyze(domain string) (Analysis, error) {
	resp, err := http.Get(fmt.Sprintf("%s/%s", baseURL, domain))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	b, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}
	return parse(string(b))
}

// An Analysis represents the analysis of all parts of a domain.
type Analysis []Domain

// Status returns the highest status for an analysis.
func (a Analysis) Status() Status {
	var status Status
	for _, domain := range a {
		for _, result := range domain.Results {
			if result.Status > status {
				status = result.Status
			}
		}
	}
	return status
}

// String formats the results of an analysis.
func (a Analysis) String() string {
	var b bytes.Buffer
	for _, domain := range a {
		fmt.Fprintf(&b, "# %s\n", domain.Name)
		for _, result := range domain.Results {
			fmt.Fprintf(&b, "- [%s] %s\n", result.Status, result.Details)
		}
	}
	return b.String()
}

// A Domain represents all the analysis for a domain.
type Domain struct {
	Name    string
	Results []Result
}

// A Result represents the result of one analysis item for a domain.
type Result struct {
	Status  Status
	Details string
}

// Status represents the result type of an analysis item.
type Status int

const (
	OK Status = iota
	WARNING
	ERROR
)

// String formats a status.
func (s Status) String() string {
	switch s {
	case OK:
		return "OK"
	case WARNING:
		return "WARNING"
	case ERROR:
		return "ERROR"
	default:
		panic(fmt.Sprintf("Status %d unknown", s))
	}
}
