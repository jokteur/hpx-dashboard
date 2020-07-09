"""Main entry for the hpx dashboard server
"""

__copyright__ = "Copyright (C) 2020 ETHZ"
__licence__ = "BSD 3"

import sys
import optparse

from tornado.ioloop import IOLoop

from logger import Logger
from singleton import Singleton
from tcplistener import Server

def args_parse(argv):
    """
    Parses the argument list
    """
    parser = optparse.OptionParser()

    parser.add_option('-p', '--port-listen', dest='port_listen',
                      help="port on which the server listens for the incoming parsed data",
                      default=5267)

    return parser.parse_args(argv)

if __name__ == '__main__':
    """Main entry for the hpx data server."""
    logger = Logger('hpx-dashboard-server')
    opt, args = args_parse(sys.argv[1:])

    Server().listen(opt.port_listen)
    logger.info("Starting the hpx-dashboard server...")
    IOLoop.instance().start()