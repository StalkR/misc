// Package cygwin implements various Cygwin things, e.g. connecting to an ssh-agent.
package cygwin

import (
  "flag"
  "fmt"
  "io"
  "os/exec"
  "path/filepath"
  "strings"
)

// TODO: find this dynamically
var flagCygwinRoot = flag.String("cygwin_root", `C:\cygwin64`, "Path to cygwin root (for SSH agent and socat).")

// SSHAgent connects to a running ssh-agent unix socket.
func SSHAgent() (io.ReadWriteCloser, error) {
  matches, err := filepath.Glob(*flagCygwinRoot + `\tmp\ssh-*\agent.*`)
  if err != nil {
    return nil, err
  }
  if len(matches) == 0 {
    return nil, fmt.Errorf("agent not found")
  }
  if len(matches) > 1 {
    return nil, fmt.Errorf("multiple agents found")
  }
  path := strings.Replace(strings.TrimPrefix(matches[0], *flagCygwinRoot), `\`, `/`, -1)
  // windows does not know how to connect to a cygwin UNIX socket,
  // so we use socat to convert it to a standard input/output.
  cmd := exec.Command(*flagCygwinRoot+`\bin\socat`, fmt.Sprintf("UNIX:%s", path), "-")
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
  return &sshAgent{stdout, stdin, cmd}, nil
}

// sshAgent implements io.ReadWriteCloser.
type sshAgent struct {
  stdout io.ReadCloser
  stdin  io.WriteCloser
  cmd    *exec.Cmd
}

func (s *sshAgent) Read(p []byte) (int, error)  { return s.stdout.Read(p) }
func (s *sshAgent) Write(p []byte) (int, error) { return s.stdin.Write(p) }
func (s *sshAgent) Close() error {
  var errors []error
  if err := s.stdin.Close(); err != nil {
    errors = append(errors, err)
  }
  if err := s.stdout.Close(); err != nil {
    errors = append(errors, err)
  }
  if err := s.cmd.Wait(); err != nil {
    errors = append(errors, err)
  }
  if len(errors) > 0 {
    if len(errors) == 1 {
      return errors[0]
    }
    return fmt.Errorf("close: %v errors, first: %v", len(errors), errors[0])
  }
  return nil
}
