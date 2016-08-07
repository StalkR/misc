= Serial to VM

== Linux

Locally:

```
socat FILE:`tty`,raw,echo=0 UNIX:<serial>
```

Remotely:

```
socat FILE:`tty`,raw,echo=0 'EXEC:"ssh <host> socat - UNIX:<serial>"'
```

== Windows

Create a shortcut to mintty, then use socat like for Linux.

```
C:\cygwin64\bin\mintty.exe -e bash -c 'SSH_AUTH_SOCK=~/.ssh-agent socat FILE:`tty`,raw,echo=0 "EXEC:\"ssh <host> socat - UNIX:<serial>\""'
```

Note mintty starts with an empty env, so if using an SSH agent it will not be
available, so set the agent sock or run a script to connect to an existing.
