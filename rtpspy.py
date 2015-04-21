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

'RtpSpy - A RTP investigation tool'

import sys
import logging
from rtspclient import RtspClient

LOGFILE = 'rtpspy.log'
logger = logging.getLogger(LOGFILE)

def prepare_log():
    'Configure logging'
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    file_handler = logging.FileHandler(LOGFILE)
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

if __name__ == '__main__':
    prepare_log()
    logger.info('#'*80)
    spy_cli = RtspClient('rtsp://10.47.165.227/cam/realmonitor?channel=1&subtype=0')
    #spy_cli = RtspClient('rtsp://10.47.161.246/StreamId=1')
    spy_cli.start()
    spy_cli.stop()
