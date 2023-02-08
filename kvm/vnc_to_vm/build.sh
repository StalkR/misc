#!/bin/bash
GOOS=windows go build -ldflags -H=windowsgui vnc_to_vm.go
