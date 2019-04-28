// Binary winpulse captures Audio from Windows and streams it to a PulseAudio server.
package main

import (
	"bufio"
	"context"
	"errors"
	"flag"
	"io"
	"log"
	"net"
	"os"
	"time"

	"github.com/StalkR/misc/pulseaudio"
	"github.com/StalkR/misc/windows/audio"
	"golang.org/x/sync/errgroup"
)

var flagServer = flag.String("server", "", "PulseAudio server to connect to (host:port).")

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
			if err := play(ctx, *flagServer, r); err != nil && err != io.EOF {
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
	return pulseaudio.Play(ctx, conn, stream)
}
