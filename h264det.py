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

'RtpSpy: RFC3984 Detector module'

import logging
from scapy.all import Packet, Raw

LOGFILE = 'rtpspy.log'
logger = logging.getLogger(LOGFILE)

def slice_parse(slice_hdr, is_idr, is_slice_hdr, length, slice_seq):
    'Parse by H264 std'
    if is_slice_hdr:
        pslice = slice_hdr[0] & 0x60
        islice = slice_hdr[0] & 0x70
        if pslice == 0x60:
            if is_idr:
                logger.critical('Wrong: P Slice but IDR!')
            sli = ('P', length)
        elif islice == 0x30:
            sli = ('I', length)
        else:
            logger.error('Unknown slice')
    else:
        # from FU-A/FU-B
        sli = (slice_seq[-1][0], length)
    slice_seq.append(sli)


def nal_parse(nal_hdr, is_fu, length, slice_seq):
    'Parse NAL by RFC3984'
    if is_fu:
        fu_start = nal_hdr[0] & 0x80
        fu_end = nal_hdr[0] & 0x60
    nal_type = nal_hdr[0] & 0x1f
    has_slice_hdr = (not is_fu) or (is_fu and fu_start)
    if nal_type == 1:
        #non-IDR slice
        slice_parse(nal_hdr[1:], is_idr=False, is_slice_hdr=has_slice_hdr, length=length, slice_seq=slice_seq)
    elif nal_type == 5:
        #IDR slice
        slice_parse(nal_hdr[1:], is_idr=True, is_slice_hdr=has_slice_hdr, length=length, slice_seq=slice_seq)
    elif nal_type == 7:
        #SPS
        pass
    elif nal_type == 8:
        #PPS
        pass
    elif nal_type == 28 or nal_type == 29:
        #FU-A/FU-B
        nal_parse(nal_hdr[1:], is_fu=True, length=length, slice_seq=slice_seq)
    else:
        logger.error('nal_type %d' % nal_type)

def udp_det(pkt, slice_seq):
    'Rtp over UDP detector'
    load = pkt[Raw].load
    try:
        nal_hdr = (ord(load[0]), ord(load[1]), ord(load[2]))
    except (ValueError, IndexError), err:
        logger.error('nal_hdr: %s', str(err))
    nal_parse(nal_hdr, is_fu=False, length=len(load), slice_seq=slice_seq)
