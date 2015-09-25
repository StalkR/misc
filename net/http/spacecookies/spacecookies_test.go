package spacecookies

import (
	"bufio"
	"log"
	"net/http"
	"net/http/cookiejar"
	"reflect"
	"strings"
	"testing"
)

func ExampleNew() {
	jar, err := cookiejar.New(nil)
	if err != nil {
		log.Fatal(err)
	}
	client := http.DefaultClient
	client.Jar = jar

	// Wrap around the client's transport to add support for space cookies.
	client.Transport = New(client.Transport, jar)

	// Assuming example.com sets space cookies, they get added to the jar.
	resp, err := client.Get("https://example.com")
	if err != nil {
		log.Fatal(err)
	}
	defer resp.Body.Close()

	// So that following requests carry these cookies.
	resp, err = client.Get("https://example.com")
	if err != nil {
		log.Fatal(err)
	}
	defer resp.Body.Close()
}

func reply(req *http.Request, s string) (*http.Response, error) {
	return http.ReadResponse(bufio.NewReader(strings.NewReader(s)), req)
}

type fakeTransport struct{}

func (f *fakeTransport) RoundTrip(req *http.Request) (*http.Response, error) {
	return reply(req, "HTTP/1.1 200 OK\r\n"+
		"Set-Cookie: s p a c e=cookie\r\n\r\n")
}

func TestTransport(t *testing.T) {
	jar, err := cookiejar.New(nil)
	if err != nil {
		t.Fatal(err)
	}
	client := http.DefaultClient
	client.Jar = jar
	client.Transport = New(&fakeTransport{}, jar)

	resp, err := client.Get("https://example.com")
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	if len(jar.Cookies(resp.Request.URL)) != 1 {
		t.Fatal("did not receive space cookies")
	}
}

func TestParse(t *testing.T) {
	for _, tt := range []struct {
		setCookie string
		want      *http.Cookie
	}{
		{
			setCookie: "name=value; path=/; domain=example.com; Secure; httpOnly",
			want: &http.Cookie{
				Name:     "name",
				Value:    "value",
				Path:     "/",
				Domain:   "example.com",
				Secure:   true,
				HttpOnly: true,
			},
		},
		{
			setCookie: "s p a c e=cookie",
			want:      &http.Cookie{Name: "s p a c e", Value: "cookie"},
		},
		{
			setCookie: "invalid",
			want:      nil,
		},
	} {
		cookie := parse(tt.setCookie)
		if !reflect.DeepEqual(cookie, tt.want) {
			t.Errorf("parse(%s): got %v; want %v", tt.setCookie, cookie, tt.want)
		}
	}
}
