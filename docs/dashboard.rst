===================
Using the dashboard
===================

This section assumes that the hpx dashboard is correctly installed and that there is any kind of
compiled hpx program available. This section will use one of the HPX's example program 
`1d_stencil_4 <https://hpx-docs.stellar-group.org/latest/html/examples/fibonacci_local.html>`_.

The hpx dashboard is divided into two separate command lines: ``hpx-dashboard-agent`` and 
``hpx-dashboard-server``. The role of the agent is to collect the data and parse it. With
the agent, you can filter out hpx data from the standard output and redirect non hpx data to a 
file or to the console. The agent connects to the server (also called the plotting server), and
sends data to it through TCP. The server will collect and organise the incoming data. Finally, the
user connects to the plotting server through the web-browser. It is also possible to do the plotting
directly on a jupyter notebook (see :doc:`jupyter`).

.. image:: _static/images/dashboard_explanation.png
    :width: 95%

Dashboard server
----------------

First start the server with ``hpx-dashboard-server``. As there is some rendering of the plots done
on the server, there is a compilation (using datashader) that is triggered whenever the server is
launched. Because of this, it could take a few seconds before the server starts.

By default, the server is listening on the port 5267 for incoming data, and is launching the Bokeh
server (plotting) on port 5006. It is possible to modify these ports with the ``-pb`` (short for
port bokeh) and ``-pl`` (short for port listen) options. Once the server is started, simply connect
with the browser for example to ``localhost:5006``.

.. image:: _static/images/dashboard_startpage.jpg
    :width: 70%

By default, the server will save all the data of a session in a local folder named
``hpx_data.<timestamp>``. It is possible to change the path of this folder with the option
``-s <save_path>``. This folder will contain a ``session_metadata.json`` - which describes
the session - and multiple csv files containing the task and the counter data. This auto-save can
be deactivated with ``--no-auto-save``.

To import data from a previous session, use the option ``-i <import path>``. If the import is
successful, then the active session will be the imported folder. Any new data coming to the
server will then be saved to the imported folder, except if ``-no-auto-save`` was also specified.


Dashboard agent
---------------
The agent can be used only if there is an active dashboard server listening (normal or jupyter).
To start collecting live data, simply pipe the standard output to the agent:

.. code:: bash

    1d_stencil_4 | hpx-dashboard-agent

However, in the example above, ``1d_stencil_4`` will produce no data. This means that the server
will create an empty data collection. To send performance counter, simply specify in the command
of the HPX program:

.. code:: bash

    1d_stencil_4 --hpx:print-counter=/scheduler/* --hpx:print-counter=/threads/* | hpx-dashboard-agent

The previous code will send scheduler and threads counters to the server.

Task data
^^^^^^^^^
Right now, live task data is an experimental feature only available in a git branch `here <https://github.com/msimberg/hpx/tree/simple-task-timers>`_.
To use this, compile HPX with the cmake option ``-DHPX_WITH_SIMPLE_TASK_TIMERS=ON``.
Once the program is compiled, you can send task data by doing:

.. code:: bash

    1d_stencil_4 --hpx:print-task-timers | hpx-dashboard-agent

Sending data to another computer
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Simply specify in the option the address and the port:

.. code:: bash

    <stuff> | hpx-dashboard-agent -a <address> -p <port>

There are other options available in the agent, please use ``hpx-dashboard-agent -h`` to explore them.