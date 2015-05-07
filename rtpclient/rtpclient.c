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
#include <stdlib.h>
#include <signal.h>
#include <assert.h>
#include <time.h>
#include <ortp/ortp.h>
#include "rtpdet.h"
#include "slice.h"

static int cond = 1;

static void stop_handler(int signum)
{
    printf("%s\n", __FUNCTION__);
	cond = 0;
}

static void ssrc_cb(RtpSession *session)
{
	printf("ssrc changed!\n");
}

/* *****************************************************************************/
/**
 * @brief  RTP seqence number continuity check
 *
 * @param  seqnum
 *
 * @return missing seqence number count
 */
/* *****************************************************************************/
static uint16_t rtp_continuity_check(uint16_t seqnum)
{
	static uint16_t last_seqnum = 0;
	uint16_t diff;

	if (0 == last_seqnum)
	{
		diff = 0;
	}
	else
	{
		diff = seqnum - last_seqnum - 1;	
	}
	last_seqnum = seqnum;

	if (diff != 0)
	{
		printf("Seqnum discontinue at %d, diff: %d\n", seqnum, diff);
	}
	return diff;
}

/* *****************************************************************************/
/**
 * @brief  rtp receive routine
 *
 * @param  port: RTP port
 * @param  payload_num: Payload number
 * @param  paylode_type: Payload type string
 * @param  sockpath: unix domain sockpath for communicating with parent thread
 *
 * @return
 */
/* *****************************************************************************/
int rtp_recv(unsigned int port, unsigned int payload_num, char *payload_type, const char *sockpath)
{
	RtpSession *session;
	RtpProfile *profile;
	mblk_t *mp;
	uint32_t ts = 0;
	uint16_t seqnum, seqdiff;
	uint32_t timestamp;
	unsigned char *payload;
	int payload_size;
    struct timespec wait_time = {0, 1000*1000}; // 1ms

	printf("Payload: %d -> %s\n", payload_num, payload_type);

    if (set_sock(sockpath) < 0)
    {
        return -1;
    }
	
	ortp_init();
	ortp_scheduler_init();
    /*ortp_set_log_level_mask(ORTP_DEBUG|ORTP_MESSAGE|ORTP_WARNING|ORTP_ERROR);*/
    ortp_set_log_level_mask(ORTP_WARNING|ORTP_ERROR);
	signal(SIGINT, stop_handler);
	session = rtp_session_new(RTP_SESSION_RECVONLY);
	rtp_session_set_scheduling_mode(session, FALSE);
	rtp_session_set_blocking_mode(session, FALSE);

	rtp_session_set_local_addr(session, "0.0.0.0", port, port+1);
    rtp_session_set_connected_mode(session, TRUE);
    rtp_session_set_symmetric_rtp(session, FALSE);
	/*avoid ortp from changing original RTP timestamp*/
    rtp_session_set_jitter_compensation(session, 0);
    rtp_session_enable_jitter_buffer(session, FALSE);
    rtp_session_enable_adaptive_jitter_compensation(session, FALSE);
	/*set correct payload type*/
	profile = rtp_session_get_recv_profile(session);
	rtp_profile_set_payload(profile, payload_num, &payload_type_h264);
	rtp_session_set_payload_type(session, payload_num);

	rtp_session_signal_connect(session, "ssrc_changed", (RtpCallback)ssrc_cb, 0);
	rtp_session_signal_connect(session, "ssrc_changed", (RtpCallback)rtp_session_reset, 0);

    int ret;
	while (cond)
	{
        mp=rtp_session_recvm_with_ts(session, ts);
        if (mp > 0)
        {
            seqnum = rtp_get_seqnumber(mp);
            timestamp = rtp_get_timestamp(mp);
            seqdiff = rtp_continuity_check(seqnum);
            payload_size = rtp_get_payload(mp, &payload);
            //printf("seq: %d\tmark: %d\tts: %d\t", \
                //seqnum, rtp_get_markbit(mp), timestamp);
            //printf("size: %d bytes\n", payload_size);
            if (payload_size > 3)
            {
                h264_payload_check(payload, payload_size, FALSE, seqdiff, timestamp);
            }
        }
        freemsg(mp);
        ts += 3600;
        nanosleep(&wait_time, NULL);
            
	}

	rtp_session_destroy(session);
	ortp_exit();

	return 0;
}
