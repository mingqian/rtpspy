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

#ifndef _H264DET_H_
#define _H264DET_H_

#include "slice.h"

enum _h264_slice_type {
	SLICE_UNKNOWN = 0,
	SLICE_I,
	SLICE_P
};

typedef struct _h264_slice_t {
	enum slice_family 		family;	
	enum _h264_slice_type 	type;
	unsigned int 			size;
    uint16_t                seqdiff;
    uint32_t                ts;
} h264_slice_t;

void h264_payload_check(unsigned char *payload, unsigned int payload_size, int is_fu, uint16_t seqdiff, uint32_t ts);

#endif
