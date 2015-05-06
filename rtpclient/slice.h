#ifndef __SLICE_H__
#define __SLICE_H__

enum slice_family {
	SLICE_FAMILY_H264,
};

typedef struct _slice_t {
	enum slice_family 		family;
	char 					*info;	
}slice_t;

#endif
