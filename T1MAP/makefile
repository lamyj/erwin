CC=gcc
CFLAGS=-W -Wall
LDFLAGS=-lm
EXEC=SPGR_EPG

all: $(EXEC)

SPGR: SPGR_EPG.o 
	$(CC) -o $@ SPGR_EPG.o $(LDFLAGS)

SPGR_EPG.o: SPGR_EPG.c
	$(CC) -o $@ -c $< $(CFLAGS)

clean:
	rm -rf *.o

mrproper: clean
	rm -rf $(EXEC)
