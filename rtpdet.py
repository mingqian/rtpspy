# Copyright (C) 2015  Rafael Han
# Author: Rafael Han
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


#!/usr/bin/env python

'RtpSpy: RTP Detector module'

import logging
from scapy.all import Packet, UDP, RTP
import rtspclient
import h264det

LOGFILE = 'rtpspy.log'
logger = logging.getLogger(LOGFILE)

#Specific payload detector
PAYLOAD_DET = {'H264/90000': h264det.udp_det, \
        }

class RtpDet(object):
    'Rtp detector object'
    def __init__(self, media):
        self.det = None
        self.payload_num = None
        self.lastseq = None
        self.lasttimestamp = None
        self.slice_seq = []
        if isinstance(media, rtspclient.MediaSession) != True:
            return None
        if PAYLOAD_DET.has_key(media.payload_type):
            self.det = PAYLOAD_DET[media.payload_type]
            self.payload_num = media.payload_num


    def parse(self, pkt):
        'parse possible RTP packet'
        try:
            pkt[UDP].decode_payload_as(RTP)
        except (IndexError, ValueError, AttributeError), err:
            logger.error('Cannot decode as RTP: %s' % str(err))

        pkt = pkt[RTP]
        if self.check(pkt):
            self.seq_check(pkt)
            if self.det:
                self.det(pkt, self.slice_seq)

    def check(self, pkt):
        'RTP layer sanity check'
        ret_val = True
        if pkt.version != 2:
            ret_val = False
        elif int(pkt.getfieldval('payload')) != self.payload_num:
            ret_val = False
        return ret_val

    def seq_check(self, pkt):
        'RTP layer sequence continuity check'
        seq = pkt.sequence
        timestamp = pkt.timestamp
        if self.lastseq != None and seq != self.lastseq + 1:
            logger.error('!!! Sequence discontinued: %d (T: %d) -> %d (T: %s), ' \
                    % (self.lastseq, self.lasttimestamp, seq, timestamp))
        self.lastseq = seq
        self.lasttimestamp = timestamp

    def get_slice_seq(self):
       return self.slice_seq
