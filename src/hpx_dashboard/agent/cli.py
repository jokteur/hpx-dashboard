# -*- coding: utf-8 -*-
#
# HPX - dashboard
#
# Copyright (c) 2020 - ETH Zurich
# All rights reserved
#
# SPDX-License-Identifier: BSD-3-Clause

"""Main entry for the hpx-dashboard agent parser.

This module is for parsing the command line arguments, initializing
the threads and the asyncio loop.
"""
import argparse
import asyncio
import fileinput
from queue import Queue
import threading
import sys

from ..common.logger import Logger
from . import tcp_client
from .hpx_parser import HPXParser


def args_parse(argv):
    """Parses the argument list of argv."""
    parser = argparse.ArgumentParser(
        description="The hpx-dashboard agent is used for parsing and redirecting hpx performance "
        "counter data. This data can be processed in the hpx-dashboard server which allows "
        "for live plotting of performance data. "
        "Data from a hpx program can be send through a standard pipe `|` or by reading an already "
        "existing file.",
        prog="hpx_dashboard.agent",
    )

    parser.add_argument(
        "-i",
        "--input",
        dest="input_file",
        help="input file for data collection. If not specified, stdin is used.",
        default=None,
    )

    parser.add_argument(
        "-o",
        "--out",
        dest="out_file",
        help="saves the output of the program the specified file.",
        default=None,
    )

    parser.add_argument(
        "--send-all-stdout",
        dest="send_all_stdout",
        action="store_true",
        help="when printing or redirecting the output, the agent strips the lines that countain "
        "informations about hpx counters. Setting this option will send all the stdout to the"
        "server.",
        default=False,
    )

    parser.add_argument(
        "--print-out",
        dest="print_out",
        action="store_true",
        help="prints the output of the program to the console.",
        default=False,
    )

    parser.add_argument(
        "--send-stdout",
        dest="send_stdout",
        action="store_true",
        help="redirects the stdout to the hpx-dashboard server such that it can be read from there",
        default=False,
    )

    parser.add_argument(
        "--buffer-timeout",
        dest="buffer_timeout",
        help="timeout (in ms) for the buffer to be filled before the data is sent over tcp. "
        "If the timeout is set to 0, the data is sent immediately after each collection.",
        default=10,
    )

    parser.add_argument(
        "-a",
        "--address",
        dest="host",
        help="ip-address to which the parsed data will be send "
        "(there needs to be an active hpx-dashboard server)",
        default="127.0.0.1",
    )

    parser.add_argument(
        "-p",
        "--port",
        dest="port",
        help="port used for the data transfer between the agent and the hpx-dashboard server",
        default=5267,
    )

    parser.add_argument(
        "--timeout",
        dest="timeout",
        help="length (in s) of the timeout when trying to connect to the hpx-dashboard server",
        default=2,
    )

    return parser.parse_args(argv)


class _StopSignal:
    def __init__(self):
        self.stop = False


def _threaded_io_loop(loop, args):
    asyncio.set_event_loop(loop)

    loop.run_until_complete(tcp_client.send_data(*args))


def agent(argv):
    """Main entry for the hpx performance counter collecting agent program.

    If there is an active pipe going into the agent, this will be the default input stream.
    Otherwise, the user has to specify an input file from which it will parse the counters.
    """
    logger = Logger("hpx-dashboard-agent")
    opt = args_parse(argv[1:])

    input_stream = None
    if not sys.stdin.isatty():
        input_stream = sys.stdin
    else:
        if opt.input_file:
            input_stream = fileinput.input(files=[opt.input_file])
        else:
            logger.error(
                "No active pipe is active and no input file has been specified. "
                "Data can not be collected."
            )
            return 1

    strip_hpx_data = True
    if opt.send_all_stdout:
        strip_hpx_data = False

    parser = HPXParser(
        opt.out_file,
        opt.print_out,
        strip_hpx_data,
        opt.send_stdout,
        int(opt.buffer_timeout),
    )

    queue = Queue()
    stop_signal = _StopSignal()

    # Launch tcp thread
    loop = asyncio.new_event_loop()
    tcp_thread = threading.Thread(
        target=_threaded_io_loop,
        args=(loop, (opt.host, opt.port, opt.timeout, queue, stop_signal)),
    )
    tcp_thread.daemon = True
    tcp_thread.start()

    # Launch collection
    parser.start_collection(input_stream, queue)

    if not stop_signal.stop:
        queue.join()
    else:
        sys.exit(1)
    # Send last signal for the thread to kill
    queue.put(None)
    stop_signal.stop = True
    tcp_thread.join()

    return 0


def main():
    agent(sys.argv)
