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
from .tcp_listener import TCP_Server, handle_response
from .components import scheduler_doc, tasks_doc, custom_counter_doc
from .worker import worker_thread, WorkerQueue


def start(port=5267):
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
    show(lambda doc: scheduler_doc({}, doc))


def tasks():
    show(lambda doc: tasks_doc({}, doc))


def custom_counter():
    show(lambda doc: custom_counter_doc({}, doc))
