// Binary server exposes a local tty shell on the network.
package main

import (
	"encoding/gob"
	"flag"
	"io"
	"log"
	"net"
	"os"
	"os/exec"
	"syscall"
	"unsafe"

	"github.com/hashicorp/yamux"
	"github.com/kr/pty"
)

var address = flag.String("listen", ":1337", "Address to listen on ([ip]:port).")

func main() {
        flag.Parse()
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
	session, err := yamux.Server(conn, nil)
	if err != nil {
		log.Printf("[%s] session error: %v", remote, err)
		return
	}

	done := make(chan struct{})

	cmd := exec.Command("/bin/bash")
	shellPty, err := pty.Start(cmd)
	if err != nil {
		log.Printf("[%s] pty error: %v", remote, err)
		return
	}
	go func() {
		if err := cmd.Wait(); err != nil {
			log.Printf("[%s] wait error: %v", remote, err)
		}
		done <- struct{}{}
	}()

	controlChannel, err := session.Accept()
	if err != nil {
		log.Printf("[%s] control channel accept error: %v", remote, err)
		return
	}
	go func() {
		r := gob.NewDecoder(controlChannel)
		for {
			var win struct {
				Rows, Cols int
			}
			if err := r.Decode(&win); err != nil {
				break
			}
			if err := Setsize(shellPty, win.Rows, win.Cols); err != nil {
				log.Printf("[%s] setsize error: %v", remote, err)
				break
			}
			if err := syscall.Kill(cmd.Process.Pid, syscall.SIGWINCH); err != nil {
				log.Printf("[%s] sigwinch error: %v", remote, err)
				break
			}
		}
		done <- struct{}{}
	}()

	dataChannel, err := session.Accept()
	if err != nil {
		log.Printf("[%s] data channel accept error: %v", remote, err)
		return
	}
	cp := func(dst io.Writer, src io.Reader) {
		io.Copy(dst, src)
		done <- struct{}{}
	}
	go cp(dataChannel, shellPty)
	go cp(shellPty, dataChannel)

	<-done
	shellPty.Close()
	session.Close() // closes controlChannel, dataChannel, session and conn
	log.Printf("[%s] done", remote)
}

type winsize struct {
	ws_row    uint16
	ws_col    uint16
	ws_xpixel uint16
	ws_ypixel uint16
}

func Setsize(f *os.File, rows, cols int) error {
	ws := winsize{ws_row: uint16(rows), ws_col: uint16(cols)}
	_, _, errno := syscall.Syscall(
		syscall.SYS_IOCTL,
		f.Fd(),
		syscall.TIOCSWINSZ,
		uintptr(unsafe.Pointer(&ws)),
	)
	if errno != 0 {
		return syscall.Errno(errno)
	}
	return nil
}
