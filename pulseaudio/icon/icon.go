//go:generate go run generate/data.go -in pulseaudio_200x200_gray.ico -out gray.go -pkg icon -var Gray
//go:generate go run generate/data.go -in pulseaudio_200x200_color.ico -out color.go -pkg icon -var Color

// Package icon holds a PulseAudio icon in ICO format.
package icon

import (
	"compress/zlib"
	"encoding/base64"
	"io/ioutil"
	"strings"
)

func decode(s string) []byte {
	decoder := base64.NewDecoder(base64.StdEncoding, strings.NewReader(s))
	r, err := zlib.NewReader(decoder)
	if err != nil {
		panic(err)
	}
	defer r.Close()
	b, err := ioutil.ReadAll(r)
	if err != nil {
		panic(err)
	}
	return b
}
