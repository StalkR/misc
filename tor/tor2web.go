// Binary tor2web is a simple tor to web gateway.
//
// It requires a TOR transparent proxy and local
// DNS resolver configured for .onion addresses.
//
// Send traffic to it, e.g. hiddenservice.onion.example.net
// and it will respond with hiddenservice.onion.
//
// Use cgo to rely on system DNS resolver.
// GODEBUG=netdns=cgo go run tor2web.go
package main

import (
	"flag"
	"log"
	"net/http"
	"net/http/httputil"
	"strings"
)

var flagListen = flag.String("listen", ":9050", "Address to listen on.")

const onionTLD = ".onion"

func main() {
	flag.Parse()
	http.Handle("/", &httputil.ReverseProxy{
		Director: func(req *http.Request) {
			req.URL.Scheme = "http"
			host, port := req.Host, ""
			if p := strings.Index(host, ":"); p > 0 {
				host, port = host[:p], host[p:]
			}
			p := strings.Index(host, onionTLD)
			if p == -1 {
				panic("only for " + onionTLD)
			}
			req.URL.Host = host[:p+len(onionTLD)]
			if port != "" {
				req.URL.Host += port
			}
			if _, ok := req.Header["User-Agent"]; !ok {
				// explicitly disable User-Agent so it's not set to default value
				req.Header.Set("User-Agent", "")
			}
		},
	})
	log.Printf("Listening on %v", *flagListen)
	log.Fatal(http.ListenAndServe(*flagListen, nil))
}
