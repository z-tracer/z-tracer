/*
 * main.c
 *  run on monitord device, use for simple data for web server
 *  Created on: june 12, 2018
 *      Author: seazson
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>
#include <arpa/inet.h>
#include <sys/wait.h>
#include <signal.h>
#include "jsonrpc-c.h"
#include <fcntl.h>

#define PORT 1234  // the port users will be connecting to
#define PROCBUFLEN 8192
#define CMDBUFLEN 8192

static int debug=0;
#define DEBUG_PRINT(fmt, args...) \
	do { if(debug) \
	printf(fmt, ## args); \
	} while(0)

unsigned char procbuf[PROCBUFLEN];
unsigned char cmdbuf[CMDBUFLEN];
struct jrpc_server my_server;
unsigned char *endstring = "sometimewhenitrains"; 

void printJson(cJSON * root)
{
	int i=0;
    for(i=0; i<cJSON_GetArraySize(root); i++)
    {
        cJSON * item = cJSON_GetArrayItem(root, i);
        if(cJSON_Object == item->type)
            printJson(item);
        else                                
        {
            printf("%s->", item->string);
            printf("%s\n", cJSON_Print(item));
        }
    }
}

cJSON * checkconnect(jrpc_context * ctx, cJSON * params, cJSON *id) {
	return cJSON_CreateString("done!sometimewhenitrains");
}

cJSON * exit_server(jrpc_context * ctx, cJSON * params, cJSON *id) {
	jrpc_server_stop(&my_server);
	return cJSON_CreateString("Bye!");
}

cJSON * readfile(jrpc_context * ctx, cJSON * params, cJSON *id) {
	int fd;

	int len;
	cJSON * ph=NULL;

	//printf("%s\n",cJSON_Print(params));
	ph = cJSON_GetObjectItem(params,"path");
	if(ph != NULL)
	{
		char *path = ph->valuestring;
		fd = open(path,O_RDONLY);
		if(fd < 0)
		{
			DEBUG_PRINT("cann't open %s\n",path);
		}
		DEBUG_PRINT("read %s\n",path);
		memset(procbuf,0,PROCBUFLEN);
		len = read(fd,procbuf,PROCBUFLEN - strlen(endstring) - 1);
		close(fd);
		strcat(procbuf, endstring);
		return cJSON_CreateString(procbuf);
	}
	return NULL;
}

cJSON * runcmd(jrpc_context * ctx, cJSON * params, cJSON *id) {
	FILE *stream = NULL;
	int len;
	cJSON * ph=NULL;
	
	//printf("%s\n",cJSON_Print(params));
	ph = cJSON_GetObjectItem(params,"cmd");
	if(ph != NULL)
	{
		char *path = ph->valuestring;
		stream = popen(path,"r");
		if(stream == NULL )
		{
			DEBUG_PRINT("cann't run cmd %s\n",path);
		}
		DEBUG_PRINT("runcmd %s\n",path);
		memset(cmdbuf,0,CMDBUFLEN);
		len = fread( cmdbuf, sizeof(char), CMDBUFLEN - strlen(endstring) - 1, stream);
		pclose(stream);
		strcat(cmdbuf, endstring);
		return cJSON_CreateString(cmdbuf);
	}
	return NULL;
}

int main(int argc,char *argv[]) {
	if(argc > 1)
	{
		if(strncmp(argv[1],"debug",5) == 0)
			debug = 1;
	}
	jrpc_server_init(&my_server, PORT);
	jrpc_register_procedure(&my_server, checkconnect, "checkconnect", NULL );
	jrpc_register_procedure(&my_server, exit_server, "exit", NULL );
	jrpc_register_procedure(&my_server, readfile, "readfile", NULL );
	jrpc_register_procedure(&my_server, runcmd, "runcmd", NULL );
	jrpc_server_run(&my_server);
	jrpc_server_destroy(&my_server);
	return 0;
}
