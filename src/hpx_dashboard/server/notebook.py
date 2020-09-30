# -*- coding: utf-8 -*-
#
# HPX - dashboard
#
# Copyright (c) 2020 - ETH Zurich
# All rights reserved
#
# SPDX-License-Identifier: BSD-3-Clause

"""Module for integration into Jupyter notebooks"""

from queue import Queue
import threading

from bokeh.plotting import output_notebook, show

from ..common.logger import Logger
from .data import DataAggregator
from .tcp_listener import TCP_Server, handle_response
from .components import scheduler_doc, tasks_doc, custom_counter_doc
from .worker import worker_thread, WorkerQueue


def start(port=5267, auto_save=True, save_path="", import_path=""):
    """Starts the TCP server for incoming data and the bokeh ioloop.

    Can only be called once in a session.

    Arguments
    ---------
    port : int
        port on which the TCP client listens for incoming data
    auto_save : bool
        if True, the session will be automatically saved at save_path.
        A directory is created for each session `hpx_data.<timestamp>`.
    save_path : str
        path where the session will be saved. Is only used if auto_save==True
    import_path : str
        imports a previous session into the new session.
        Any new data coming to this session will be saved in the imported session.
    """
    DataAggregator(auto_save=auto_save, save_path=save_path, import_path=import_path)

    tcp_queue = Queue()
    tcp_server = TCP_Server(queue=tcp_queue)
    tcp_server.listen(port)
    tcp_thread = threading.Thread(target=lambda: handle_response(tcp_queue))
    tcp_thread.daemon = True
    tcp_thread.start()

    work_queue = WorkerQueue()
    work_thread = threading.Thread(target=lambda: worker_thread(work_queue))
    work_thread.daemon = True
    work_thread.start()

    output_notebook()

    Logger().info(f"Server has started and is listening on port {port}")


def scheduler():
    """Shows the scheduler plot in a notebook."""
    show(lambda doc: scheduler_doc({}, doc))


def tasks():
    """Shows the task plot in a notebook."""
    show(lambda doc: tasks_doc({}, doc))


def custom_counter():
    """Shows the custom counter plot widget in a notebook."""
    show(lambda doc: custom_counter_doc({}, doc))
