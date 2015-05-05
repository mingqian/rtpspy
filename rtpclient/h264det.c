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
#include <stdint.h>
#include <assert.h>
#include <sys/time.h>
#include <ortp/ortp.h>
#include "h264det.h"


enum _slice_type {
	SLICE_UNKNOWN = 0,
	SLICE_I,
	SLICE_P
};

typedef struct _slice_t {
	enum _slice_type 	type;
	unsigned int 		size;
} slice_t;

#define MAX_SLICES          (70 * 3) // enough to hold 60fps for 3 secs
static slice_t slices[MAX_SLICES];
static unsigned int slice_count;

static void slice_check(unsigned char *payload, unsigned int payload_size, int have_slice_hdr)
{
	uint8_t p_slice, i_slice;
    slice_t *slice;
	static int slice_count = 0;
	static struct timeval start_tv = {0, 0};
	struct timeval current_tv;
	gettimeofday(&current_tv, NULL);
    if (0 == start_tv.tv_sec && 0 == start_tv.tv_usec)
    {
        start_tv = current_tv;
    }

	if (have_slice_hdr)
	{
		slice = &slices[slice_count++];
        assert(slice);
		p_slice = payload[0] & 0x60;
		i_slice = payload[0] & 0x70;
		if (0x60 == p_slice)
		{
			printf("P %d\n", payload_size);
			slice->type = SLICE_P;
		}
		else if (0x30 == i_slice)
		{
			printf("I %d\n", payload_size);
			slice->type = SLICE_I;
		}
		else
		{
			printf("Unknown slice type %d\n", payload[0]);
			slice->type = SLICE_UNKNOWN;
		}
		slice->size = payload_size;
	}
	else 
	/*FU non-start*/
	{	

	}

    // reset every 3 secs
    if ((current_tv.tv_sec - start_tv.tv_sec) * 1000 * 1000 + \
            (current_tv.tv_usec - start_tv.tv_usec) >= 3 * 1000 * 1000)
    {
        start_tv = current_tv;
        printf("FPS: %.2f\n", slice_count / 3.00);
        slice_count = 0;
    }
}

void h264_payload_check(unsigned char *payload, unsigned int payload_size, int is_fu)
{
	uint8_t fu_start, fu_end, nal_type, have_slice_hdr;
	if (is_fu)
	{
		fu_start = payload[0] & 0x80;
		fu_end = payload[0] & 0x60;
	}
	nal_type = payload[0] & 0x1f;
	have_slice_hdr = (!is_fu) || (is_fu && fu_start);
	
	/*there are 3 cases to consider:*/
	/*1. non-FU packet: (NAL header, slice header, ...)*/
	/*2. FU packet start: (FU header, FU indicator, slice header, ...)*/
	/*3. FU packet non-start: (FU header, FU indicator, ...)*/
	switch (nal_type)
	{
		case 1:
			/*non-IDR*/
			slice_check(&payload[1], payload_size-1, have_slice_hdr);
			break;
		case 5:
			/*IDR*/
			slice_check(&payload[1], payload_size-1, have_slice_hdr);
			break;
		case 6:
			/*SEI*/
			break;
		case 7:
			/*SPS*/
			break;
		case 8:
			/*PPS*/
			break;
		case 28:
			/*FU-A*/
		case 29:
			/*FU-B*/
			h264_payload_check(&payload[1], payload_size-1, TRUE);
			break;
		default:
			printf("unknown nal_type: %d\n", nal_type);
			break;
	}
}
