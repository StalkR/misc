/*
Binary dns_sesame is a DNS server responding desired IP addresses.

It is useful against firewalls wanting a fixed set of domains and
opening only on the IPs resolved.

Example usage:
        go run dns_sesame.go -address :53 -suffix z.stalkr.net

How it works:
- choose a name ('test'), send a DNS request to set the IP
   e.g. dig 1.2.3.4.test.z.stalkr.net >/dev/null
- request that name, it will have the desired IP
   e.g. dig +short test.z.stalkr.net => 1.2.3.4

Response TTL is 300 (5 minutes).
Pick a random name to avoid colliding with others.
Use multiple names to pool responses until TTL expires.
*/
package main

import (
	"flag"
	"fmt"
	"log"
	"math/rand"
	"net"
	"strings"
	"sync"
	"time"

	"github.com/miekg/dns"
)

const TTL = 5 * time.Minute

var (
	flagListen = flag.String("listen", ":53", "Address to listen to (TCP and UDP)")
	flagSuffix = flag.String("suffix", "", "Suffix for DNS")
)

func init() {
	rand.Seed(time.Now().Unix())
}

func main() {
	flag.Parse()
	*flagSuffix = strings.ToLower(*flagSuffix)
	if !strings.HasSuffix(*flagSuffix, ".") {
		*flagSuffix = *flagSuffix + "."
	}
	if !strings.HasPrefix(*flagSuffix, ".") {
		*flagSuffix = "." + *flagSuffix
	}

	cache := NewCache()
	dns.HandleFunc(".", func(w dns.ResponseWriter, req *dns.Msg) {
		handle(w, req, cache)
	})
	start(&dns.Server{Addr: *flagListen, Net: "udp"})
	start(&dns.Server{Addr: *flagListen, Net: "tcp"})
	for ; ; time.Sleep(TTL) {
		cache.GC()
	}
}

func start(server *dns.Server) {
	go func() {
		if err := server.ListenAndServe(); err != nil {
			log.Fatal(err)
		}
	}()
}

func handle(w dns.ResponseWriter, req *dns.Msg, cache *Cache) {
	name := strings.ToLower(req.Question[0].Name)
	if !strings.HasSuffix(name, *flagSuffix) {
		dns.HandleFailed(w, req)
		return
	}
	name = strings.TrimSuffix(name, *flagSuffix)
	if !strings.Contains(name, ".") {
		ip, ok := cache.Get(name)
		if !ok {
			dns.HandleFailed(w, req)
			return
		}
		answer(w, req, ip)
		return
	}

	var a, b, c, d byte
	if _, err := fmt.Sscanf(name, "%d.%d.%d.%d.%s", &a, &b, &c, &d, &name); err != nil {
		dns.HandleFailed(w, req)
		return
	}
	ip := net.IPv4(a, b, c, d)
	cache.Set(name, ip)
	answer(w, req, ip)
}

func answer(w dns.ResponseWriter, req *dns.Msg, ip net.IP) {
	m := new(dns.Msg)
	m.SetReply(req)
	m.Answer = []dns.RR{
		&dns.A{
			Hdr: dns.RR_Header{
				Name:   req.Question[0].Name,
				Rrtype: dns.TypeA,
				Class:  dns.ClassINET,
				Ttl:    uint32(TTL / time.Second),
			},
			A: ip,
		},
	}
	w.WriteMsg(m)
}

type Entry struct {
	ip  net.IP
	set time.Time
}

func (s *Entry) Expired() bool {
	return time.Now().After(s.set.Add(TTL))
}

type Cache struct {
	m  sync.Mutex
	db map[string]Entry
}

func NewCache() *Cache {
	return &Cache{
		db: map[string]Entry{},
	}
}

func (s *Cache) Set(key string, ip net.IP) {
	s.m.Lock()
	defer s.m.Unlock()
	s.db[key] = Entry{ip: ip, set: time.Now()}
}

func (s *Cache) Get(key string) (net.IP, bool) {
	s.m.Lock()
	defer s.m.Unlock()
	e, ok := s.db[key]
	if !ok {
		return nil, false
	}
	if e.Expired() {
		delete(s.db, key)
		return nil, false
	}
	return e.ip, true
}

func (s *Cache) GC() {
	s.m.Lock()
	defer s.m.Unlock()
	for key, e := range s.db {
		if e.Expired() {
			delete(s.db, key)
		}
	}
}
