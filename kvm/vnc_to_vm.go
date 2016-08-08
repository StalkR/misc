// +build windows,!linux,!darwin

/*
Binary vnc_to_vm connects VNC to a remote VM via its socket file over SSH.
- connect to the local SSH agent in cygwin
- connect to the remote server with SSH
- relay the remote VNC socket file over SSH into a local listener
- start VNC viewer with it

Requirements:
- cygwin, with ssh and socat installed, ssh-agent running
- socat on the destination, TightVNC viewer locally

To avoid opening a command window:
  go build -ldflags "-H windowsgui" vnc_to_vm.go
*/

package main

import (
	"bufio"
	"flag"
	"fmt"
	"io"
	"io/ioutil"
	"net"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strings"

	"golang.org/x/crypto/ssh"
	"golang.org/x/crypto/ssh/agent"
)

var (
	flagHost   = flag.String("host", "", "Host to SSH to (user@host[:port]).")
	flagSocket = flag.String("socket", "", "Path to remote VNC socket.")
	flagViewer = flag.String("viewer", `C:\Program Files\TightVNC\tvnviewer.exe`, "Path to local TightVNC viewer.")
	flagCygwin = flag.String("cygwin", `C:\cygwin64`, "Path to cygwin root (for SSH agent and socat).")
)

func main() {
	flag.Parse()
	if err := launch(); err != nil {
		fmt.Printf("Error: %v\n\n[press enter to exit]", err)
		bufio.NewScanner(os.Stdin).Scan()
	}
}

func launch() error {
	if *flagHost == "" || *flagSocket == "" {
		flag.PrintDefaults()
		return nil
	}
	userHost := regexp.MustCompile(`^([^@]*)@(.*)$`).FindStringSubmatch(*flagHost)
	if len(userHost) == 0 {
		return fmt.Errorf("invalid host")
	}
	remote, err := sshToVNC(userHost[1], userHost[2], *flagSocket)
	if err != nil {
		return err
	}
	return vncViewer(remote)
}

func sshToVNC(user, host, socket string) (io.ReadWriteCloser, error) {
	agentc, err := connectAgent()
	if err != nil {
		return nil, err
	}
	defer agentc.Close()
	config := &ssh.ClientConfig{
		User: user,
		Auth: []ssh.AuthMethod{
			ssh.PublicKeysCallback(agent.NewClient(agentc).Signers),
		},
	}
	client, err := ssh.Dial("tcp", host, config)
	if err != nil {
		return nil, err
	}
	fmt.Println("[+] Connected to remote SSH server")
	session, err := client.NewSession()
	if err != nil {
		return nil, err
	}
	stdin, err := session.StdinPipe()
	if err != nil {
		return nil, err
	}
	stdout, err := session.StdoutPipe()
	if err != nil {
		return nil, err
	}
	if strings.Contains(socket, `"`) || strings.Contains(socket, `'`) {
		return nil, fmt.Errorf("invalid socket path")
	}
	if err := session.Start(fmt.Sprintf(`socat 'UNIX:"%s"' -`, socket)); err != nil {
		return nil, err
	}
	fmt.Println("[+] Connected to remote VNC")
	return &ReadWriteCloser{ioutil.NopCloser(stdout), stdin}, nil
}

func connectAgent() (io.ReadWriteCloser, error) {
	matches, err := filepath.Glob(*flagCygwin + `\tmp\ssh-*\agent.*`)
	if err != nil {
		return nil, err
	}
	if len(matches) == 0 {
		return nil, fmt.Errorf("agent not found")
	}
	if len(matches) > 1 {
		return nil, fmt.Errorf("multiple agents found")
	}
	path := strings.Replace(strings.TrimPrefix(matches[0], *flagCygwin), `\`, `/`, -1)
	cmd := exec.Command(*flagCygwin+`\bin\socat`, fmt.Sprintf("UNIX:%s", path), "-")
	stdin, err := cmd.StdinPipe()
	if err != nil {
		return nil, err
	}
	stdout, err := cmd.StdoutPipe()
	if err != nil {
		return nil, err
	}
	if err := cmd.Start(); err != nil {
		return nil, err
	}
	fmt.Println("[+] Connected to SSH agent")
	return &ReadWriteCloser{stdout, stdin}, nil
}

func vncViewer(remote io.ReadWriteCloser) error {
	ln, err := net.Listen("tcp", "localhost:0")
	if err != nil {
		return err
	}
	port := ln.Addr().(*net.TCPAddr).Port
	cmd := exec.Command(*flagViewer, fmt.Sprintf("localhost::%d", port))
	if err := cmd.Start(); err != nil {
		return err
	}
	fmt.Println("[+] VNC viewer started")
	local, err := ln.Accept()
	if err != nil {
		return err
	}
	if err := ln.Close(); err != nil {
		return err
	}
	fmt.Println("[+] VNC viewer connected")
	go io.Copy(remote, local)
	go io.Copy(local, remote)
	return cmd.Wait()
}

// ReadWriteCloser implements io.ReadWriteCloser.
type ReadWriteCloser struct {
	io.ReadCloser
	io.WriteCloser
}

// Close closes both the reader and writer.
func (s *ReadWriteCloser) Close() error {
	if err := s.ReadCloser.Close(); err != nil {
		return err
	}
	return s.WriteCloser.Close()
}
