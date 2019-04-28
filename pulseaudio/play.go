// Package pulseaudio implements playing audio using native protocol.
// It implements just enough of the protocol and nothing else.
package pulseaudio

import (
  "bytes"
  "context"
  "encoding/binary"
  "io"
  "io/ioutil"
)

// Play plays an audio stream on a PulseAudio server.
// Format is float32 little-endian, stereo, sampling 44100 Hz.
func Play(ctx context.Context, server io.ReadWriter, stream io.Reader) error {
  if err := pulseAuth(server); err != nil {
    return err
  }
  if err := pulseCreatePlaybackStream(server); err != nil {
    return err
  }
  go io.Copy(ioutil.Discard, server) // ignore the server

  b := make([]byte, 4096)
  for {
    select {
    case <-ctx.Done():
      return nil
    default:
    }
    n, err := stream.Read(b)
    if err != nil {
      return err
    }
    if err := pulseWritePacket(server, 0, b[:n]); err != nil {
      return err
    }
  }
  return nil
}

func pulseWritePacket(w io.Writer, index uint32, data []byte) error {
  b := &bytes.Buffer{}
  binary.Write(b, binary.BigEndian, uint32(len(data))) // length
  binary.Write(b, binary.BigEndian, uint32(index))     // index
  binary.Write(b, binary.BigEndian, uint64(0))         // offset
  binary.Write(b, binary.BigEndian, uint32(0))         // flags
  b.Write(data)
  _, err := w.Write(b.Bytes())
  return err
}

func pulseAuth(w io.Writer) error {
  b := &bytes.Buffer{}
  // command
  b.WriteByte('L')
  binary.Write(b, binary.BigEndian, uint32(8)) // op
  b.WriteByte('L')
  binary.Write(b, binary.BigEndian, uint32(0)) // tag

  // version
  b.WriteByte('L')
  binary.Write(b, binary.BigEndian, uint32(0x20))
  // cookie
  cookie := bytes.Repeat([]byte("\x00"), 256)
  b.WriteByte('x')
  binary.Write(b, binary.BigEndian, uint32(len(cookie)))
  b.Write(cookie)
  return pulseWritePacket(w, 0xFFFFFFFF, b.Bytes())
}

func pulseCreatePlaybackStream(w io.Writer) error {
  b := &bytes.Buffer{}
  b.WriteByte('L')
  binary.Write(b, binary.BigEndian, uint32(3)) // op
  b.WriteByte('L')
  binary.Write(b, binary.BigEndian, uint32(0)) // tag

  // sample spec
  b.WriteByte('a')
  b.WriteByte(5)                                   // format (5=float32le)
  b.WriteByte(2)                                   // channels
  binary.Write(b, binary.BigEndian, uint32(44100)) // rate
  // channel map
  b.WriteByte('m')
  b.WriteByte(2) // channels
  b.WriteByte(1) // left
  b.WriteByte(2) // right
  // sink index
  b.WriteByte('L')
  binary.Write(b, binary.BigEndian, uint32(0))
  // sink name
  b.WriteByte('N') // empty
  // buffer max length
  b.WriteByte('L')
  binary.Write(b, binary.BigEndian, uint32(0xffffffff))
  // corked
  b.WriteByte('0')
  // buffer target length
  b.WriteByte('L')
  binary.Write(b, binary.BigEndian, uint32(0))
  // buffer prebuffer length
  b.WriteByte('L')
  binary.Write(b, binary.BigEndian, uint32(0xffffffff))
  // buffer minimum request
  b.WriteByte('L')
  binary.Write(b, binary.BigEndian, uint32(0))
  // sync ID
  b.WriteByte('L')
  binary.Write(b, binary.BigEndian, uint32(0))
  // channel volumes
  b.WriteByte('v')
  b.WriteByte(2)                                   // channels
  binary.Write(b, binary.BigEndian, uint32(0x100)) // left
  binary.Write(b, binary.BigEndian, uint32(0x100)) // right
  // no remap
  b.WriteByte('0')
  // no remix
  b.WriteByte('0')
  // fix format
  b.WriteByte('0')
  // fix rate
  b.WriteByte('0')
  // fix channels
  b.WriteByte('0')
  // no move
  b.WriteByte('0')
  // variable rate
  b.WriteByte('0')
  // muted
  b.WriteByte('0')
  // adjust latency
  b.WriteByte('0')
  // properties
  b.WriteByte('P')
  b.WriteByte('N') // empty
  // volume set
  b.WriteByte('0')
  // early requests
  b.WriteByte('0')
  // muted set
  b.WriteByte('0')
  // don't inhibit auto suspend
  b.WriteByte('0')
  // fail on suspend
  b.WriteByte('0')
  // relative volume
  b.WriteByte('0')
  // passthrough
  b.WriteByte('0')
  // formats
  b.WriteByte('B')
  b.WriteByte(0) // empty
  return pulseWritePacket(w, 0xFFFFFFFF, b.Bytes())
}
