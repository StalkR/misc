; nasm -f bin -o test test.asm
; nasm -f elf64 -o test.o test.asm && ld --oformat=elf32-i386 test.o -o test

GLOBAL _start
SECTION .text
_start:

BITS 32

push 0x33 ; 64-bit USER_CS
call next
next:
add dword [esp], go64 - $
retf

BITS 64

go64:
mov rax, 231 ; sys_exit_group
mov rdi, 42  ; int status
syscall
