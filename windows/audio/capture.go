// Package audio implements audio capture on Windows.
package audio

import (
  "context"
  "fmt"
  "io"
  "time"
  "unsafe"

  ole "github.com/go-ole/go-ole"
  wca "github.com/moutend/go-wca"
  "golang.org/x/sys/windows"
)

// Capture captures local audio and writes it to the sink.
// Format is float32 little-endian, stereo, sampling 44100 Hz.
func Capture(ctx context.Context, sink io.Writer) error {
  if err := ole.CoInitializeEx(0, ole.COINIT_MULTITHREADED); err != nil {
    return err
  }
  defer ole.CoUninitialize()

  var de *wca.IMMDeviceEnumerator
  if err := wca.CoCreateInstance(wca.CLSID_MMDeviceEnumerator, 0, wca.CLSCTX_ALL, wca.IID_IMMDeviceEnumerator, &de); err != nil {
    return err
  }
  defer de.Release()

  var mmd *wca.IMMDevice
  if err := de.GetDefaultAudioEndpoint(wca.ERender, wca.EConsole, &mmd); err != nil {
    return err
  }
  defer mmd.Release()

  var ac *wca.IAudioClient
  if err := mmd.Activate(wca.IID_IAudioClient, wca.CLSCTX_ALL, nil, &ac); err != nil {
    return err
  }
  defer ac.Release()

  var wfx *wca.WAVEFORMATEX
  if err := ac.GetMixFormat(&wfx); err != nil {
    return err
  }
  defer ole.CoTaskMemFree(uintptr(unsafe.Pointer(wfx)))

  const WAVE_FORMAT_EXTENSIBLE = 0xfffe // float32 little-endian
  if wfx.WFormatTag != WAVE_FORMAT_EXTENSIBLE {
    return fmt.Errorf("expected WAVE_FORMAT_EXTENSIBLE but got %v", wfx.WFormatTag)
  }

  var defaultPeriod wca.REFERENCE_TIME
  var minimumPeriod wca.REFERENCE_TIME
  if err := ac.GetDevicePeriod(&defaultPeriod, &minimumPeriod); err != nil {
    return err
  }
  latency := time.Duration(int(defaultPeriod) * 100)

  const hnsBufferDuration = 0
  const hnsPeriodicity = 0
  if err := ac.Initialize(wca.AUDCLNT_SHAREMODE_SHARED, wca.AUDCLNT_STREAMFLAGS_LOOPBACK, hnsBufferDuration, hnsPeriodicity, wfx, nil); err != nil {
    return err
  }

  var acc *wca.IAudioCaptureClient
  if err := ac.GetService(wca.IID_IAudioCaptureClient, &acc); err != nil {
    return err
  }
  defer acc.Release()

  // register with MMCSS
  revertMm, err := setMmThreadCharacteristics("Audio")
  if err != nil {
    return err
  }
  defer revertMm()

  if err := ac.Start(); err != nil {
    return err
  }
  defer ac.Stop()

  for {
    select {
    case <-ctx.Done():
      return nil
    default:
    }
    for {
      var packetLength uint32
      if err := acc.GetNextPacketSize(&packetLength); err != nil {
        return err
      }
      if packetLength == 0 {
        break
      }

      var data *byte
      var numFramesAvailable uint32
      var flags uint32
      if err := acc.GetBuffer(&data, &numFramesAvailable, &flags, nil, nil); err != nil {
        return err
      }
      // now careful not to return/break early and skipping ReleaseBuffer

      length := int(numFramesAvailable) * int(wfx.NBlockAlign)
      var sl = struct {
        addr *byte
        len  int
        cap  int
      }{data, length, length}
      b := *(*[]byte)(unsafe.Pointer(&sl))

      if flags&wca.AUDCLNT_BUFFERFLAGS_SILENT != 0 {
        // must ignore values and treat it as silence
        // memset zero, rely on compiler to optimize
        for i := range b {
          b[i] = 0
        }
      }

      _, writeErr := sink.Write(b)

      if err := acc.ReleaseBuffer(numFramesAvailable); err != nil {
        return err
      }

      if writeErr != nil {
        return writeErr
      }
    }
    time.Sleep(latency / 2)
  }
  return nil
}

var (
  modavrt                             = windows.MustLoadDLL("avrt.dll")
  procAvSetMmThreadCharacteristicsA   = modavrt.MustFindProc("AvSetMmThreadCharacteristicsA")
  procAvRevertMmThreadCharacteristics = modavrt.MustFindProc("AvRevertMmThreadCharacteristics")
)

func setMmThreadCharacteristics(name string) (func() error, error) {
  taskName, err := windows.BytePtrFromString(name)
  if err != nil {
    return nil, err
  }
  taskIndex := 0
  avHandle, _, _ := procAvSetMmThreadCharacteristicsA.Call(uintptr(unsafe.Pointer(taskName)), uintptr(unsafe.Pointer(&taskIndex)))
  if avHandle == 0 {
    return nil, fmt.Errorf("AvSetMmThreadCharacteristicsA returned %v", avHandle)
  }
  return func() error {
    r, _, _ := procAvRevertMmThreadCharacteristics.Call(avHandle)
    if r == 0 {
      return fmt.Errorf("AvRevertMmThreadCharacteristics returned %v", r)
    }
    return nil
  }, nil
}
