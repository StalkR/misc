// Binary tor2web is a simple tor to web gateway.
package main

import (
	"flag"
	"log"
	"net/http"
	"net/http/httputil"
	"os"
	"strings"
)

var (
	flagListen = flag.String("listen", ":9080", "Address to listen on.")
	flagServer = flag.String("server", "", "TOR socks server to proxy connections to.")
)

const onionTLD = ".onion"

func main() {
	flag.Parse()
	if *flagServer == "" {
		flag.Usage()
		os.Exit(1)
	}
	os.Setenv("HTTP_PROXY", "socks5://"+*flagServer)
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
