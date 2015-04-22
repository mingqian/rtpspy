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
#from matplotlib import pyplot as plt

LOGFILE = 'rtpspy.log'
logger = logging.getLogger(LOGFILE)


def slice_parse(hdr, length, continuity, slices, **kargs):
    'Parse by H264 slices'
    #Todo: add jitter analysis
    #hdr: (slice header, slice data) when not FU-A/FU-B
    #     (slice header) when FU-A/FU-B start
    #     (slice data) when FU-A/FU-B non-start
    #lendgh: RTP load length
    #continuity: (seq, RTP sequence diff, RTP timestamp diff)
    #slices: slice list to store parse result
    #        [frame type, frame length, start seq, frame discontinuity, in-FU discontinuity]
    is_idr = False
    is_slice_hdr = False
    if kargs.has_key('is_idr'):
        is_idr = kargs['is_idr']
    if kargs.has_key('is_slice_hdr'):
        is_slice_hdr = kargs['is_slice_hdr']

    if is_slice_hdr:
        sli = []
        p_slice = hdr[0] & 0x60
        i_slice = hdr[0] & 0x70
        if p_slice == 0x60:
            if is_idr:
                logger.critical('Wrong: P Slice but IDR!')
            #[frame type, frame length, start seq, frame discontinuity, in-FU discontinuity]
            sli = ['P', length, continuity[0], 0, 0]
        elif i_slice == 0x30:
            sli = ['I', length, continuity[0], 0, 0]
        else:
            logger.error('Unknown slice type')
        if continuity[1] > 1:
            sli[3] += continuity[1]-1
        slices.append(sli)
    else:
        # FU-A/FU-B non-start
        slices[-1][1] += length
        if continuity[1] > 1:
            slices[-1][4] += continuity[1]-1


def nal_parse(hdr, length, continuity, slices, **kargs):
    'Parse NAL by RFC3984'
    #hdr: (NAL header, slice header, slice data) when not FU-A/FU-B
    #     (FU header, FU indicator, slice header) when FU-A/FU-B start
    #     (FU header, FU indicator, slice data) when FU-A/FU-B non-start
    #length: RTP load length
    #continuity: (RTP sequence diff, RTP timestamp diff)
    #slices: slice list to store parse result
    #        [frame type, frame length, start seq, frame discontinuity, in-FU discontinuity]

    is_fu = False
    if kargs.has_key('is_fu'):
        is_fu = kargs['is_fu']
    if is_fu:
        fu_start = hdr[0] & 0x80
        fu_end = hdr[0] & 0x60
    nal_type = hdr[0] & 0x1f
    has_slice_hdr = (not is_fu) or (is_fu and fu_start)
    if nal_type == 1:
        #non-IDR slice
        slice_parse(hdr[1:], length, continuity, slices, is_slice_hdr=has_slice_hdr)
    elif nal_type == 5:
        #IDR slice
        slice_parse(hdr[1:], length, continuity, slices, is_slice_hdr=has_slice_hdr, is_idr=True)
    elif nal_type == 6:
        #SEI
        pass
    elif nal_type == 7:
        #SPS
        pass
    elif nal_type == 8:
        #PPS
        pass
    elif nal_type == 28 or nal_type == 29:
        #FU-A/FU-B
        nal_parse(hdr[1:], length, continuity, slices, is_fu=True)
    else:
        logger.error('nal_type %d' % nal_type)

def udp_det(pkt, continuity, slices):
    'Rtp over UDP detector'
    #pkt: RTP layer packet
    #continuity: (RTP sequence diff, RTP timestamp diff)
    #slices: slice list to store parse result
    #        [frame type, frame length, start seq, frame discontinuity, in-FU discontinuity]
    load = pkt[Raw].load
    try:
        hdr = (ord(load[0]), ord(load[1]), ord(load[2]))
    except (ValueError, IndexError), err:
        logger.error('nal_hdr: %s', str(err))
    nal_parse(hdr, len(load), continuity, slices)

def tcp_det(pkt, continuity, slices):
    'Rtp over TCP detector'
    #pkt: RTP layer packet
    #continuity: (RTP sequence diff, RTP timestamp diff)
    #slices: slice list to store parse result
    #        [frame type, frame length, start seq, frame discontinuity, in-FU discontinuity]
    pass

def plot(slices):
    'plot'
    #slices: slice list to store parse result
    #        [frame type, frame length, start seq, frame discontinuity, in-FU discontinuity]
    new_slices = [sli for sli in slices if sli[3] > 0 or sli[4] > 0]
    logger.debug('Losts: %d' % len(new_slices))
    logger.debug(new_slices)
    #plt.plot(slices)
    #plt.show()
