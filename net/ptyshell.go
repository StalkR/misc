// Binary ptyshell sets up a listening shell on a pty.
// Connect with: socat FILE:`tty`,raw,echo=0 TCP:localhost:1234
package main

import (
	"flag"
	"io"
	"log"
	"net"
	"os/exec"

	"github.com/kr/pty"
)

var address = flag.String("listen", ":1234", "Address to listen on ([ip]:port).")

func main() {
	ln, err := net.Listen("tcp", *address)
	if err != nil {
		log.Fatal(err)
	}
	log.Printf("listening on %s", *address)
	for {
		conn, err := ln.Accept()
		if err != nil {
			log.Printf("[%s] accept error: %v", conn.RemoteAddr().String(), err)
			continue
		}
		go handle(conn)
	}
}

func handle(conn net.Conn) {
	remote := conn.RemoteAddr().String()
	shell, err := pty.Start(exec.Command("bash"))
	if err != nil {
		log.Printf("[%s] pty error: %v", remote, err)
		return
	}
	done := make(chan struct{})
	cp := func(dst io.Writer, src io.Reader) {
		io.Copy(dst, src)
		done <- struct{}{}
	}
	go cp(conn, shell)
	go cp(shell, conn)
	// wait for one copy to signal termination and close both socket/pty
	// this will make the other copy stop as well
	<-done
	conn.Close()
	shell.Close()
	// wait for the other copy to finish before closing channel
	<-done
	close(done)
	log.Printf("[%s] done", remote)
}
