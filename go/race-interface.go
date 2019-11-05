/*
go run race-interface.go
go run -race race-interface.go
GORACE=halt_on_error=1 go run -race race-interface.go
*/
package main

import (
	"fmt"
	"os"
	"runtime"
	"strconv"
)

func address(i interface{}) int {
	addr, err := strconv.ParseUint(fmt.Sprintf("%p", i), 0, 0)
	if err != nil {
		panic(err)
	}
	return int(addr)
}

type itf interface {
	X()
}

type safe struct {
	f *int
}

func (s safe) X() {}

type unsafe struct {
	f func()
}

func (u unsafe) X() {
	if u.f != nil {
		u.f()
	}
}

func win() {
	fmt.Println("win", i, j)
	os.Exit(1)
}

var i, j int

func main() {
	if runtime.NumCPU() < 2 {
		fmt.Println("need >= 2 CPUs")
		os.Exit(1)
	}
	var confused, good, bad itf
	pp := address(win)
	good = &safe{f: &pp}
	bad = &unsafe{}
	confused = good
	go func() {
		for {
			confused = bad
			// a single goroutine flipping confused exploits the race much
			// faster than having two goroutines alternate on the value
			// however, in modern Go versions we need to avoid the smarter
			// compiler removing both statements because they appear useless
			func() {
				if i >= 0 { // always true, but the compiler doesn't know that
					return
				}
				fmt.Println(confused) // avoid confused optimized away
			}()
			confused = good
			i++
		}
	}()
	// we want confused to point to the type of bad/unsafe (where func is)
	// but still have the value of good/safe (uint we control)
	for {
		confused.X()
		j++
	}
}
