// Binary winpulse captures Audio from Windows and streams it to a PulseAudio server over SSH.
package main

import (
  "bufio"
  "context"
  "errors"
  "flag"
  "fmt"
  "io"
  "log"
  "os"
  "regexp"
  "time"

  "github.com/StalkR/misc/windows/audio"
  "github.com/StalkR/misc/windows/cygwin"
  "golang.org/x/crypto/ssh"
  "golang.org/x/crypto/ssh/agent"
  "golang.org/x/sync/errgroup"
)

var flagServer = flag.String("server", "", "PulseAudio server to connect to via SSH + pacat (user@host[:port]).")

func main() {
  flag.Parse()
  if err := launch(context.Background()); err != nil {
    log.Fatal(err)
  }
}

func launch(ctx context.Context) error {
  if *flagServer == "" {
    flag.PrintDefaults()
    return nil
  }
  userHost := regexp.MustCompile(`^([^@]*)@(.*)$`).FindStringSubmatch(*flagServer)
  if len(userHost) == 0 {
    return fmt.Errorf("invalid host")
  }

  g, ctx := errgroup.WithContext(ctx)
  g.Go(func() error {
    log.Print("Press enter to stop")
    bufio.NewScanner(os.Stdin).Scan()
    return errStop
  })

  r, w := io.Pipe()
  g.Go(func() error {
    defer w.Close()
    return audio.Capture(ctx, w)
  })

  g.Go(func() error {
    defer r.Close()
    for ; ; time.Sleep(time.Second) {
      if err := play(userHost[1], userHost[2], r); err != nil && err != io.EOF {
        log.Printf("error: %v", err)
      }
      select {
      case <-ctx.Done():
        return nil
      default:
      }
    }
  })

  if err := g.Wait(); err != nil && err != errStop {
    return err
  }
  return nil
}

var errStop = errors.New("stop")

func play(user, host string, stream io.Reader) error {
  client, err := connect(user, host)
  if err != nil {
    return err
  }
  log.Print("Connected to server")
  session, err := client.NewSession()
  if err != nil {
    return err
  }
  session.Stdin = stream
  if err := session.Start("pacat -p --format float32le"); err != nil {
    return err
  }
  log.Print("Connected to PulseAudio")
  return session.Wait()
}

func connect(user, host string) (*ssh.Client, error) {
  ag, err := cygwin.SSHAgent()
  if err != nil {
    return nil, err
  }
  defer ag.Close()
  config := &ssh.ClientConfig{
    User: user,
    Auth: []ssh.AuthMethod{
      ssh.PublicKeysCallback(agent.NewClient(ag).Signers),
    },
    HostKeyCallback: ssh.InsecureIgnoreHostKey(),
  }
  return ssh.Dial("tcp", host, config)
}
