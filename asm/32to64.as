# as test.as -o test.o && ld -pic --oformat=binary test.o -o test
# as test.as -o test.o && ld --oformat=elf32-i386 test.o -o test

.intel_syntax
.globl _start
.section .text
_start:

.code32

push 0x33 # 64-bit USER_CS
call next
next:
addb [%esp], go64 - $
retf

.code64

go64:
mov %rax, 231 # sys_exit_group
mov %rdi, 42  # int status
syscall
