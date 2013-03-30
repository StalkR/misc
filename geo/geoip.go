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
	Continent GeoContinent
	Country   GeoCountry
	Location  GeoLocation
	Traits    GeoTraits
}

type GeoContinent struct {
	Continent_code string
	Geoname_id     int
	Name           ContinentName
}

type ContinentName struct {
	En string
}

type GeoCountry struct {
	Geoname_id         int
	Iso_3166_1_alpha_2 string
	Iso_3166_1_alpha_3 string
	Name               CountryName
}

type CountryName struct {
	En string
}

type GeoLocation struct {
	Latitude, Longitude float64
	Time_zone           string
}

type GeoTraits struct {
	Autonomous_system_number       string
	Autonomous_system_organization string
	Domain, Ip_address             string
	Is_anonymous_proxy             string
	Isp, Organization              string
}

func (g *GeoIP) String() string {
	var values []string
	values = append(values, fmt.Sprintf("Latitude: %f", g.Location.Latitude))
	values = append(values, fmt.Sprintf("Longitude: %f", g.Location.Longitude))
	if g.Country.Name.En != "" {
		values = append(values, fmt.Sprintf("Country: %s", g.Country.Name.En))
	}
	if g.Traits.Organization != "" {
		values = append(values, fmt.Sprintf("Org: %s", g.Traits.Organization))
	}
	if g.Traits.Isp != "" {
		values = append(values, fmt.Sprintf("ISP: %s", g.Traits.Isp))
	}
	if g.Traits.Autonomous_system_number != "" {
		values = append(values, fmt.Sprintf("AS: %s", g.Traits.Autonomous_system_number))
	}
	if g.Traits.Ip_address != "" {
		values = append(values, fmt.Sprintf("IP: %s", g.Traits.Ip_address))
	}
	if g.Traits.Domain != "" {
		values = append(values, fmt.Sprintf("Domain: %s", g.Traits.Domain))
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
