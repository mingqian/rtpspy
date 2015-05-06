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
