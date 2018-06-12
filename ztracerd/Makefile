##for x86
CC=gcc

##for arm
#CC=arm-linux-gcc
#HOST=--host=arm-linux


SRCS = jsonrpc-c.c main.c cJSON.c
OBJS = $(SRCS:%.c=%.o)

all: lib $(OBJS)
	$(CC) $(OBJS) -o ztracerd -L./ -lev -lm 
	#$(CC) -L./ -lev -lm -I./libev $(OBJS) -o ztracerd
	
%.o: %.c
	$(CC) -I./libev -c $< -o $@
	
lib:
	cd libev ;\
	./configure $(HOST) CC=$(CC);\
	make;\
	cp .libs/libev.so* ../

clean:
	rm -f *.o
	rm -f libev.so*
	rm -f ztracerd
	cd libev && make distclean
