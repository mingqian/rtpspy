# Copyright (c) 2015 Rafael Han
# Author: Rafael Han
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

#!/usr/bin/env python

'RtpSpy: H264 process module'

import time
import struct
import logging
import matplotlib.pyplot as plt
import numpy as np

LOGFILE = 'rtpspy.log'
logger = logging.getLogger(LOGFILE)

def singleton(cls_):
    instances = {}
    def getinstance():
        if cls_ not in instances:
            instances[cls_] = cls_()
        return instances[cls_]
    return getinstance
    
@singleton
class ProcessorH264(object):
    def __init__(self):
        plt.ion()
        self.fig, self.ax = plt.subplots()
        self.i_ts = []
        self.p_ts = []
        self.u_ts = []
        self.i_size = []
        self.p_size = []
        self.u_size = []
        self.current_gopsize = 0
        self.gopsize = []
        self.time1 = time.time()
        self.ts_offset = 0
        self.tickunit = 3600.00

    def plot(self, slice_type, slice_size, seqdiff, ts, *args, **kwargs):
        #print 'type %d, size %d, seqdiff %d, ts: %d' %(slice_type, slice_size, seqdiff, ts)
        if self.ts_offset == 0:
            self.ts_offset = ts
        tick = (ts - self.ts_offset)/self.tickunit
        #print 'tick %d, offset %d' % (tick, self.ts_offset)
        if slice_type == 1: # I
            self.i_ts.append(tick)
            self.i_size.append(slice_size)
            if self.current_gopsize > 0:
                self.gopsize.append(self.current_gopsize+1) # I gopnum=0
                self.current_gopsize = 0
        elif slice_type == 2: # P
            self.p_ts.append(tick)
            self.p_size.append(slice_size)
            self.current_gopsize += 1
        elif slice_type == 0: # Unknown
            self.u_ts.append(tick)
            self.u_size.append(slice_size)

        time2 = time.time()
        if (time2 - self.time1) >= 3: #every 3 secs
            self.draw()
            self.time1 = time2
            self.ts_offset = 0
            self.i_ts[:] = []
            self.p_ts[:] = []
            self.u_ts[:] = []
            self.i_size[:] = []
            self.p_size[:] = []
            self.u_size[:] = []
            self.gopsize[:] = []
        
    def draw(self):
        logger.info('fps: %.2f' % ((len(self.i_ts) + len(self.p_ts) + len(self.u_ts))/3.0))
        for i in self.gopsize:
            logger.info('GOP length: %d' % i)
        plt.cla() #clear
        plt.bar(self.i_ts, self.i_size, width=1, color='r')
        plt.bar(self.p_ts, self.p_size, width=0.5, color='b')
        plt.bar(self.u_ts, self.u_size, width=0.5, color='y')
        plt.draw()

def h264_process(data):
    'process h264 check result from rtpclient'
    proc = ProcessorH264()
    try:
        family, slice_type, slice_size, seqdiff, ts = struct.unpack('iiIHI', data)
        proc.plot(slice_type, slice_size, seqdiff, ts)
    except Exception, err:
        print 'exception: %s' % str(err)

