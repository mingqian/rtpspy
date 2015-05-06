#ifndef __UTIL_H__
#define __UTIL_H__


int set_sock(const char *sockpath);
void send_sock(void *buf, int buf_len);

#endif
