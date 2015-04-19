package memory

import (
	"fmt"
	"strconv"
	"testing"
)

func addressViaFmt(t *testing.T, i interface{}) int {
	addr, err := strconv.ParseUint(fmt.Sprintf("%p", i), 0, 0)
	if err != nil {
		t.Fatalf("could not parse address of %p", i)
	}
	return int(addr)
}

func TestAddress(t *testing.T) {
	want := addressViaFmt(t, TestAddress)
	got := address(TestAddress)
	if got != want {
		t.Errorf("wrong address for func: got %x, want %x", got, want)
	}

	x := 1
	want = addressViaFmt(t, &x)
	got = address(&x)
	if got != want {
		t.Errorf("wrong address for var: got %x, want %x", got, want)
	}
}

func TestRead(t *testing.T) {
	want := 0x41414141
	got := read(address(&want))
	if got != want {
		t.Errorf("wrong read: got %x, want %x", got, want)
	}
}

func TestWrite(t *testing.T) {
	got := 0x41414141
	want := 0x42424242
	write(address(&got), want)
	if got != want {
		t.Errorf("wrong read: got %x, want %x", got, want)
	}
}

var callWorked = false // Has to be a global otherwise cannot be set from inside call.

func TestCall(t *testing.T) {
	call(address(func() { callWorked = true }))
	if !callWorked {
		t.Error("wrong call: got false, want true")
	}
}
