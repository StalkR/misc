# Remote TTY with terminal resize (Linux)
Code from post located at https://blog.stalkr.net/2015/12/from-remote-shell-to-remote-terminal.html

## TL;DR

    go get github.com/StalkR/misc/pty
    go build github.com/StalkR/misc/pty/server
    ./server [--listen  [IP]:port] # default ':1337'
    go build github.com/StalkR/misc/pty/client
    ./client [--connect [IP]:port] # default ':1337'

## From simple reverse shell to remote tty and terminal resize

### Simple

Connect a program's stdin/out/err to a socket and back:

 * server:
 ```socat TCP-LISTEN:1337,reuseaddr,fork EXEC:bash```
 * client:
 ```socat - TCP:localhost:1337```

Problems:

 * `^C` quits your shell, not an app on the other end (very frustrating!)
 * it doesn't handle tty programs such as `top` or `vim`

### TTY

Alright, we can do better:

 * server:
 ```socat TCP-LISTEN:1337,reuseaddr,fork EXEC:bash,pty,stderr,setsid,sigint,sane```
 * client:
 ```socat FILE:`tty`,raw,echo=0 TCP:localhost:1337```

Problems:

 * resizing the local terminal does not resize the remote terminal
 * we can use `stty rows X cols Y` but on every window resize it is painful

### TTY and terminal resize

Signal `SIGWINCH` is delivered when the window size changes, and we
can use `ioctl` `TIOCGWINSZ` to know the rows/cols of the local terminal.
With that, we can send it over to the other end, and set the window size with
the `TIOCSWINSZ` `iotctl` counterpart. However the socket is taken for relaying
the tty data, so we need to multiplex some sort of control channel
to send the window change event and window size information.

Implemented at [server](server/server.go) and [client](client/client.go)

Note: this is a remote tty, not a reverse shell.

Add some TLS and you're not too far from SSH!
We could even add port forwarding or file transfer, why not even inline using
the control channel to handle commands and multiplex new streams on the fly...
