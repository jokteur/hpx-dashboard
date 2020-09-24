=================
HPX dashboard
=================

This document will guide you through the basic steps to get started with the HPX dashboard.

------------
Installation
------------

As the dashboard is almost entirely built with Python, installation can be done through the usual
``pip install``. It is recommended to create a virtual environnement:

.. code:: bash

    python -m venv path_for_the_venv
    source path_for_the_venv
    pip install --upgrade wheel

or if you use anaconda, you can create the environnement as follows:

.. code:: bash

    conda create --name myenv python=3.8

Once the environnement is created, clone the repository:

.. code:: bash

    git clone https://github.com/jokteur/hpx-dashboard

For regular users, installation can be done with the command:

.. code:: bash

    cd hpx-dashboard
    pip install .

For developpers, it is recommended to install with the source in place:

.. code:: bash

    cd hpx-dashboard
    pip install -e .
    
    # Install pre-commit and Sphinx additionnaly
    pip install -r ./requirements-dev.txt
    # Install the hooks for git
    pre-commit install

Once the hpx-dashboard is installed, make sure that it works by testing the command:

.. code:: bash

    hpx-dashboard-server

If after a few seconds, it shows

.. code:: bash

    INFO:hpx-dashboard:Bokeh server started on http://localhost:5006

Then it means that the installation has been successful.^

^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Installation on CSCS - Daint
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
If you are a user of the supercomputer Piz Daint of the CSCS, then the installation procedure is a
little bit different. To create the virtual environnement:

.. code:: bash

    # Load the python module if it is not already loaded
    module load cray-python
    python -m venv path_for_the_venv
    # It may that the wrong packages (from system packages) will load once the program is running
    # Before activating the environnement, you can unset the python path
    unset PYTHONPATH
    # Then activate the environnement
    source ./path_for_the_venv/bin/activate

Then the rest of the installation should be similar as described above.


------------
Introduction
------------

^^^^^^^^^^^^^
What is HPX ?
^^^^^^^^^^^^^

HPX is an open-source C++ standard library for Concurrency and Parallelism which closely follows 
the C++11/14/17/20 ISO standard. The goal of HPX is to provide an open source implementation of a
`new programming model <https://hpx-docs.stellar-group.org/latest/html/why_hpx.html#parallex-a-new-execution-model-for-future-architectures>`_
which allows to fully take advantage of parallel systems, from low power devices to large scale 
clusters. This means that the libary allows for task-based programming: the user can spawn millions
of threads (i.e. tasks) with minimal overhead.

To learn more about HPX, visit the `official documentation <https://hpx-docs.stellar-group.org/latest/html/index.html>`_ or the `official github <https://github.com/STEllAR-GROUP/hpx>`_.

^^^^^^^^^^^^^
The dashboard
^^^^^^^^^^^^^

The goal of the HPX dashboard is to provide an open-source interactive dashboard for debugging and 
performance analysis of HPX applications. The tool is build with Python and `Bokeh <https://bokeh.org/>`_
, which allows for interactive plotting. Here are the goals of the project:

* It should be an external tool that does not add overhead on the HPX application. This is why data produced by HPX can be streamed over the network to the plotting server of the dashboard.
* The tool should be in real-time. Indeed, HPX has a capability of producing real-time data (with the `performance counters <https://hpx-docs.stellar-group.org/latest/html/manual/optimizing_hpx_applications.html#performance-counters>`_). This allows for the user to have a quick feedback on the performance of his app. 
* Integration with Jupyter notebooks. With the notebooks, the user explore the data that is collected by the dashboard and also extend it.
* A tool that is also build for the demonstration of HPX applications in tutorials and courses.

This tool is *not* intended to replace more advanced profiling tools such as vampire. Also, due to
current limitations with Python and rendering, this tool cannot process extremely large datasets
which typically result from very long executions of HPX applications.

^^^^^^^^^^^^^^^^^^
Terminology of HPX
^^^^^^^^^^^^^^^^^^
As the dashboard is specifically build for HPX, it also uses some of its `terminology <https://hpx-docs.stellar-group.org/latest/html/terminology.html>`_.

.. figure:: _static/images/hpx_model.png

   *fig 1.* The HPX programming model (from https://github.com/STEllAR-GROUP/tutorials/tree/master/hlrs2019/session2)

Based on the previous figure, here are some explanations for the terms used in the dashboard:

* **Performance counter**: data provided from HPX which indicates how well the runtime system or an application is running. The counter data is produced live an can be plotted in the dashboard. To know more about what kind of performance counter exist, please visit `this page <https://hpx-docs.stellar-group.org/latest/html/manual/optimizing_hpx_applications.html#performance-countersl>`_.
* **Locality**: A locality designates a synchronous domain of execution, which is usually a single node in a cluster or a NUMA domain. When executed on a single machine, there is only one locality, designated by 0.
* **Thread**: A thread (or worker thread) corresponds to a real CPU thread on a locality which waits on tasks to be delivered by the *thread scheduler*. The number of available worker threads is by default the number of CPU cores on the system and can be otherwise specified with the `--hpx:threads` option in the HPX application.
* **Pool**: Sometimes, threads on a locality can be grouped into pools. If no pool-name is specified the counter refers to the 'default' pool.
* **Task**: A task designates some piece of work that can be executed on a thread. A basic HPX task has a name, the ID of the worker thread on which it is executed, a beginning and an end. All the finished tasks are plotted on the dashboard in the `task plot` tab.
