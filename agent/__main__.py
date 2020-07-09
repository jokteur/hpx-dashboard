"""Main entry for the hpx agent parser
"""

__copyright__ = "Copyright (C) 2020 ETHZ"
__licence__ = "BSD 3"

import sys
import optparse
import time
import fileinput

import asyncio

from logger import Logger
import tcpclient
from hpx_parser import HPXParser

def args_parse(argv):
    """Parses the argument list of argv.
    """
    parser = optparse.OptionParser()

    parser.add_option('-i', '--input', dest='input_file',
                      help="input file for data collection. If not specified, stdin is used.",
                      default=None)

    parser.add_option('-o', '--out', dest='out_file',
                      help="saves the output of the program the specified file.",
                      default=None)
                      
    parser.add_option('--strip-hpx-counters', dest='strip_hpx_counters', action='store_true',
                      help="when printing or redirecting the output strips the lines that countain informations about hpx counters.",
                      default=False)

    parser.add_option('--print-out', dest='print_out', action='store_true',
                      help="prints the output of the program to the console.",
                      default=False)
                      
    parser.add_option('-a', '--address', dest='host',
                      help="ip-address to which the parsed data will be send (it needs an active hpx-dashboard server running)",
                      default='127.0.0.1')
                      
    parser.add_option('-p', '--port', dest='port',
                      help="port used for the data transfer between the agent and the hpx-dashboard server",
                      default=5267)
                      
    parser.add_option('--timeout', dest='timeout',
                      help="length of the timeout when trying to connect to the hpx-dashboard server (in seconds)",
                      default=2)

    return parser.parse_args(argv)



async def amain(argv):
    """Main entry for the hpx performance counter collecting agent program.

    If there is an active pipe going into the collecting agent, this will be the default input stream.
    Otherwise, the user has to specify an input file from which it will parse the hpx performance counters.
    """
    logger = Logger('hpx-dashboard-agent')
    opt, args = args_parse(argv[1:])

    input_stream = None                                              
    if not sys.stdin.isatty():
        input_stream = sys.stdin
    else:
        if opt.input_file:
            input_stream = fileinput.input(files=[opt.input_file])
        else:
            logger.error("No active pipe is active and no input file has been specified. Data can not be collected.")
            return 1

    tcp_writer = None
    try:
        tcp_writer = await tcpclient.connect(opt.host, opt.port)
    except TimeOutError:
        logger.error(f"Timeout error: could not connect to {opt.host}:{opt.port} after {opt.timeout} seconds")
        return 1
        
    parser = HPXParser(opt.out_file, opt.print_out, opt.strip_hpx_counters)
    queue = asyncio.Queue()

    producer = asyncio.create_task(parser.start_collection(input_stream, queue))
    consumer = asyncio.create_task(tcpclient.send_data(tcp_writer, queue))

    await asyncio.gather(producer)
    await queue.join()
    print("SDf")
    consumer.cancel()
    return 0

if __name__ == '__main__':
    return_code = asyncio.run(amain(sys.argv))
    sys.exit(return_code)