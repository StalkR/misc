// Binary winpulse captures Audio from Windows and streams it to a PulseAudio server.
// It shows in systray with PulseAudio icon, right-click to exit.
// Build with `-ldflags -H=windowsgui` to avoid launching a console window.
package main

import (
	"context"
	"errors"
	"flag"
	"io"
	"log"
	"net"
	"time"

	"github.com/StalkR/misc/pulseaudio"
	"github.com/StalkR/misc/pulseaudio/icon"
	"github.com/StalkR/misc/windows/audio"
	"github.com/getlantern/systray"
	"golang.org/x/sync/errgroup"
)

var flagServer = flag.String("server", "", "PulseAudio server to connect to (host:port).")

func main() {
	ctx := context.Background()
	flag.Parse()
	if *flagServer == "" {
		flag.PrintDefaults()
		return
	}

	ctx, cancel := context.WithCancel(ctx)
	systray.Run(func() { onReady(ctx, *flagServer) }, cancel)
}

func onReady(ctx context.Context, server string) {
	systray.SetIcon(icon.Data)
	systray.SetTitle("WinPulse")
	exit := systray.AddMenuItem("Exit", "Exit")
	go func() {
		<-exit.ClickedCh
		systray.Quit()
	}()
	if err := launch(ctx, server); err != nil {
		log.Fatal(err)
	}
}

func launch(ctx context.Context, server string) error {
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
			if err := play(ctx, server, r); err != nil && err != io.EOF {
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

func play(ctx context.Context, server string, stream io.Reader) error {
	conn, err := net.Dial("tcp", server)
	if err != nil {
		return err
	}
	defer conn.Close()
	log.Print("Connected to PulseAudio")
	systray.SetTooltip("Connected to PulseAudio")
	return pulseaudio.Play(ctx, conn, stream)
}
