// Package memory showcases some unsafe operations in Go: read, write and call.
package memory

import (
	"reflect"
	"unsafe"
)

func address(thing interface{}) int {
	return int(reflect.ValueOf(thing).Pointer())
}

func read(addr int) int {
	paddr := &addr
	pv := reflect.NewAt(reflect.TypeOf(&paddr), unsafe.Pointer(&paddr))
	return **pv.Elem().Interface().(**int)
}

func write(addr, value int) {
	paddr := &addr
	pv := reflect.NewAt(reflect.TypeOf(&paddr), unsafe.Pointer(&paddr))
	**pv.Elem().Interface().(**int) = value
}

func call(addr int) {
	f := func() {}
	write(address(&f), address(&addr))
	f()
}
