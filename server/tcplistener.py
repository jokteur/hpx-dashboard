"""
"""

__copyright__ = "Copyright (C) 2020 ETHZ"
__licence__ = "BSD 3"

import time 

from tornado.tcpserver import TCPServer
from tornado.iostream import StreamClosedError

class Server(TCPServer):
    async def handle_stream(self, stream, address):
        print_next = False
        while True:
            try:
                request = await stream.read_until(b'\r\n')
                request = request.decode('utf-8').strip()
                
                if 'OS_Threads' in request:
                    print(request)
                    print_next = True
                    continue
                if print_next:
                    print(request)
                    print_next = False
            except StreamClosedError:
                stream.close(exc_info=True)
                return