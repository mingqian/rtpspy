/*
 * Copyright (c) 2015 Rafael Han
 * Author: Rafael Han
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy of
 * this software and associated documentation files (the "Software"), to deal in
 * the Software without restriction, including without limitation the rights to
 * use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
 * the Software, and to permit persons to whom the Software is furnished to do so,
 * subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
 * FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
 * COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
 * IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
 * CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 */

#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/un.h> // for sockaddr_un
#include "util.h"

static int comm_sock = -1;
static struct sockaddr_un comm_addr;

/* *****************************************************************************/
/**
 * @brief  setup unix domain socket for communicating with parent thread
 *
 * @param  sockpath
 * @param  addr
 *
 * @return  sock or -1 when failure
 */
/* *****************************************************************************/
int set_sock(const char *sockpath)
{
	int sock;
	struct sockaddr_un *addr = &comm_addr;
	int flags;

	if (comm_sock < 0)
	{
		if (!sockpath)
		{
			return -1;
		}
		printf("sockpath: %s\n", sockpath);

		sock = socket(AF_UNIX, SOCK_DGRAM, 0);
		if (sock < 0)
		{
			perror("sock failed:");
			return -1;
		}

		if ((flags = fcntl(sock, F_GETFL, 0)) < 0)
		{
			perror("sock getflag: ");
			return -1;
		}

		if (fcntl(sock, F_SETFL, flags | O_NONBLOCK) < 0)
		{
			perror("sock setflag: ");
			return -1;
		}
		comm_sock = sock;

		memset(addr, 0, sizeof(*addr));
		addr->sun_family = AF_UNIX;
		strncpy(addr->sun_path, sockpath, sizeof(addr->sun_path));

	}

	return comm_sock;
}

void send_sock(void *buf, int buf_len)
{
	if (comm_sock < 0)
		return;

    if (sendto(comm_sock, (const char *)buf, buf_len, 0, (const struct sockaddr *)&comm_addr, sizeof(comm_addr)) < 0) 
    {
        perror("sendto: ");
    }
}
