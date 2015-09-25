// Package spacecookies implements support for HTTP cookies with a space in their name.
// Go does not support it https://github.com/golang/go/issues/11519.
package spacecookies

import (
	"net/http"
	"strconv"
	"strings"
	"time"
)

// Transport implements a RoundTripper adding space cookies support to an existing RoundTripper.
type Transport struct {
	wrap http.RoundTripper
	jar  http.CookieJar
}

// New wraps around a Transport and a Cookie Jar to support cookies with space in the name.
// Just like an http.Client if transport is nil, http.DefaultTransport is used.
func New(transport http.RoundTripper, jar http.CookieJar) *Transport {
	if transport == nil {
		transport = http.DefaultTransport
	}
	return &Transport{
		wrap: transport,
		jar:  jar,
	}
}

// RoundTrip executes a single HTTP transaction to add support for space cookies.
// It is safe for concurrent use by multiple goroutines.
func (t *Transport) RoundTrip(req *http.Request) (*http.Response, error) {
	resp, err := t.wrap.RoundTrip(req)
	if err != nil {
		return nil, err
	}
	for _, s := range resp.Header[http.CanonicalHeaderKey("Set-Cookie")] {
		cookie := parse(s)
		if cookie != nil && strings.Contains(cookie.Name, " ") {
			// Only add the space cookies, normal ones are handled by net/http.
			t.jar.SetCookies(resp.Request.URL, []*http.Cookie{cookie})
		}
	}
	return resp, nil
}

// parse parses a Set-Cookie header into a cookie.
// It supports space in name unlike net/http.
// Returns nil if invalid.
func parse(s string) *http.Cookie {
	var c http.Cookie
	for i, field := range strings.Split(s, ";") {
		if len(field) == 0 {
			continue
		}
		nv := strings.SplitN(field, "=", 2)
		name := strings.TrimSpace(nv[0])
		value := ""
		if len(nv) > 1 {
			value = strings.TrimSpace(nv[1])
		}
		if i == 0 {
			if len(nv) != 2 {
				continue
			}
			c.Name = name
			c.Value = value
			continue
		}
		switch strings.ToLower(name) {
		case "secure":
			c.Secure = true
		case "httponly":
			c.HttpOnly = true
		case "domain":
			c.Domain = value
		case "max-age":
			secs, err := strconv.Atoi(value)
			if err != nil || secs != 0 && value[0] == '0' {
				continue
			}
			if secs <= 0 {
				c.MaxAge = -1
			} else {
				c.MaxAge = secs
			}
		case "expires":
			exptime, err := time.Parse(time.RFC1123, value)
			if err != nil {
				exptime, err = time.Parse("Mon, 02-Jan-2006 15:04:05 MST", value)
				if err != nil {
					c.Expires = time.Time{}
					continue
				}
			}
			c.Expires = exptime.UTC()
		case "path":
			c.Path = value
		}
	}
	if c.Name == "" {
		return nil
	}
	return &c
}
