/*
 * Copyright (C) 2015  Rafael Han
 * Author: Rafael Han
 * 
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#include <stdio.h>
#include <stdint.h>
#include <assert.h>
#include <sys/time.h>
#include <ortp/ortp.h>
#include "h264det.h"
#include "util.h"

enum {
	FU_NAL_MIDDLE_SLICE = 0,	
	SINGLE_NAL_SLICE = 1,
	FU_NAL_START_SLICE,
	FU_NAL_END_SLICE
};

static uint32_t get_ue(unsigned char *payload, unsigned int payload_size, int *bitcount) 
{
	// count leading zero bits
	int zero_bits_count = 0;
	int bit_count = *bitcount;
	int i;
	int remain = 0;

	while (bit_count < payload_size * 8)
	{
		if (payload[bit_count / 8] & (0x80 >> (bit_count % 8)))
		{
			break;
		}
		bit_count ++;
		zero_bits_count ++;
	}

	bit_count ++; // skip this '1'

	// calculate value
	for (i = 0; i < zero_bits_count; i ++)
	{
		remain = remain << 1;
		if (payload[bit_count / 8] & (0x80 >> (bit_count % 8)))
		{
			remain += 1;
		}
		bit_count ++;
	}

	*bitcount = bit_count;
	return ((1 << zero_bits_count) -1 + remain);
}

static void slice_check(unsigned char *payload, unsigned int payload_size, int slice_flag, uint16_t seqdiff, uint32_t ts)
{
	uint8_t first_mb_in_slice;
	uint32_t slice_type;
	int bitcount = 0;
    h264_slice_t slice;
	static h264_slice_t last_fu_slice; // last FU start slice
	static int have_last_fu_slice = FALSE;

	if (SINGLE_NAL_SLICE == slice_flag || FU_NAL_START_SLICE == slice_flag)
	{
		// Exp-Golomb code
		// first_mb_in_slice: ue(v)
		// slice_type: ue(v)
		first_mb_in_slice = get_ue(payload, payload_size, &bitcount);
		slice_type = get_ue(payload, payload_size, &bitcount);
		
		if (0 == slice_type || 5 == slice_type)
		{
			/*printf("P %d\n", payload_size);*/
			slice.type = SLICE_P;
		}
		else if (2 == slice_type || 7 == slice_type)
		{
			/*printf("I %d\n", payload_size);*/
			slice.type = SLICE_I;
		}
		else
		{
			/*printf("Unknown %d\n", payload_size);*/
			slice.type = SLICE_UNKNOWN;
		}
		slice.family = SLICE_FAMILY_H264;
		slice.size = payload_size;
		slice.seqdiff = seqdiff;
		slice.ts = ts;
		if (SINGLE_NAL_SLICE == slice_flag)
		{
			have_last_fu_slice = FALSE;
			send_sock(&slice, sizeof(slice));
		}
		else if (FU_NAL_START_SLICE == slice_flag)
		{
			last_fu_slice = slice;
			have_last_fu_slice = TRUE; // do not send, wait for following FU
		}
	}
	else if (FU_NAL_END_SLICE == slice_flag)
	{
		if (have_last_fu_slice) // most likely
		{
			if (ts == last_fu_slice.ts)
			{
				last_fu_slice.size += payload_size;
				last_fu_slice.seqdiff += seqdiff;
				send_sock(&last_fu_slice, sizeof(last_fu_slice)); // send last FU stat
				have_last_fu_slice = FALSE; // MUST!
			}
			else // there is packet loss
			{
				last_fu_slice.seqdiff += 1; // regard it as missing 1 FU end packet for last FU
				send_sock(&last_fu_slice, sizeof(last_fu_slice)); // send last FU packet stat
				have_last_fu_slice = FALSE; // MUST!

				slice.family = SLICE_FAMILY_H264;
				slice.type = SLICE_UNKNOWN;
				slice.size = payload_size;
				slice.seqdiff = seqdiff;
				slice.ts = ts;
				send_sock(&slice, sizeof(slice)); // this one
			}
		}
		else // no last fu slice, there is packet loss
		{
			slice.family = SLICE_FAMILY_H264;
			slice.type = SLICE_UNKNOWN;
			slice.size = payload_size;
			slice.seqdiff = seqdiff; // seqdiff should reflect acutal seqnum missing
			slice.ts = ts;
			send_sock(&slice, sizeof(slice)); // this one
		}
	}
	else if (FU_NAL_MIDDLE_SLICE == slice_flag)
	{	
		if (have_last_fu_slice) // most likely
		{
			if (ts == last_fu_slice.ts)
			{
				last_fu_slice.size += payload_size;
				last_fu_slice.seqdiff += seqdiff; // calculates total seqnum missing
				// do not send, wait for FU end
			}
			else // there is packet loss
			{
				last_fu_slice.seqdiff += 1; // regard it as missing 1 FU end packet for last FU
				send_sock(&last_fu_slice, sizeof(last_fu_slice)); // send last FU packet stat
				have_last_fu_slice = FALSE; // MUST!

				slice.family = SLICE_FAMILY_H264;
				slice.type = SLICE_UNKNOWN;
				slice.size = payload_size;
				slice.seqdiff = seqdiff; // seqdiff should reflect actual seqnum missing
				slice.ts = ts;
				send_sock(&slice, sizeof(slice)); // this one
			}
		}
		else // no last fu slice, there is packet loss
		{
			slice.family = SLICE_FAMILY_H264;
			slice.type = SLICE_UNKNOWN;
			slice.size = payload_size;
			slice.seqdiff = seqdiff;
			slice.ts = ts;
			send_sock(&slice, sizeof(slice)); // this one
		}
	}
}

void h264_payload_check(unsigned char *payload, unsigned int payload_size, int is_fu, uint16_t seqdiff, uint32_t ts)
{
	uint8_t fu_start, fu_end, nal_type, slice_flag;
	if (is_fu)
	{
		fu_start = payload[0] & 0x80;
		fu_end = payload[0] & 0x60;
	}
	nal_type = payload[0] & 0x1f;

	if (!is_fu)
	{
		slice_flag = SINGLE_NAL_SLICE;
	}
	else if (is_fu && fu_start)
	{
		slice_flag = FU_NAL_START_SLICE;
	}
	else if (is_fu && fu_end)
	{
		slice_flag = FU_NAL_END_SLICE;
	}
	else if (is_fu && !fu_start && !fu_end)
	{
		slice_flag = FU_NAL_MIDDLE_SLICE;
	}
	
	/*there are 3 cases to consider:*/
	/*1. non-FU packet: (NAL header, slice header, ...)*/
	/*2. FU packet start: (FU header, FU indicator, slice header, ...)*/
	/*3. FU packet non-start: (FU header, FU indicator, ...)*/
	switch (nal_type)
	{
		case 1:
			/*non-IDR*/
			slice_check(&payload[1], payload_size-1, slice_flag, seqdiff, ts);
			break;
		case 5:
			/*IDR*/
			slice_check(&payload[1], payload_size-1, slice_flag, seqdiff, ts);
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
			h264_payload_check(&payload[1], payload_size-1, TRUE, seqdiff, ts);
			break;
		default:
			printf("unknown nal_type: %d\n", nal_type);
			break;
	}
}
