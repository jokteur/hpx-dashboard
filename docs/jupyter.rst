=================================
Exploring the data with notebooks
=================================
It is also possible to execute the dashboard and explore its data in a Jupyter notebook. 

Installation
------------

Make sure that you have the correct environment installed and activated as explained in the
:doc:`quickstart`.

Install jupyter notebook in the environment and start a new notebook:

.. code:: bash

    pip install jupyter
    jupyter notebook

Installation on Daint
---------------------
For users that desire to use the notebook on the CSCS cluster *Daint*, please follow 
`this link <https://user.cscs.ch/tools/interactive/jupyterlab/#ipython>`_ to learn how to create 
jupyter kernels on the JupyterLab. Kernels are necessary to access virtual environments that you
may have created on your user account.

Currently, pre-built hpx-dashboard widgets and plots do not work in the interactive JupyterLab
session. However, you may still collect data and explore it with pandas.

Initializing the session
------------------------
Once the notebook is started, you need to initialize a new hpx-dashboard session. The 
:py:func:`start <hpx_dashboard.server.notebook.start>` function is there to initialize the TCP
server for listening and initialize the Bokeh output. You can import the 
:py:mod:`notebook <hpx_dashboard.server.notebook>` notebook module and do:

.. code:: python

    from hpx_dashboard.server.notebook import start
    start()

On this function has been called, the hpx dashboard server will be ready to receive and save
incoming hpx data. This function can only be called once in a session. Restart the jupyter kernel
if you want to reinitialize this function. By default, this function will save any incoming data to
a local folder in the form of ``hpx_data.<timestamp>``. If you do not want auto-saving in your
session, then just add the argument ``start(auto_save=False)``.

Importing a session
-------------------
You may want to import data from a previous session. There are two ways to do this. The first is to
specify the option in the :py:func:`start <hpx_dashboard.server.notebook.start>` function:

.. code:: python

    start(import_path="example_folder/hpx_data.123")

If successful, then you can explore the data saved in the specified folder. If ``auto_save`` is set
to ``True``, then any new data coming to the hpx-dashboard server will also be saved in the import
folder. If you want to avoid this, specify the ``import_path`` and set ``auto_save`` to ``False``.

If you have already an active session (i.e. ``start`` has already been called), but you still want
to explore data from another session, then you can still import with the
:py:class:`DataAggregator <hpx_dashboard.server.data.DataAggregator>` (see :ref:`aggregator`):

.. code:: python

    from hpx_dashboard.server.data import DataAggregator
    DataAggregator().import_session("example_folder/hpx.123")

This will abandon the current session and make the imported session as the current session.

.. _aggregator:

The Data aggregator
-------------------
The data aggregator is a Singleton object that collects all the runs (also called 
:py:class:`DataCollection <hpx_dashboard.server.data.DataCollection>`) that are in the session. 
With the object, you can explore all past and current collections present in the session.

If you want to explore live data, just call:

.. code:: python

    from hpx_dashboard.server.data import DataAggregator
    collection = DataAggregator().get_live_collection()

If there is a current live session going on, then the corresponding 
:py:class:`DataCollection <hpx_dashboard.server.data.DataCollection>` object is returned. If there
are no live collection but still there have been past collections, then the most recent collection
is returned. If there are no collections at all in the session, then ``None`` is returned.

If you want to get the last collection ignoring any live collection, call:

.. code:: python

    collection = DataAggregator().get_last_run()

And if you want to get all the collections present in the session (live or not), then call:

.. code:: python

    # Returns a list of all the collections objects in the session
    collection = DataAggregator().get_all_runs()

Using the dashboard's widgets
-----------------------------

It is possible to use individually the widgets of the standalone Bokeh server (see :doc:`dashboard`).
Currently, there are three available widgets: 
:py:func:`scheduler plot <hpx_dashboard.server.notebook.scheduler>`, 
:py:func:`task plot <hpx_dashboard.server.notebook.tasks>`, and 
:py:func:`customizable plot <hpx_dashboard.server.notebook.custom_counter>`.
These widgets will already know about the data present in the session.

.. code:: python

    from hpx_dashboard.server.notebook import scheduler, tasks, custom_counter
    scheduler() # Plots the scheduler utilization
    tasks() # Show the task plot widget
    custom_counter() # Show the customizable plot widget


Exporting data as pandas DataFrames
-----------------------------------

Data present in the session can be exported to pandas DataFrames for further exploration. You can
export task data with the :py:func:`DataCollection.export_task_data <hpx_dashboard.server.data.DataCollection.export_task_data>`
and export counter data with the :py:func:`DataCollection.export_counter_data <hpx_dashboard.server.data.DataCollection.export_counter_data>`.
Here is one little snipped:

.. code:: python

    collection = DataAggregator().get_last_run()
    if collection:
        df = collection.export_task_data()
        print(df)

