"""
"""

__copyright__ = "Copyright (C) 2020 ETHZ"
__licence__ = "BSD 3"

import time 
import pickle

from tornado.tcpserver import TCPServer
from tornado.iostream import StreamClosedError

class Server(TCPServer):
    async def handle_stream(self, stream, address):
        print_next = False
        while True:
            try:
                request = await stream.read_until(b'\r\n')
                data_type, data = pickle.loads(request)
                
                if data_type == 'line':
                    print(data)
            except StreamClosedError:
                stream.close(exc_info=True)
                return