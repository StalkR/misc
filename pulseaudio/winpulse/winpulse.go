// +build windows

/*
Binary winpulse captures Audio from Windows and streams it to a PulseAudio server.
It can stream with native protocol or over SSH with pacat.
It shows in systray with PulseAudio icon, right-click to exit.
Build with `-ldflags -H=windowsgui` to avoid launching a console window.
*/
package main

import (
	"context"
	"errors"
	"flag"
	"fmt"
	"io"
	"log"
	"net"
	"os"
	"regexp"
	"time"

	"github.com/StalkR/misc/pulseaudio"
	"github.com/StalkR/misc/pulseaudio/icon"
	"github.com/StalkR/misc/windows/audio"
	"github.com/StalkR/misc/windows/cygwin"
	"github.com/getlantern/systray"
	"golang.org/x/crypto/ssh"
	"golang.org/x/crypto/ssh/agent"
	"golang.org/x/sync/errgroup"
)

var (
	flagServer = flag.String("server", "", "PulseAudio server to connect to (host:port).")
	flagSSH    = flag.String("ssh", "", "PulseAudio server to connect to via SSH + pacat (user@host[:port]).")
)

var sshRE = regexp.MustCompile(`^([^@]*)@(.*)$`) // matches user@host[:port]

func main() {
	flag.Parse()
	if *flagServer == "" && *flagSSH == "" {
		flag.PrintDefaults()
		return
	}
	if *flagSSH != "" && !sshRE.MatchString(*flagSSH) {
		log.Fatal("invalid user@host[:port]")
	}
	ctx := context.Background()
	systray.Run(
		func() { onReady(ctx) },
		func() { os.Exit(0) },
	)
}

func onReady(ctx context.Context) {
	systray.SetTitle("WinPulse")
	play := systray.AddMenuItem("Play", "Play")
	play.Hide()
	stop := systray.AddMenuItem("Stop", "Stop")
	stop.Hide()
	systray.AddSeparator()
	exit := systray.AddMenuItem("Exit", "Exit")

	go func() {
		<-exit.ClickedCh
		systray.Quit()
	}()

	for {
		ctx, cancel := context.WithCancel(ctx)
		var g errgroup.Group
		g.Go(func() error {
			return start(ctx)
		})
		systray.SetIcon(icon.Color)
		stop.Show()
		<-stop.ClickedCh
		stop.Hide()
		cancel()
		if err := g.Wait(); err != nil {
			log.Fatal(err)
		}
		log.Print("Stopped")
		systray.SetTooltip("Stopped")
		systray.SetIcon(icon.Gray)
		play.Show()
		<-play.ClickedCh
		play.Hide()
	}
}

func start(ctx context.Context) error {
	parentCtx := ctx
	g, ctx := errgroup.WithContext(ctx)
	g.Go(func() error {
		<-parentCtx.Done()
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
			log.Print("Connecting to PulseAudio...")
			systray.SetTooltip("Connecting to PulseAudio...")
			if err := play(ctx, r); err != nil && err != io.EOF {
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

func play(ctx context.Context, stream io.Reader) error {
	if *flagServer != "" {
		return playNative(ctx, stream, *flagServer)
	}
	userHost := sshRE.FindStringSubmatch(*flagSSH)
	if len(userHost) == 0 { // verified earlier anyway
		return fmt.Errorf("invalid user@host[:port]")
	}
	return playSSH(ctx, stream, userHost[1], userHost[2])
}

func playNative(ctx context.Context, stream io.Reader, server string) error {
	conn, err := net.Dial("tcp", server)
	if err != nil {
		return err
	}
	defer conn.Close()
	log.Print("Connected to PulseAudio")
	systray.SetTooltip("Connected to PulseAudio")
	return pulseaudio.Play(ctx, conn, stream)
}

func playSSH(ctx context.Context, stream io.Reader, user, host string) error {
	client, err := connectSSH(user, host)
	if err != nil {
		return err
	}
	defer client.Close()
	log.Print("Connected to server")
	session, err := client.NewSession()
	if err != nil {
		return err
	}
	defer session.Close()
	session.Stdin = stream
	if err := session.Start("pacat -p --format float32le"); err != nil {
		return err
	}
	log.Print("Connected to PulseAudio")
	systray.SetTooltip("Connected to PulseAudio")
	return session.Wait()
}

func connectSSH(user, host string) (*ssh.Client, error) {
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
