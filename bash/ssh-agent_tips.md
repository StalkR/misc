# Linux desktops

Most environments will start an ssh agent for you and propagate it to your shell via `SSH_AUTH_SOCK` environment variable: no problem.



# Windows, with cygwin and mintty

The problem is Windows doesn't start an ssh agent, so when we open a new shell and there is no ssh agent running, we need to start one, then when we open new shells we need to reattach to that one.

Put this in your `.bashrc`:

    # find a running ssh-agent and link to it
    # useful below and in other scenarios (e.g. root using user ssh agent)
    link_ssh_agent() {
      local dir sock
      dir=$(find /tmp -type d -name 'ssh-*' 2>/dev/null | head -1)
      sock=$(find "$dir" -type s -name 'agent.*' 2>/dev/null)
      if [[ -r "$sock" ]]; then
        ln -snf "$sock" ~/.ssh-agent
        echo "Agent linked: $sock"
        ssh-add -l
      else
        echo "Error: cannot find running ssh-agent in /tmp"
      fi
    }

    # start ssh-agent if not started, else link to it
    if ! ps ax 2>/dev/null | grep -q ssh-agent; then
      # make sure no dead ssh agent sockets remain
      rm -rf /tmp/ssh-*
      eval $(ssh-agent) > /dev/null
    else
      export SSH_AUTH_SOCK=~/.ssh-agent
      link_ssh_agent > /dev/null
    fi


# SSH and screen

The problem is screen won't get the ssh agent because it inherits the environment from when it started, so when using screen we set it to a static file in the home directory, and maintain a symlink to the current ssh agent using the `.ssh/rc` file executed at every connection.

Put in your `.bashrc`:

    # .ssh/rc maintains SSH agent symlink at ~/.ssh-agent, use it in screen.
    case "$TERM" in
      screen*) export SSH_AUTH_SOCK=~/.ssh-agent ;;
    esac

Put in your `.ssh/rc`:

    #!/bin/sh
    # Do not use bash, this file is executed by /bin/sh regardless of shebang.

    # Maintain ~/.ssh-agent symlink to the current SSH agent.
    if [ -e "$SSH_AUTH_SOCK" ]; then
      ln -snf "$SSH_AUTH_SOCK" ~/.ssh-agent
    fi

    # sshd(8) says if no ~/.ssh/rc, xauth is run; so we have to do it ourselves.
    if read proto cookie && [ -n "$DISPLAY" ]; then
      part1=$(echo "$DISPLAY" | cut -d: -f1)
      part2=$(echo "$DISPLAY" | cut -d: -f2)
      if [ "$part1" = "localhost" ]; then
        # sshd with X11UseLocalhost=yes
        xauth -q add "unix:$part2" "$proto" "$cookie"
      else
        # sshd with X11UseLocalhost=no
        xauth -q add "$DISPLAY" "$proto" "$cookie"
      fi
    fi

Then you can use ssh forwarding, use screen and your ssh agent always works.
Also, X11 forwarding still works.

By the way, instead of ssh and typing screen, I use a handy `co` function that automatically reattaches to the current screen session or creates a new one:

    co() {
      ssh -t "$@" 'screen -rx || screen'
    }

    co machine
    co machine -A # with SSH forwarding
