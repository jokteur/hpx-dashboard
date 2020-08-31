# -*- coding: utf-8 -*-
#
# HPX - dashboard
#
# Copyright (c) 2020 - ETH Zurich
# All rights reserved
#
# SPDX-License-Identifier: BSD-3-Clause

"""
"""


from bokeh.layouts import row, column
from bokeh.models import AutocompleteInput, Select, TextInput, RadioGroup, Div, Button

from .base import BaseWidget, empty_placeholder
from ..data import DataAggregator, format_instance
from ...common.constants import counternames


class DataCollectionSelect(BaseWidget):
    """Produces a widget that shows all the current and past data collection instances
    in the form of a Select."""

    def __init__(self, doc, callback, refresh_rate=500, **kwargs):
        """Produces a widget that shows all the current and past data collection instances
        in the form of a Select.

        Arguments
        ---------
        doc : Bokeh Document
            bokeh document for auto-updating the widget
        callback : function(collection: DataCollection)
            callback for notifying when the user selects a certain data collection
        refresh_rate : int
            refresh rate at which the Select refreshes and checks for new data collections (in ms)
        **kwargs
            arguments for the bokeh Select widget
        """
        self._defaults_opts = dict(width=250)
        self._defaults_opts.update((key, value) for key, value in kwargs.items())

        super().__init__(doc, callback, refresh_rate=refresh_rate)
        self._root = Select(
            title="Select run",
            name=f"Select run_{BaseWidget.instance_num}",
            options=self._generate_options(),
            **self._defaults_opts,
        )
        self._root.on_change("value", self._on_change_select)

    def _generate_options(self):
        data_collection_list = ["Most recent"]
        for i, run in reversed(list(enumerate(DataAggregator().data))):

            if i == DataAggregator().current_run:
                data_collection_list.append(f"Run {i} (live)")
            else:
                data_collection_list.append(f"Run {i}")

        return data_collection_list

    # Notify the user for a possible change in selection
    def _on_change_select(self, attr, old, new):
        if new != "Most recent":
            run_id = int(new.split()[1])
            data = DataAggregator().data
            self._callback(data[run_id])
        else:
            self._callback(None)

    # Update the Select in case there are new runs
    def update(self):
        options = self._generate_options()
        if options != self._root.options:
            self._root.options = self._generate_options()


class SelectCustomLine(BaseWidget):
    """Produces a widget for selecting a custom line (counter)"""

    def __init__(self, doc, idx, plots, callback=None, refresh_rate=500, collection=None, **kwargs):
        super().__init__(
            doc, callback=callback, refresh_rate=refresh_rate, collection=collection, **kwargs
        )

        self._countername_autocomplete = AutocompleteInput(
            name=f"Autocomplete_{BaseWidget.instance_num}",
            title="Countername:",
            completions=counternames,
            width=200,
        )

        self._collection_widget = DataCollectionSelect(doc, self._set_collection, width=120)
        self._selected_collection = None

        self._name = f"Line {idx}"
        self._name_edit = TextInput(title="Change name:", value=self._name, width=150)
        self._name_edit.on_change("value", self._change_name)
        self._title = Div(text=f"<h3>{self._name}</h3>")

        self._delete = Button(label="Remove", width=70, button_type="danger")
        self._delete.on_click(lambda: callback(idx))
        self._to_plot = Select(options=plots, value=plots[0], title="To plot:", width=70)

        # Instance infos
        self._locality_input = TextInput(title="Locality #id:", value="0", width=70)
        self._locality_select = Select(options=[], title="Locality #id:", value="0", width=70)
        self._worker_id = TextInput(title="Worker #id:", width=70, value="0")
        self._pool = TextInput(title="Pool name:", width=70)
        self._pool_select = Select(options=[], title="Pool name:", width=70)
        self._is_total = RadioGroup(labels=["Yes", "No"], active=0, width=30)
        self._is_total.on_change("active", self._change_is_total)

        self._root = column(
            row(self._title, self._name_edit),
            self._delete,
            row(
                self._to_plot,
                self._collection_widget.layout(),
                self._countername_autocomplete,
                self._locality_input,
                self._pool,
                row(Div(text="Is total?"), self._is_total),
                empty_placeholder(),
            ),
        )

    def _change_name(self, old, attr, new):
        self._name = new
        self._title.text = f"<h3>{new}</h3>"

    def _change_is_total(self, old, attr, new):
        if new:
            self._root.children[2].children[6] = self._worker_id
            self._pool.value = "default"
            if "default" in self._pool_select.options:
                self._pool_select.value = "default"
        else:
            self._pool.value = ""
            if "No pool" in self._pool_select.options:
                self._pool_select.value = "No pool"
            self._root.children[2].children[6] = empty_placeholder()

    def _set_collection(self, collection):
        self._selected_collection = collection
        if collection:
            self._countername_autocomplete.completions = collection.get_counter_names()
            self._locality_select.options = collection.get_localities()
            self._pool_select.options = [
                "No pool" if not pool else pool
                for pool in collection.get_pools(self._locality_input.value)
            ]
            if "No pool" in self._pool_select.options:
                self._pool_select.value = "No pool"

            self._root.children[2].children[3] = self._locality_select
            self._root.children[2].children[4] = self._pool_select
        else:
            self._countername_autocomplete.completions = counternames
            self._root.children[2].children[3] = self._locality_input
            self._root.children[2].children[4] = self._pool

    def properties(self):
        """Returns a tuple containing all the information about the custom counter line.

        In order, returns:
            id of the plot
            collection object or None
            countername of the line
            instance
        """
        plot_id = int(self._to_plot.value.split()[1])

        countername = self._countername_autocomplete.value
        if not self._countername_autocomplete.value:
            countername = self._countername_autocomplete.value_input

        pool = None
        locality = "0"
        if self._selected_collection:
            locality = self._locality_select.value
            if self._pool_select.value != "No pool":
                pool = self._pool_select.value
        else:
            locality = self._locality_input.value
            if self._pool.value:
                pool = self._pool.value

        is_total = True
        if self._is_total.active == 1:
            is_total = False

        worker_id = None
        if is_total:
            worker_id = "total"
        else:
            worker_id = self._worker_id.value

        instance = format_instance(locality, pool, worker_id)

        return plot_id, self._selected_collection, countername, instance, self._name

    def set_plots(self, plots):
        self._to_plot.options = plots
        if self._to_plot.value not in plots:
            self._to_plot.value = plots[0]
