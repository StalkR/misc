// Binary client connects to a remote tty shell on the network.
package main

import (
	"encoding/gob"
	"flag"
	"io"
	"log"
	"net"
	"os"
	"os/signal"
	"syscall"

	"github.com/hashicorp/yamux"
	"golang.org/x/crypto/ssh/terminal"
)

var address = flag.String("connect", ":1337", "Address to connect to ([ip]:port).")

func main() {
	flag.Parse()

	conn, err := net.Dial("tcp", *address)
	if err != nil {
		log.Fatalf("connection error: %v", err)
	}

	session, err := yamux.Client(conn, nil)
	if err != nil {
		log.Fatalf("session error: %v", err)
	}

	stdin := int(os.Stdin.Fd())
	if !terminal.IsTerminal(stdin) {
		log.Fatal("not on a terminal")
	}
	oldState, err := terminal.MakeRaw(stdin)
	if err != nil {
		log.Fatalf("unable to make terminal raw: %v", err)
	}
	defer terminal.Restore(stdin, oldState)

	done := make(chan struct{})

	controlChannel, err := session.Open()
	if err != nil {
		log.Fatalf("control channel open error: %v", err)
	}
	go func() {
		w := gob.NewEncoder(controlChannel)
		c := make(chan os.Signal, 1)
		signal.Notify(c, syscall.SIGWINCH)
		for {
			cols, rows, err := terminal.GetSize(stdin)
			if err != nil {
				log.Printf("getsize error: %v", err)
				break
			}
			win := struct {
				Rows, Cols int
			}{Rows: rows, Cols: cols}
			if err := w.Encode(win); err != nil {
				break
			}
			<-c
		}
		done <- struct{}{}
	}()

	dataChannel, err := session.Open()
	if err != nil {
		log.Fatalf("data channel open error: %v", err)
	}
	cp := func(dst io.Writer, src io.Reader) {
		io.Copy(dst, src)
		done <- struct{}{}
	}
	go cp(dataChannel, os.Stdin)
	go cp(os.Stdout, dataChannel)

	<-done
	session.Close() // closes controlChannel, dataChannel, session and conn
}
