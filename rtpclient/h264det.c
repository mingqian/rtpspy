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


static void slice_check(unsigned char *payload, unsigned int payload_size, int have_slice_hdr)
{
	uint8_t p_slice, i_slice;
	slice_t *slice = NULL;
	static int slice_count = 0;
	static struct timeval start_tv;
	struct timeval current_tv;
	start_tv.tv_sec = 0;
	start_tv.tv_usec = 0;
	gettimeofday(&current_tv, NULL);


	if (have_slice_hdr)
	{
		slice = malloc(sizeof(slice_t));
		slice_count ++;
		assert(slice);
		p_slice = payload[0] & 0x60;
		i_slice = payload[0] & 0x70;
		if (0x60 == p_slice)
		{
			printf("P\n");
			slice->type = SLICE_P;
		}
		else if (0x30 == i_slice)
		{
			printf("I\n");
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
