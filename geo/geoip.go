// Package geo implements geographic functions such as location of an IP address.
package geo

import (
	"encoding/json"
	"errors"
	"fmt"
	"io/ioutil"
	"net"
	"net/http"
	"strings"
)

type GeoIP struct {
	Latitude, Longitude                       float64
	Continent_code, Country_code, Region_code string
	Area_code, Metro_code, Postal_code        string
	Continent_name, Country_name, Region_name string
	Time_zone, City                           string
	Organization, Isp, Net_speed              string
	Ip_address, Domain, As_number             string
}

func (g *GeoIP) String() string {
	var values []string
	values = append(values, fmt.Sprintf("Latitude: %f", g.Latitude))
	values = append(values, fmt.Sprintf("Longitude: %f", g.Longitude))
	if g.Country_name != "" {
		values = append(values, fmt.Sprintf("Country: %s", g.Country_name))
	}
	if g.Region_name != "" {
		values = append(values, fmt.Sprintf("Region: %s", g.Region_name))
	}
	if g.City != "" {
		values = append(values, fmt.Sprintf("City: %s", g.City))
	}
	if g.Organization != "" {
		values = append(values, fmt.Sprintf("Org: %s", g.Organization))
	}
	if g.Isp != "" {
		values = append(values, fmt.Sprintf("ISP: %s", g.Isp))
	}
	if g.Ip_address != "" {
		values = append(values, fmt.Sprintf("IP: %s", g.Ip_address))
	}
	if g.Domain != "" {
		values = append(values, fmt.Sprintf("DNS: %s", g.Domain))
	}
	if g.As_number != "" {
		values = append(values, fmt.Sprintf("AS: %s", g.As_number))
	}
	return strings.Join(values, ", ")
}

// IPLocation gets location of an IP address using MaxMind demo.
// It is limited to 25 addresses per day.
func IPLocation(ip string) (g GeoIP, e error) {
	url := fmt.Sprintf("http://www.maxmind.com/geoip/city_isp_org/%s?demo=1", ip)
	resp, err := http.Get(url)
	if err != nil {
		return g, err
	}
	defer resp.Body.Close()
	c, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return g, err
	}
	err = json.Unmarshal(c, &g)
	// Go < 1.1 do not accept mismatched null so just skip this error.
	// See https://code.google.com/p/go/issues/detail?id=2540
	if err != nil && !strings.Contains(fmt.Sprintf("%s", err), "cannot unmarshal null") {
		return g, err
	}
	return g, nil
}

// Location gets location of a host/IP using IPLocation. If given a host,
// it first performs a DNS lookup and takes one of the IPs.
func Location(addr string) (g GeoIP, e error) {
	if net.ParseIP(addr) == nil {
		addrs, err := net.LookupHost(addr)
		if err != nil {
			return g, err
		}
		if len(addrs) == 0 {
			return g, errors.New("no IP for this host")
		}
		addr = strings.TrimRight(addrs[0], ".")
	}
	return IPLocation(addr)
}
