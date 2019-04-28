// Binary winpulse captures Audio from Windows and streams it to a PulseAudio server over SSH.
// It shows in systray with PulseAudio icon, right-click to exit.
// Build with `-ldflags -H=windowsgui` to avoid launching a console window.
package main

import (
  "context"
  "errors"
  "flag"
  "io"
  "log"
  "regexp"
  "time"

  "github.com/StalkR/misc/pulseaudio/icon"
  "github.com/StalkR/misc/windows/audio"
  "github.com/StalkR/misc/windows/cygwin"
  "github.com/getlantern/systray"
  "golang.org/x/crypto/ssh"
  "golang.org/x/crypto/ssh/agent"
  "golang.org/x/sync/errgroup"
)

var flagServer = flag.String("server", "", "PulseAudio server to connect to via SSH + pacat (user@host[:port]).")

func main() {
  ctx := context.Background()
  flag.Parse()
  if *flagServer == "" {
    flag.PrintDefaults()
    return
  }
  userHost := regexp.MustCompile(`^([^@]*)@(.*)$`).FindStringSubmatch(*flagServer)
  if len(userHost) == 0 {
    log.Fatal("invalid host")
  }
  user, host := userHost[1], userHost[2]

  ctx, cancel := context.WithCancel(ctx)
  systray.Run(func() { onReady(ctx, user, host) }, cancel)
}

func onReady(ctx context.Context, user, host string) {
  systray.SetIcon(icon.Data)
  systray.SetTitle("WinPulse")
  exit := systray.AddMenuItem("Exit", "Exit")
  go func() {
    <-exit.ClickedCh
    systray.Quit()
  }()
  if err := launch(ctx, user, host); err != nil {
    log.Fatal(err)
  }
}

func launch(ctx context.Context, user, host string) error {
  gui := ctx
  g, ctx := errgroup.WithContext(ctx)
  g.Go(func() error {
    <-gui.Done()
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
      systray.SetTooltip("Connecting to PulseAudio...")
      if err := play(user, host, r); err != nil && err != io.EOF {
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
  systray.SetTooltip("Connected to PulseAudio")
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
