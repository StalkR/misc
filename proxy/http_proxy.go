// Binary http_proxy is a simple HTTP proxy, no caching.
package main

import (
	"crypto/tls"
	"flag"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"strings"
	"time"
)

var (
	flagListen       = flag.String("listen", ":8080", "Address to listen on.")
	flagForwardedFor = flag.Bool("forwardedfor", false, "Add client IP to X-Forwarded-For header.")
)

func main() {
	flag.Parse()
	srv := &http.Server{
		Addr: *flagListen,
		Handler: http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			if r.Method == http.MethodConnect {
				connect(w, r)
				return
			}
			proxy(w, r)
		}),
		// Disable direct HTTP/2 because hijacking is not possible.
		// Fortunately, in practice it works because it uses CONNECT then inside HTTP/2.
		TLSNextProto: map[string]func(*http.Server, *tls.Conn, http.Handler){},
	}
	log.Printf("Listening on %v", srv.Addr)
	log.Fatal(srv.ListenAndServe())
}

func connect(w http.ResponseWriter, req *http.Request) {
	dst, err := net.DialTimeout("tcp", req.Host, 30*time.Second)
	if err != nil {
		log.Printf("%v %v %v dial error: %v", req.RemoteAddr, req.Method, req.URL, err)
		http.Error(w, fmt.Sprintf("dial error: %v", err), http.StatusServiceUnavailable)
		return
	}
	w.WriteHeader(http.StatusOK)
	hijacker, ok := w.(http.Hijacker)
	if !ok {
		log.Printf("%v %v %v hijacking not supported", req.RemoteAddr, req.Method, req.URL)
		http.Error(w, "hijacking not supported", http.StatusInternalServerError)
		return
	}
	src, _, err := hijacker.Hijack()
	if err != nil {
		log.Printf("%v %v %v hijack error: %v", req.RemoteAddr, req.Method, req.URL, err)
		http.Error(w, fmt.Sprintf("hijack error: %v", err), http.StatusServiceUnavailable)
		return
	}
	log.Printf("%v %v %v %v", req.RemoteAddr, req.Method, req.URL, http.StatusOK)
	go transfer(dst, src)
	go transfer(src, dst)
}

func transfer(dst io.WriteCloser, src io.ReadCloser) {
	defer dst.Close()
	defer src.Close()
	io.Copy(dst, src)
}

func proxy(w http.ResponseWriter, req *http.Request) {
	if *flagForwardedFor {
		clientIP, _, err := net.SplitHostPort(req.RemoteAddr)
		if err != nil {
			log.Printf("%v %v %v invalid remote address: %v", req.RemoteAddr, req.Method, req.URL, err)
			http.Error(w, "invalid remote address", http.StatusInternalServerError)
			return
		}
		appendHostToXForwardHeader(req.Header, clientIP)
	}
	delHopHeaders(req.Header)
	resp, err := http.DefaultTransport.RoundTrip(req)
	if err != nil {
		log.Printf("%v %v %v error sending request: %v", req.RemoteAddr, req.Method, req.URL, err)
		http.Error(w, fmt.Sprintf("proxy failed: %v", err), http.StatusInternalServerError)
		return
	}
	defer resp.Body.Close()
	log.Printf("%v %v %v %v", req.RemoteAddr, req.Method, req.URL, resp.Status)
	delHopHeaders(resp.Header)
	copyHeader(w.Header(), resp.Header)
	w.WriteHeader(resp.StatusCode)
	io.Copy(w, resp.Body)
}

// Hop-by-hop headers. These are removed when sent to the backend.
// http://www.w3.org/Protocols/rfc2616/rfc2616-sec13.html
var hopHeaders = []string{
	"Connection",
	"Keep-Alive",
	"Proxy-Authenticate",
	"Proxy-Authorization",
	"Te", // canonicalized version of "TE"
	"Trailers",
	"Transfer-Encoding",
	"Upgrade",
}

func delHopHeaders(header http.Header) {
	for _, h := range hopHeaders {
		header.Del(h)
	}
}

func copyHeader(dst, src http.Header) {
	for k, vv := range src {
		for _, v := range vv {
			dst.Add(k, v)
		}
	}
}

func appendHostToXForwardHeader(header http.Header, host string) {
	// If we aren't the first proxy retain prior
	// X-Forwarded-For information as a comma+space
	// separated list and fold multiple headers into one.
	if prior, ok := header["X-Forwarded-For"]; ok {
		host = strings.Join(prior, ", ") + ", " + host
	}
	header.Set("X-Forwarded-For", host)
}
