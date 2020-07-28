# -*- coding: utf-8 -*-
#
# HPX - dashboard
#
# Copyright (c) 2020 - ETH Zurich
# All rights reserved
#
# SPDX-License-Identifier: BSD-3-Clause

"""The data aggregator module is for storing any data coming from one or multiple hpx program runs.
"""

from datetime import datetime

from bokeh.layouts import row, column
from bokeh.models.widgets import AutocompleteInput, Select, Div, Button
import panel as pn

from ..data import DataAggregator, format_instance

# from ..plots import PlotGenerator


def empty_placeholder():
    return Div(text=" ")


class BaseWidget:
    """"""

    instance_num = 0

    def __init__(self, doc, callback, refresh_rate=500, **kwargs):
        """"""
        BaseWidget.instance_num += 1
        self.doc = doc
        self.widget = empty_placeholder()
        self.refresh_rate = refresh_rate
        self.callback = callback
        self.callback_object = doc.add_periodic_callback(self._update_widget, refresh_rate)

    def __del__(self):
        print("I am deleting")
        self.doc.remove_periodic_callback(self.callback_object)

    def _update_widget(self):
        pass


class SelectDataCollection(BaseWidget):
    """Produces a widget that shows all the current and past data collection instances
    in the form of a Select."""

    def __init__(self, doc, callback, refresh_rate=500, width=450, **kwargs):
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
        super().__init__(doc, callback, refresh_rate=refresh_rate)
        self.widget = Select(
            name=f"Select run_{BaseWidget.instance_num}",
            options=self._generate_options(),
            width=width,
            **kwargs,
        )
        self.widget.on_change("value", self._on_change_select)

    def _generate_options(self):
        data_collection_list = ["Select run"]
        for i, run in reversed(list(enumerate(DataAggregator().data))):
            begin_time = datetime.fromtimestamp(int(run["begin-time"]))

            if i == DataAggregator().current_run:
                data_collection_list.append(f"Run {i} (current). Begin: {begin_time}")
            else:
                end_time = "N/A"
                if run["end-time"]:
                    end_time = datetime.fromtimestamp(int(run["end-time"]))
                data_collection_list.append(f"Run {i} Begin: {begin_time}; End: {end_time}")

        return data_collection_list

    # Notify the user for a possible change in selection
    def _on_change_select(self, attr, old, new):
        if new != "Select run":
            run_id = int(new.split()[1])
            self.callback(DataAggregator().data[run_id]["data"])
        else:
            self.callback(None)

    # Update the Select in case there are new runs
    def _update_widget(self):
        self.widget.options = self._generate_options()


class MultiCounterNameSelect(BaseWidget):
    """Produces a widget that shows all the current and past data collection instances
    in the form of a Select."""

    def __init__(
        self,
        doc,
        callback,
        collection,
        refresh_rate=500,
        width=450,
        select_kwargs={},
        autocomplete_kwargs={},
    ):
        """Produces a widget that shows all the available counters in a particular DataCollection.

        Arguments
        ---------
        doc : Bokeh Document
            bokeh document for auto-updating the widget
        callback : function(collection: DataCollection)
            callback for notifying when the user selects a certain data collection
        collection : DataCollection
            instance of data collection to search for the available counters
        refresh_rate : int
            refresh rate at which the Select refreshes and checks for new data collections (in ms)
        select_opt : dict
            arguments for the bokeh Select
        autocomplete_opt : dict
            arguments for the bokeh AutoCompleteInput
        """
        super().__init__(doc, callback, refresh_rate=refresh_rate)
        self.collection = collection
        self.previous_change = None

        self.widget = pn.widgets.MultiChoice(
            name=f"Multi_select counter_{BaseWidget.instance_num}",
            options=self._generate_options(),
            width=width,
            **select_kwargs,
        )

        self.widget.on

    def _generate_options(self):
        if self.collection:
            return self.collection.get_counter_names()
        else:
            return []

    # Notify the user for a possible change in selection
    def _on_change(self, attr, old, new):
        if self.previous_change != new:
            self.previous_change = new
            if new != "Select name":
                self.callback(new)
                self.autocomplete.value = new
                self.select.value = new
            else:
                self.previous_change = None
                self.autocomplete.value = None
                self.select.value = "Select name"
                self.callback(None)

    # Update the Select and autocomplete in case there are new runs
    def _update_widget(self):
        self.widget.options = self._generate_options()


class SelectCounterName(BaseWidget):
    """Produces a widget that shows all the current and past data collection instances
    in the form of a Select."""

    def __init__(
        self,
        doc,
        callback,
        collection,
        refresh_rate=500,
        width=450,
        select_kwargs={},
        autocomplete_kwargs={},
    ):
        """Produces a widget that shows all the available counters in a particular DataCollection.

        Arguments
        ---------
        doc : Bokeh Document
            bokeh document for auto-updating the widget
        callback : function(collection: DataCollection)
            callback for notifying when the user selects a certain data collection
        collection : DataCollection
            instance of data collection to search for the available counters
        refresh_rate : int
            refresh rate at which the Select refreshes and checks for new data collections (in ms)
        select_opt : dict
            arguments for the bokeh Select
        autocomplete_opt : dict
            arguments for the bokeh AutoCompleteInput
        """
        super().__init__(doc, callback, refresh_rate=refresh_rate)
        self.collection = collection
        self.previous_change = None

        self.select = Select(
            name=f"Select counter__{BaseWidget.instance_num}",
            options=["Select name"] + self._generate_options(),
            width=width,
            **select_kwargs,
        )
        self.autocomplete = AutocompleteInput(
            name=f"Autocomplete_{BaseWidget.instance_num}",
            completions=self._generate_options(),
            width=width,
            **autocomplete_kwargs,
        )
        self.select.on_change("value", self._on_change)
        self.autocomplete.on_change("value", self._on_change)

        self.widget = row(self.select, self.autocomplete)

    def _generate_options(self):
        if self.collection:
            return self.collection.get_counter_names()
        else:
            return []

    # Notify the user for a possible change in selection
    def _on_change(self, attr, old, new):
        if self.previous_change != new:
            self.previous_change = new
            if new != "Select name":
                self.callback(new)
                self.autocomplete.value = new
                self.select.value = new
            else:
                self.previous_change = None
                self.autocomplete.value = None
                self.select.value = "Select name"
                self.callback(None)

    # Update the Select and autocomplete in case there are new runs
    def _update_widget(self):
        self.select.options = ["Select name"] + self._generate_options()
        self.autocomplete.completions = self._generate_options()


class SelectInstance(BaseWidget):
    """Produces a widget that shows all the current and past data collection instances
    in the form of a Select."""

    def __init__(
        self,
        doc,
        callback,
        collection,
        refresh_rate=500,
        width=450,
        select_locality_kwargs={},
        select_instance_kwargs={},
    ):
        """Produces a widget that shows all the available counters in a particular DataCollection.

        Arguments
        ---------
        doc : Bokeh Document
            bokeh document for auto-updating the widget
        callback : function(collection: DataCollection)
            callback for notifying when the user selects a certain data collection
        collection : DataCollection
            instance of data collection to search for the available counters
        refresh_rate : int
            refresh rate at which the Select refreshes and checks for new data collections (in ms)
        select_locality_kwargs : dict
            arguments for the bokeh Select locality widget
        select_instance_kwargs : dict
            arguments for the bokeh Select instance widget
        """
        super().__init__(doc, callback, refresh_rate=refresh_rate)
        self.collection = collection

        self.select_locality = Select(
            name=f"Select locality_{BaseWidget.instance_num}",
            options=self._generate_localities(),
            width=width,
            **select_locality_kwargs,
        )

        self.select_instance = Select(
            name=f"Select instance_{BaseWidget.instance_num}",
            options=self._generate_instances(),
            width=width,
            **select_instance_kwargs,
        )
        self.select_locality.on_change("value", self._on_change_locality)
        self.select_instance.on_change("value", self._on_change_instance)

        self.widget = row(self.select_locality, empty_placeholder())

    def _generate_localities(self):
        prelude = ["Select locality"]
        if self.collection:
            return prelude + list(self.collection.get_localities())
        else:
            return prelude

    def _generate_instances(self, locality="Select locality"):
        prelude = ["Select instance"]
        if self.collection and locality.strip() and locality != "Select locality":
            instances_names = []
            for pool in self.collection.get_pools(locality):
                if pool == "total":
                    instances_names.append(pool)
                elif pool:
                    for worker_thread in self.collection.get_worker_threads(locality, pool):
                        instances_names.append(f"Pool #{pool} ; Worker-thread #{worker_thread}")
            return prelude + instances_names
        else:
            return prelude

    def _on_change_locality(self, attr, old, new):
        if new != "Select locality":
            self.select_instance.options = self._generate_instances(new)
            self.widget.children[1] = self.select_instance
        else:
            self.select_instance.value = "Select instance"
            self.widget.children[1] = empty_placeholder()

    # Notify the user for a possible change in selection
    def _on_change_instance(self, attr, old, new):
        if new != "Select instance":
            if new == "total":
                self.callback(format_instance(self.select_locality.value))
            else:
                split = new.split()
                pool = split[1][1:]
                worker_thread = split[4][1:]
                self.callback(
                    format_instance(self.select_locality.value, pool, worker_thread, False)
                )
        else:
            self.callback(None)

    def _update_widget(self):
        self.select_instance.options = self._generate_instances(self.select_locality.value)
        self.select_locality.options = self._generate_localities()


class SelectCounter(BaseWidget):
    """Produces a widget that allows for selecting a particular counter
    and instance in a certain run."""

    def __init__(self, doc, callback, refresh_rate=500, **kwargs):
        """Produces a widget that allows for selecting a particular counter and instance in a certain run.

        Arguments
        ---------
        doc : Bokeh Document
            bokeh document for auto-updating the widget
        callback : function(collection: DataCollection)
            callback for notifying when the user selects a certain data collection
        collection : DataCollection
            instance of data collection to search for the available counters
        refresh_rate : int
            refresh rate at which the widget refreshes itself
        **kwargs
            arguments for the bokeh Select widgets
        """
        super().__init__(doc, callback, refresh_rate=refresh_rate)

        self.select_run = SelectDataCollection(
            doc, self._update_run, width=450, title="Select run", **kwargs
        )
        self.select_counter_name = None
        self.select_instance = None
        self.widget = column(self.select_run.widget, empty_placeholder(), empty_placeholder())

    def _update_run(self, collection):
        if collection:
            self.select_counter_name = SelectCounterName(
                self.doc,
                self.callback,
                collection,
                self.refresh_rate,
                select_kwargs={"title": "Select the counter name"},
                autocomplete_kwargs={"title": "or type in the counter name"},
            )
            self.select_instance = SelectInstance(
                self.doc,
                self.callback,
                collection,
                self.refresh_rate,
                select_locality_kwargs={"title": "Select the locality"},
                select_instance_kwargs={"title": "Select the instance"},
            )
            self.widget.children[1] = self.select_counter_name.widget
            self.widget.children[2] = self.select_instance.widget
        else:
            self.select_counter_name = None
            self.select_instance = None
            self.widget.children[1] = empty_placeholder()
            self.widget.children[2] = empty_placeholder()


class PlotGeneratorWidget(BaseWidget):
    """"""

    def __init__(self, doc, callback, refresh_rate=500, **kwargs):
        """Produces a widget that allows for selecting a particular counter and instance in a certain run.

        Arguments
        ---------
        doc : Bokeh Document
            bokeh document for auto-updating the widget
        callback : function(collection: DataCollection)
            callback for notifying when the user selects a certain data collection
        collection : DataCollection
            instance of data collection to search for the available counters
        refresh_rate : int
            refresh rate at which the widget refreshes itself
        **kwargs
            arguments for the bokeh Select widgets
        """
        super().__init__(doc, callback, refresh_rate=refresh_rate)

        # self.plot = PlotGenerator(doc, "Line plot", width=980, height=500)

        self.add_button = Button("Add counter")
        self.ok_button = Button("Ok")
        self.add_button.on_click(self._add_button_click)
        self.ok_button.on_click(self._ok_button_click)

        self.selected_locality = None
        self.selected_collection = None
        self.selected_instance = None

        self.widget = column(self.add_button, empty_placeholder(), self.plot.get_plot())

    def _selected(self, out):
        print(out)

    def _add_button_click(self):
        self.widget.children[1] = column(SelectCounter(self.doc, self._selected), self.ok_button)

    def _ok_button_click(self):
        pass
