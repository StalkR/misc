// +build windows

// Package cygwin implements various Cygwin things, e.g. connecting to an ssh-agent.
package cygwin

import (
  "fmt"
  "io"
  "os/exec"
  "path/filepath"
  "strings"

  "golang.org/x/sys/windows/registry"
)

// SSHAgent connects to a running ssh-agent unix socket.
func SSHAgent() (io.ReadWriteCloser, error) {
  k, err := registry.OpenKey(registry.LOCAL_MACHINE, `SOFTWARE\Cygwin\setup`, registry.QUERY_VALUE)
  if err != nil {
    return nil, err
  }
  defer k.Close()
  cygwin, _, err := k.GetStringValue("rootdir")
  if err != nil {
    return nil, err
  }
  matches, err := filepath.Glob(cygwin + `\tmp\ssh-*\agent.*`)
  if err != nil {
    return nil, err
  }
  if len(matches) == 0 {
    return nil, fmt.Errorf("agent not found")
  }
  if len(matches) > 1 {
    return nil, fmt.Errorf("multiple agents found")
  }
  path := strings.Replace(strings.TrimPrefix(matches[0], cygwin), `\`, `/`, -1)
  // windows does not know how to connect to a cygwin UNIX socket,
  // so we use socat to convert it to a standard input/output.
  cmd := exec.Command(cygwin+`\bin\socat`, fmt.Sprintf("UNIX:%s", path), "-")
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
