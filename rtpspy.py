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
import os
import getopt
import logging
from time import ctime
from rtspclient import RtspClient

LOGFILE = 'rtpspy.log'
logger = logging.getLogger(LOGFILE)

def prepare_log():
    'Configure logging'
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(levelname)s:' + os.linesep + '%(message)s' + os.linesep)
    file_handler = logging.FileHandler(LOGFILE)
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

def usage():
    print 'rtpspy -- RTP investigation Tool', os.linesep
    print 'Run with ', sys.argv[0], ' [options]' ' "url"', os.linesep
    print 'Options: ', os.linesep
    print '-h/--help:\t' 'help', os.linesep
    print '-o/--output=:\t' 'specify log file', os.linesep
    print 'Put URL string in double quotes(" ")'

def url_check(arg):
    'URL arg sanity check, return None on error'
    return arg

if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'ho:', ['help', 'output='])
    except getopt.GetoptError as err:
        print str(err)
        usage()
        sys.exit(2)

    url = None
    output = None

    for opt, arg in opts:
        if opt in ('-h', '-help'):
            usage()
            sys.exit()
        elif opt in ('-o', 'output='):
            pass

    if len(args) > 0:
        url = url_check(args[0])
        print 'URL: ', url

    if url == None:
        usage()
        sys.exit(2)

    prepare_log()
    logger.info('#'*20 + ctime() + '#'*20)
    spy_cli = RtspClient(url)
    spy_cli.start()
    spy_cli.process()
    print 'bye'
    sys.exit()
