# -*- coding: utf-8 -*-
#
# HPX - dashboard
#
# Copyright (c) 2020 - ETH Zurich
# All rights reserved
#
# SPDX-License-Identifier: BSD-3-Clause

"""Wrapper around the python logging module
"""

import logging
import sys

from .singleton import Singleton


class Logger(metaclass=Singleton):
    """Logging class which is a wrapper around the logging module.

    The Logger class is a wrapper around the logging module which allows multiple console output
    or file output. Logger is a singleton.
    """

    def __init__(self, name: str, formating="%(levelname)s - %(message)s"):
        """Sets the logging module with the specified format and logger name

        Parameters
        ----------
        name
            name of the logging instance
        formatting : optional
            custom logging formatting string
        """
        logging.basicConfig()
        self.logger = logging.getLogger(name)
        self.formatter = logging.Formatter(formating)

        self.handlers = []
        self.name = name

        handler = logging.NullHandler()
        handler.setFormatter(self.formatter)

        self.handlers.append(handler)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)  # Default level

        # Due to Bokeh serve messing up the logging module, this is a work-around
        # to avoid printing the same message twice to the console
        for h in logging.getLogger(name).handlers:
            h.setFormatter(self.formatter)

        self.log_file = None

    def addHandler(self, handler, verbosity: int) -> None:
        """Adds a custom logging StreamHandler to the logging module

        Parameters
        ----------
        handler : StreamHandler
            logging stream handler to add to the logging module
        verbosity : int
            2 (by default) : infos, warning and errors are printed
            1 : only warning and errors are printed
            0 : only errors are printed
        """
        if int(verbosity) == 2:
            handler.setLevel(logging.INFO)
        elif int(verbosity) == 1:
            handler.setLevel(logging.WARNING)
        elif int(verbosity) == 0:
            handler.setLevel(logging.ERROR)

        handler.setFormatter(self.formatter)

        self.handlers.append(handler)
        self.logger.addHandler(handler)

    def setLogFile(self, filename: str) -> None:
        """Specifies a file which will contain the log.

        If there is already a log file, this function won't do anything.

        Warning
        -------
        Beware that the logger will add first erase any content which could be in
        filename before writing the log.
        """

        if not self.log_file:
            # Erase any content of the file
            with open(filename, "w") as file:
                file.close()

            file_log_handler = logging.FileHandler(filename)
            file_log_handler.setFormatter(self.formatter)
            self.logger.addHandler(file_log_handler)
            self.log_file = filename

    def setVerbosity(self, verbosity: int) -> None:
        """Sets the level of verbosity of the logger.

        Parameters
        ----------
        verbosity
            2 (by default) : infos, warning and errors are printed
            1 : only warning and errors are printed
            0 : only errors are printed
        """
        if int(verbosity) == 2:
            self.logger.setLevel(logging.INFO)
        elif int(verbosity) == 1:
            self.logger.setLevel(logging.WARNING)
        elif int(verbosity) == 0:
            self.logger.setLevel(logging.ERROR)

    def flush(self):
        """Flushes the last entry in all log handlers."""
        for h in logging.getLogger(self.name).handlers:
            h.flush()

        # Dirty hack for flushing the console, because of the NullHandler
        sys.stdout.write("\033[F")  # back to previous line
        sys.stdout.write("\033[K")  # clear line
        sys.stdout.flush()

    def info(self, message: str, flush=False) -> None:
        """Emits an information in the log.

        Parameters
        ----------
        message
            Message to be send to the logger
        flush
            If True, flushes the last line in the console output"""
        if flush:
            self.flush()
        self.logger.info(message)

    def warning(self, message: str, flush=False) -> None:
        """Emits a warning in the log.

        Parameters
        ----------
        message
            Message to be send to the logger
        flush
            If True, flushes the last line in the console output"""
        if flush:
            self.flush()
        self.logger.warning(message)

    def error(self, message: str, flush=False) -> None:
        """Emits an error in the log.

        Parameters
        ----------
        message
            Message to be send to the logger
        flush
            If True, flushes the last line in the console output"""
        if flush:
            self.flush()
        self.logger.error(message)
