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

char *perfbuf=NULL;
char *p_cmdbuf=NULL;
static int debug=0;
#define DEBUG_PRINT(fmt, args...) \
	do { if(debug) \
	printf(fmt, ## args); \
	} while(0)

unsigned char procbuf[PROCBUFLEN];
unsigned char cmdbuf[CMDBUFLEN];
struct jrpc_server my_server;
unsigned char *endstring = "sometimewhenitrains"; 
unsigned char *okendstring = "oksometimewhenitrains"; 
unsigned char *errendstring = "errsometimewhenitrains"; 
unsigned char *doneendstring = "donesometimewhenitrains"; 
unsigned char *waitendstring = "waitsometimewhenitrains"; 

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
	int buffersize = PROCBUFLEN + 8192;
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
			return cJSON_CreateString(endstring);
		}
		memset(procbuf,0,PROCBUFLEN);
		len = read(fd,procbuf,PROCBUFLEN);
		DEBUG_PRINT("read %s len = %d\n",path,len);
		if(len >= PROCBUFLEN - strlen(endstring) - 1)
		{
			printf("proc file is bigger than %d,use malloc inside\n",PROCBUFLEN);
			if(p_cmdbuf != NULL)
				free(p_cmdbuf);
			
			p_cmdbuf = malloc(buffersize);
			if(p_cmdbuf != NULL)
			{
				memset(p_cmdbuf,0,buffersize);
				memcpy(p_cmdbuf,procbuf,len);
				if(len == PROCBUFLEN)
				{
					while(1)
					{
						len = read(fd, p_cmdbuf+buffersize-PROCBUFLEN, 8192);
						printf("read len %d buffersize %d\n",len,buffersize);
						if(len <= 8192 - strlen(endstring) - 1)
							break;
						buffersize +=8192;
						p_cmdbuf = realloc(p_cmdbuf,buffersize);
						memset(p_cmdbuf+buffersize-8192,0,8192);
						if(p_cmdbuf == NULL)
						{
							printf("remalloc fail\n");
							break;
						}
					}
				}
				close(fd);
				strcat(p_cmdbuf, endstring);
				return cJSON_CreateString(p_cmdbuf);
			}
		}
		else
		{
			close(fd);
			strcat(procbuf, endstring);
			return cJSON_CreateString(procbuf);
		}
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
			cJSON_CreateString(endstring);
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

cJSON * perfscript(jrpc_context * ctx, cJSON * params, cJSON *id) {
	FILE *stream = NULL;
	int len;
	cJSON * ph=NULL;
	char *buf = NULL;
	int buffersize = 8192;
	
	ph = cJSON_GetObjectItem(params,"cmd");
	if(ph != NULL)
	{
		char *cmd = ph->valuestring;
		DEBUG_PRINT("run perf %s\n",cmd);
		system(cmd);

		stream = popen("perf script --header","r");
		if(stream == NULL )
		{
			DEBUG_PRINT("cann't run cmd perf script\n");
			return NULL;
		}
		
		if(perfbuf != NULL)
			free(perfbuf);
		
		perfbuf = malloc(buffersize);
		if(perfbuf != NULL)
		{
			memset(perfbuf,0,8192);
			while(1)
			{
				len = fread(perfbuf+buffersize-8192, sizeof(char), 8192, stream);
				DEBUG_PRINT("read len %d buffersize %d\n",len,buffersize);
				if(len <= 8192 - strlen(endstring) - 1)
					break;
				buffersize +=8192;
				perfbuf = realloc(perfbuf,buffersize);
				memset(perfbuf+buffersize-8192,0,8192);
				if(perfbuf == NULL)
				{
					printf("remalloc fail\n");
					break;
				}
			}
			pclose(stream);
			strcat(perfbuf, endstring);
			return cJSON_CreateString(perfbuf);
		}
	}
	return NULL;
}

int perfpid = 0;
int perfrunning = 0;
cJSON * perfastart(jrpc_context * ctx, cJSON * params, cJSON *id) {
	FILE *stream = NULL;
	int len;
	cJSON * ph=NULL;
	char *buf = NULL;
	int buffersize = 8192;
	char *p;
	char *argv[128];
	int i = 0;
	int j = 0;
	
	ph = cJSON_GetObjectItem(params,"cmd");
	if(ph != NULL)
	{
		if(perfpid == 0)
		{
			char *cmd = ph->valuestring;
			perfpid = fork();
			if(perfpid == 0)
			{
				p = strtok (cmd," "); 
				while(p!=NULL) { 
					DEBUG_PRINT (":%s\n",p); 
					argv[i] = p;
					i++;
					p = strtok(NULL," "); 
				}
				argv[i++] = "--filter"; 
				sprintf(argv[i++], "common_pid!=%d", getpid()); 
				argv[i] = '\0';
				DEBUG_PRINT("child run cmd %s\n",cmd);
				execvp(argv[0], argv);
				printf("error never got here\n");
				exit(0);
			}
			else
			{
				DEBUG_PRINT("childpid %d\n",perfpid);
				perfrunning = 1;
			}
			return cJSON_CreateString(okendstring);
		}
	}
	return cJSON_CreateString(errendstring);
}

cJSON * acmdstart(jrpc_context * ctx, cJSON * params, cJSON *id) {
	FILE *stream = NULL;
	int len;
	cJSON * ph=NULL;
	char *buf = NULL;
	int buffersize = 8192;
	char *p;
	char *argv[128];
	int i = 0;
	
	ph = cJSON_GetObjectItem(params,"cmd");
	if(ph != NULL)
	{
		if(perfpid == 0)
		{
			char *cmd = ph->valuestring;
			perfpid = fork();
			if(perfpid == 0)
			{
				p = strtok (cmd," "); 
				while(p!=NULL) { 
					DEBUG_PRINT (":%s\n",p); 
					argv[i] = p;
					i++;
					p = strtok(NULL," "); 
				} 
				argv[i] = '\0';
				DEBUG_PRINT("child run cmd %s\n",cmd);
				execvp(argv[0], argv);
				printf("error never got here\n");
				exit(0);
			}
			else
			{
				DEBUG_PRINT("childpid %d\n",perfpid);
				perfrunning = 1;
			}
			return cJSON_CreateString(okendstring);
		}
	}
	return cJSON_CreateString(errendstring);
}

cJSON * acmdstop(jrpc_context * ctx, cJSON * params, cJSON *id) {
	FILE *stream = NULL;
	int len;
	cJSON * ph=NULL;
	char *buf = NULL;
	int buffersize = 8192;
	int status;
	int ret;

	if(perfpid != 0)
	{
		kill(perfpid,SIGINT);
	}
	return cJSON_CreateString(okendstring);
}


cJSON * acmdcheckdone(jrpc_context * ctx, cJSON * params, cJSON *id) {
	FILE *stream = NULL;
	int len;
	cJSON * ph=NULL;
	char *buf = NULL;
	int buffersize = 8192;
	int status;
	int ret;

	if(perfpid != 0)
	{
		ret = waitpid(perfpid,&status,WNOHANG);
		if(ret == 0)
			return cJSON_CreateString(waitendstring);
		else
		{
			perfpid = 0;
			perfrunning = 0;
			return cJSON_CreateString(doneendstring);
		}
	}
	return cJSON_CreateString(doneendstring);
}

cJSON * acmdwait(jrpc_context * ctx, cJSON * params, cJSON *id) {
	FILE *stream = NULL;
	int len;
	cJSON * ph=NULL;
	char *buf = NULL;
	int buffersize = 8192;
	int status;
	int ret;

	if(perfpid != 0)
	{
		while(1)
		{
			ret = waitpid(perfpid,&status,WNOHANG);
			sleep(1);
			if(ret == 0)
				printf("wait\n");
			else
			{
				perfpid = 0;
				perfrunning = 0;
				break;
			}
		}
	}
	return cJSON_CreateString(doneendstring);
}

cJSON * acmdresult(jrpc_context * ctx, cJSON * params, cJSON *id) {
	FILE *stream = NULL;
	int len;
	cJSON * ph=NULL;
	char *buf = NULL;
	int buffersize = 8192;
	
	ph = cJSON_GetObjectItem(params,"cmd");
	if(ph != NULL)
	{
		char *cmd = ph->valuestring;
		DEBUG_PRINT("run result cmd %s\n",cmd);

		stream = popen(cmd,"r");
		if(stream == NULL )
		{
			DEBUG_PRINT("cann't run result cmd\n");
			return cJSON_CreateString(endstring);
		}
		
		if(perfbuf != NULL)
			free(perfbuf);
		
		perfbuf = malloc(buffersize);
		if(perfbuf != NULL)
		{
			memset(perfbuf,0,8192);
			while(1)
			{
				len = fread(perfbuf+buffersize-8192, sizeof(char), 8192, stream);
				DEBUG_PRINT("read len %d buffersize %d\n",len,buffersize);
				if(len <= 8192 - strlen(endstring) - 1)
					break;
				buffersize +=8192;
				perfbuf = realloc(perfbuf,buffersize);
				memset(perfbuf+buffersize-8192,0,8192);
				if(perfbuf == NULL)
				{
					printf("remalloc fail\n");
					break;
				}
			}
			pclose(stream);
			strcat(perfbuf, endstring);
			return cJSON_CreateString(perfbuf);
		}
	}
	return NULL;
}

int get_ftrace_buffer_size(void)
{
	int fd;
	int len=0;
	char buf[128];
	int bufferkb=0;
	fd = open("/sys/kernel/debug/tracing/buffer_total_size_kb",O_RDONLY);
	if(fd < 0 )
	{
		DEBUG_PRINT("cann't run seqread\n");
		return 0;
	}
	
	memset(buf,0,128);
	len = read(fd, buf, 128);
	if(len > 0)
		bufferkb = atoi(buf);
	printf("ftrace buffer size=%dkB\n",bufferkb);
	return bufferkb;
}

cJSON * seqread(jrpc_context * ctx, cJSON * params, cJSON *id) {
	int fd;
	int len = 0;
	int totallen = 0;
	int pos = 0;
	cJSON * ph=NULL;
	char *buf = NULL;
	int mallocstep = (get_ftrace_buffer_size()+1)*1024;
	int buffersize = mallocstep;
	
	ph = cJSON_GetObjectItem(params,"path");
	if(ph != NULL)
	{
		char *path = ph->valuestring;
		DEBUG_PRINT("seqread %s\n",path);

		fd = open(path,O_RDONLY);
		if(fd < 0 )
		{
			DEBUG_PRINT("cann't run seqread\n");
			return cJSON_CreateString(endstring);
		}
		
		if(perfbuf != NULL)
			free(perfbuf);
		
		perfbuf = malloc(buffersize);
		if(perfbuf != NULL)
		{
			memset(perfbuf,0,buffersize);
			while(1)
			{
				len = read(fd, perfbuf+buffersize-mallocstep + pos, mallocstep - pos);
				totallen += len;
				printf("read len %d buffersize %d,total len %d\n",len,buffersize,totallen);
				if(len == 0)
					break;
				pos += len;
				if(pos == mallocstep)
				{
					buffersize +=mallocstep;
					pos = 0;
					perfbuf = realloc(perfbuf,buffersize);
					memset(perfbuf+buffersize-mallocstep,0,mallocstep);
					if(perfbuf == NULL)
					{
						printf("remalloc fail\n");
						break;
					}					
				}
			}
			if(pos > mallocstep - strlen(endstring) - 1)
			{
				printf("malloc more space for endstring\n");
				buffersize += mallocstep;
				perfbuf = realloc(perfbuf,buffersize);
				memset(perfbuf+buffersize-mallocstep,0,mallocstep);
			}
			close(fd);
			strcat(perfbuf, endstring);
			return cJSON_CreateString(perfbuf);
		}
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

	jrpc_register_procedure(&my_server, acmdstart, "acmdstart", NULL );
	jrpc_register_procedure(&my_server, acmdstop, "acmdstop", NULL );
	jrpc_register_procedure(&my_server, acmdcheckdone, "acmdcheckdone", NULL );
	jrpc_register_procedure(&my_server, acmdwait, "acmdwait", NULL );
	jrpc_register_procedure(&my_server, acmdresult, "acmdresult", NULL );
	jrpc_register_procedure(&my_server, seqread, "seqread", NULL );

	jrpc_register_procedure(&my_server, perfastart, "perfastart", NULL );
	jrpc_register_procedure(&my_server, perfscript, "perfscript", NULL );

	jrpc_server_run(&my_server);
	jrpc_server_destroy(&my_server);
	return 0;
}
