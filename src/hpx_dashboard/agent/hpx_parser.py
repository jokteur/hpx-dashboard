# -*- coding: utf-8 -*-
#
# HPX - dashboard
#
# Copyright (c) 2020 - ETH Zurich
# All rights reserved
#
# SPDX-License-Identifier: BSD-3-Clause

"""Module for parsing the stdout of an HPX program.
"""

import time
import pickle
import re

from ..common.logger import Logger


class FixedBuffer:
    def __init__(self, size):
        """"""
        self._buffer = [""] * size
        self._size = size
        self._index = 0

    def add(self, line):
        """"""
        if self._index < self._size:
            self._buffer[self._index] = line
            self._index += 1
        else:
            self._buffer = self._buffer[1:] + [line]

    def get(self):
        return self._buffer


class HPXParser:
    """"""

    def __init__(
        self,
        out_file=None,
        print_out=False,
        strip_hpx_counters=False,
        send_stdout=False,
        buffer_timeout=0,
    ):
        """Initializes the data collectors

        Parameters
        ----------
        out_file : str
            output file to which the output of the program should be written
        print_out : bool
            if true, prints the output of the program to the console
        strip_hpx_counters: bool
            if true, when printing either to the console or a file, the hpx performance counters
            and similar informations are stripped from the output
        buffer_timeout: None or float
            time that happens between two TCP sends (in miliseconds)
            In pratice the buffer of the parser gets filled until a certain time and
            then the data gets sent once the time is over.
        """

        self.counter_descriptions = {}
        self.collect_counter_infos = False
        self.current_counter_name = ""
        self.queue = None

        self.out_file_handler = None
        if out_file:
            self.out_file_handler = open(out_file, "w")

        self.out_file = out_file
        self.print_out = print_out
        self.strip_hpx_counters = strip_hpx_counters
        self.send_stdout = send_stdout

        # To check when the --hpx:list-counter-infos evt finishes
        self.hpx_info_buffer = FixedBuffer(3)

        self.buffer_timeout = buffer_timeout
        self.last_buffer_send = None
        self.buffer = []

    def _add_to_buffer(self, data):
        """Adds the data to the buffer and if the buffer_timeout is elapsed,
        the buffer is emptied into the queue"""

        self.buffer.append(data)

        if (time.time() - self.last_buffer_send) * 1000.0 > self.buffer_timeout:
            self.queue.put(pickle.dumps(("regular-data", self.buffer)))
            self.last_buffer_send = time.time()
            self.buffer = []

    def parse_line(self, line):
        """Parses a line and if the lines has some hpx performance counter data, it is added to the data

        Returns
        -------
        bool
            True if the line has something do to with hpx performance data, false otherwise
        """

        line = line.strip()
        hpx_separator = "-" * 78
        self.hpx_info_buffer.add(line)

        # Regex based on
        # https://stellar-group.github.io/hpx/docs/sphinx/latest/html/manual/optimizing_hpx_applications.html#performance-counter-names
        objectname_re = "/([a-zA-Z_][a-zA-Z_0-9\\-]*)"
        fullinstancename_re = "\\{(.*)\\}"
        countername_re = "/([a-zA-Z_0-9\\-/]+)"
        parameters_re = "@?([a-zA-Z_0-9\\-]+)?"
        regex = '"?' + objectname_re + fullinstancename_re + countername_re + parameters_re + '"?'

        result = re.match("^" + regex, line)

        if result:
            # As there can be commas inside the counter name, it is essential to split the line
            # only after the name. The first split should be an empty string, because we split
            # just after the counter name
            regex_end = result.span()[1]
            line_split = line[regex_end:].split(",")
            if len(line_split) in [5, 6]:
                objectname = result.group(1)
                full_instancename = result.group(2)
                countername = result.group(3)
                parameters = result.group(4)

                fullname = objectname + "/" + countername

                value_unit = None
                if len(line_split) == 6:
                    value_unit = line_split[5]

                # The given data in order: fullname, full_instancename, parameters, sequence_number,
                # timestamp, timestamp_unit, value, value_unit
                data = (
                    "counter-data",
                    [
                        fullname,
                        full_instancename,
                        parameters,
                        int(line_split[1]),
                        float(line_split[2]),
                        line_split[3],
                        line_split[4],
                        value_unit,
                    ],
                )
                self._add_to_buffer(data)

            # Means that we are somewhere in --hpx:list-counters or that the user intentionnaly
            # prints an hpx counter
            else:
                # Skip line but no data collection
                return True

            # It is assumed that once the first hpx performance counter is outputed, the
            # --hpx:list-counter-infos is finished.
            # This means that the counter informations can be sent
            if self.collect_counter_infos:
                self.queue.put(pickle.dumps(("counter-infos", self.counter_descriptions)))
            self.collect_counter_infos = False

            return True

        # Try to determine when exactly the --hpx:list-counter-infos finishes printing
        if self.collect_counter_infos:
            buffer = self.hpx_info_buffer.get()
            if buffer[0] == hpx_separator and buffer[1] == "\n" and buffer[2] != hpx_separator:
                self.collect_counter_infos = False

        # Lines generated by --hpx:list-counter-infos
        if line == "Information about available counter instances":
            self.collect_counter_infos = True
            return True

        # Try to extract fullname, helptext, type and version from counter infos if they exist
        split = line.split(":")
        if len(split) > 1 and self.collect_counter_infos:
            split[0] = split[0].strip()
            split[1] = split[1].strip()
            if "fullname" in split[0] and re.match(regex, split[1]):
                self.current_counter_name = split[1]
                self.counter_descriptions[self.current_counter_name] = {}
                return True
            elif self.current_counter_name:
                if split[0] in ["helptext", "version", "type"]:
                    self.counter_descriptions[self.current_counter_name][split[0]] = "".join(
                        split[1:]
                    )
                    if split[0] == "version":
                        self.current_counter_name = ""
                    return True

        # If we arrive here, it means that the line is neither some counter infos or performance
        # counter data. There could be still `\n` between the counter infos that we want to count
        # as part of hpx output
        if self.collect_counter_infos:
            return True

        # Collect task counter infos
        split = line.split(",")
        if len(split) == 6 and split[0] == "task_data":
            data = (
                "task-data",
                [
                    split[1],  # Locality num
                    split[2],  # Worker-thread num
                    split[3],  # Task name
                    split[4],  # Begin time
                    split[5],  # End time
                ],
            )
            self._add_to_buffer(data)
            return True

        # If we arrive here, this means that the line should be a simple non hpx-related stdout
        else:
            return False

    def start_collection(self, input_stream, queue):
        """Starts collecting from the input stream until the HPX program is finished or interrupted
        and sends the data to the hpx-dashboard server.

        Parameters
        ----------
        input_stream : mixed
            streaming input (either stdin or fileinput) TCPClient
            TCP client to which the data will be send
        queue : asyncio.Queue
            queue for putting the parsed data to be send via TCP
        """

        self.queue = queue

        self.queue.put(pickle.dumps(("transmission_begin", time.time())))
        self.last_buffer_send = time.time()

        try:
            for line in input_stream:
                strip_line = self.parse_line(line)
                strip_line = strip_line and self.strip_hpx_counters

                # Take care of redirecting the output of the program
                if self.print_out and not strip_line:
                    Logger().info(line.strip())
                if self.out_file_handler and not strip_line:
                    self.out_file_handler.write(line)
                if self.send_stdout and not strip_line:
                    self._add_to_buffer(("line", line.strip()))
        except KeyboardInterrupt:
            Logger().info("Keyboard interrupt, ending transmission.")

        if self.buffer:
            self.queue.put(pickle.dumps(("regular-data", self.buffer)))

        self.queue.put(pickle.dumps(("transmission_end", time.time())))
