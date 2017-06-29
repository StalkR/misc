// Binary forward forwards IPv4/IPv6 TCP/UDP traffic.
package main

import (
	"flag"
	"io"
	"log"
	"net"
	"os"
	"strings"
)

var (
	listen  = flag.String("listen", "", `Listen proto and address, e.g. "tcp6/:1234".`)
	forward = flag.String("forward", "", `Forward proto and address, e.g. "tcp/1.2.3.4:5678`)
)

func main() {
	flag.Parse()
	if *listen == "" || *forward == "" {
		flag.Usage()
		os.Exit(1)
	}
	listens := strings.SplitN(*listen, "/", 2)
	ln, err := net.Listen(listens[0], listens[1])
	if err != nil {
		log.Fatal(err)
	}
	for {
		conn, err := ln.Accept()
		if err != nil {
			continue
		}
		go relay(conn)
	}
}

func relay(src net.Conn) {
	forwards := strings.SplitN(*forward, "/", 2)
	dst, err := net.Dial(forwards[0], forwards[1])
	if err != nil {
		log.Fatal(err)
	}
	go copy(src, dst)
	copy(dst, src)
}

func copy(dst io.WriteCloser, src io.Reader) {
	defer dst.Close()
	io.Copy(dst, src)
}
