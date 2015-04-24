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

'RtpSpy: RTSP Client module'

import sys
import os
from time import ctime
import logging
import socket
import random
from scapy.all import StreamSocket, IP, UDP, Raw, sniff
import rtpdet

RTSP_PORT = 554

LOGFILE = 'rtpspy.log'
logger = logging.getLogger(LOGFILE)

class Sdp(object):
    'RTSP SDP class'
    def __init__(self, desc_resp):
        'Create SDP object by parsing DESCRIBE response'
        if self.parse_resp(desc_resp) == False:
            return None

    def __str__(self):
        line = []
        for media in self.sessions:
            line.append(media.__str__())
        return os.linesep.join(line)

    __repr__ = __str__

    def parse_resp(self, resp):
        'Parse SDP, returns False when no valid media sessions'
        sessions = []
        for line in resp.strip().split('\r\n'):
            try:
                if line[:2] == 'm=':
                    media = MediaSession()
                    item = line[2:] .split(' ')
                    #only process video
                    if item[0] == 'video':
                        media.payload_num = int(item[3])
                    sessions.append(media)

                elif line[:2] == 'a=':
                    media = sessions[-1]
                    item = line[2:].split(':', 1)

                    if item[0] == 'control':
                        media.control = item[1]
                    elif item[0] == 'framerate':
                        media.framerate = float(item[1])
                    elif item[0] == 'rtpmap':
                        rtpmap = item[1].split(' ')
                        if int(rtpmap[0]) == media.payload_num:
                            media.payload_type = rtpmap[1].strip()
                    elif item[0] == 'fmtp':
                        fmtp = item[1].split(' ')
                        if int(rtpmap[0]) == media.payload_num:
                            fmtp2 = fmtp[1].split(';')
                            for i in fmtp2:
                                tmp = i.split('=', 1)
                                if tmp[0] == 'packetization-mode':
                                    media.packetization_mode = tmp[1]
                                elif tmp[0] == 'profile-level-id':
                                    media.profile_level_id = tmp[1]
                                elif tmp[0] == 'sprop-parameter-sets':
                                    media.sprop_parameter_sets = tmp[1]
            except (IndexError, ValueError), err:
                print 'Skip SDP line: %s : %s' % (line, str(err))
                continue

        self.sessions = [media for media in sessions if media.check()]

        return self.sessions_check()

    def sessions_check(self):
        'SDP media sessions sanity check'
        if len(self.sessions) > 0:
            ret_val = True
        else:
            # contains no media
            ret_val = False

        return ret_val

    def get_sessions(self):
        'Get media sessions'
        return self.sessions


class MediaSession(object):
    'RTSP Session class'
    def __init__(self):
        'Create MediaSession object by parsing SETUP response'
        self.payload_num = None
        self.payload_type = None
        self.control = None
        self.packetization_mode = ''
        self.profile_level_id = ''
        self.sprop_parameter_sets = ''
        self.session_num = None


    def __str__(self):
        line = []
        try:
            line.append('payload: %d -> %s' % (self.payload_num, self.payload_type))
            line.append('control: %s' % self.control)
            line.append('packetization_mode: %s' % self.packetization_mode)
            line.append('profile_level_id: %s' % self.profile_level_id)
            line.append('sprop_parameter_sets: %s' % self.sprop_parameter_sets)
            line.append('session num: %s' % self.session_num)
            return os.linesep.join(line)
        except ValueError, err:
            return 'Incomplete media: %s' % str(err)

    __repr__ = __str__

    def parse_resp(self, resp):
        'Parse SETUP response'
        ret_val = False
        for line in resp.strip().split('\r\n'):
            if line[:8] == 'Session:':
                self.session_num = line[8:].strip().split(';')[0]
                ret_val = True
        return ret_val

    def check(self):
        'MediaSession object sanity check'
        return self.payload_num != None \
                and self.payload_type != None \
                and self.control != None

    def get_session_num(self):
        'Get session number'
        return self.session_num

class RtspClient(object):
    'RTSP client'
    def __init__(self, url):
        self.url = url.strip()
        dst = self.url.split('/')[2].split(':')
        if len(dst) > 1:  # user provides port
            self.dst_addr = dst[0]
            self.dst_port = dst[1]
        else:
            self.dst_addr = dst[0]
            self.dst_port = RTSP_PORT

        self.sock = socket.socket()
        self.sock.connect((self.dst_addr, self.dst_port))
        self.stream_sock = StreamSocket(self.sock)
        self.cseq = 1
        self.rtp_port = random.randint(10000, 60000)
        self.sessions = [] # a list of media sessions

    @staticmethod
    def rtsp_response_check(resp):
        'RTSP response general sanity check'
        if resp.split('\r\n')[0] != 'RTSP/1.0 200 OK':
            logger.error('Error response: %s' % resp)
            return False
        return True

    def send_rtsp_request(self, line):
        'Send RTSP requests'
        req = '\r\n'.join(line)
        req += '\r\n\r\n'
        ret = self.stream_sock.sr1(Raw(load=req))
        if self.rtsp_response_check(ret[Raw].load) == True:
            return ret[Raw].load
        else:
            return None


    def send_options(self):
        'Send RTSP OPTIONS request'
        line = []
        line.append(' '.join(['OPTIONS', self.url, 'RTSP/1.0']))
        line.append(' '.join(['CSeq:', str(self.cseq)]))
        line.append(' '.join(['Date:', ctime(), 'GMT']))
        resp = self.send_rtsp_request(line)
        if resp != None:
            self.cseq += 1

    def send_describe(self):
        'Send RTSP DESCRIBE request'
        line = []
        line.append(' '.join(['DESCRIBE', self.url, 'RTSP/1.0']))
        line.append(' '.join(['CSeq:', str(self.cseq)]))
        line.append(' '.join(['Accept:', 'application/sdp']))
        line.append(' '.join(['Date:', ctime(), 'GMT']))
        resp = self.send_rtsp_request(line)
        if resp != None:
            sdp = Sdp(resp)
            if sdp != None:
                self.sessions = sdp.get_sessions()
                self.cseq += 1

    @staticmethod
    def listen_udp(port):
        # nc -lu <port>
        cmd = 'nc -lu %d > /dev/null' % port
        os.system(cmd)

    def send_setup(self, media):
        'Send RTSP SETUP request'
        print 'RTP Port: ', self.rtp_port
        pid = os.fork()
        if pid == 0:
            # child process
            pid2 = os.fork()
            if pid2 == 0:
                # child2 process: listen RTCP port
                self.listen_udp(self.rtp_port + 1)
                sys.exit()
            else:
                # child process: listen RTP port
                self.listen_udp(self.rtp_port)
                sys.exit()
        else:
            line = []
            control_url = self.url + '/' + media.control
            line.append(' '.join(['SETUP', control_url, 'RTSP/1.0']))
            line.append(' '.join(['CSeq:', str(self.cseq)]))
            line.append(' '.join(['Transport:', 'RTP/AVP;unicast;client_port=%d-%d' % \
                    (self.rtp_port, self.rtp_port+1)]))
            line.append(' '.join(['Date:', ctime(), 'GMT']))
            resp = self.send_rtsp_request(line)
            if resp != None:
                if media.parse_resp(resp) == True:
                    logger.info(media)
                    self.cseq += 1

    def send_play(self, media):
        'Send RTSP PLAY request'
        line = []
        line.append(' '.join(['PLAY', self.url, 'RTSP/1.0']))
        line.append(' '.join(['CSeq:', str(self.cseq)]))
        line.append(' '.join(['Date:', ctime(), 'GMT']))
        line.append(' '.join(['Session:', media.get_session_num()]))
        line.append(' '.join(['Range:', 'npt=0.000-']))
        resp = self.send_rtsp_request(line)
        if resp != None:
            self.cseq += 1

    def send_teardown(self, media):
        'Send RTSP TEARDOWN request'
        line = []
        line.append(' '.join(['TEARDOWN', self.url, 'RTSP/1.0']))
        line.append(' '.join(['CSeq:', str(self.cseq)]))
        line.append(' '.join(['Date:', ctime(), 'GMT']))
        line.append(' '.join(['Session:', media.get_session_num()]))
        resp = self.send_rtsp_request(line)
        if resp != None:
            self.cseq += 1

    def start(self):
        'Convenient method to start play'
        self.send_options()
        self.send_describe()
        for media in self.sessions:
            self.send_setup(media)
            media.det = rtpdet.RtpDet(media)
            self.send_play(media)
            bpf = 'udp and ip host %s' % self.dst_addr
            try:
                #at least 20 bytes for UDP hdr(8) + RTP hdr(12)
                sniff(filter=bpf, \
                        lfilter=lambda x: x.haslayer(IP) and x[IP].src == self.dst_addr \
                        and x.haslayer(UDP) and x[UDP].len > 20, \
                        prn=media.det.parse)
            except (KeyboardInterrupt, IndexError), err:
                logger.error('sniff failed: %s' % str(err))
                self.stop()

    def stop(self):
        'Convenient method to stop play'
        logger.error('Going to STOP')
        for media in self.sessions:
            self.send_teardown(media)
            if media.det:
                media.det.plot()
        sys.exit()
