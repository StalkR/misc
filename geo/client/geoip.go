// GeoIP client.
package main

import (
	"fmt"
	"github.com/StalkR/misc/geo"
	"os"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Println("Usage: geoip <ip|host>")
		os.Exit(1)
	}
	g, err := geo.Location(os.Args[1])
	if err != nil {
		fmt.Println("Error:", err)
		os.Exit(1)
	}
	fmt.Println(g.String())
}
