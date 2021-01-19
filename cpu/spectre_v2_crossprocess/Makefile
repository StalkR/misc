CFLAGS += -Wall -O0 -masm=intel
CC = gcc

all: attacker victim

attacker: attacker.c
	$(CC) $(CFLAGS) -o attacker attacker.c

victim: victim.c
	$(CC) $(CFLAGS) -o victim victim.c

clean:
	rm -f attacker victim
