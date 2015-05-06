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

import socket
import struct
import matplotlib

def h264_process(sock):
    'process h264 check result from rtpclient'
    try:
        data, addr = sock.recvfrom(100)
        # todo: support for different slice family
        family, slice_type, slice_size = struct.unpack('iiI', data)
        #print 'type %d, size %d' %(slice_type, slice_size)
        h264_plot(slice_type, slice_size)
    except socket.error:
        pass

def h264_plot(slice_type, slice_size, **kwargs):
    print 'type %d, size %d' %(slice_type, slice_size)
    pass

