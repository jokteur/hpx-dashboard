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

import os
import time
import json
import csv
from typing import Union

import pandas as pd

from ...common.singleton import Singleton
from ...common.logger import Logger
from .collection import DataCollection, format_instance


class DataAggregator(metaclass=Singleton):
    """DataAggregator is a singleton that store all the data from all the runs."""

    def __init__(self, auto_save=True, save_path="", import_path=""):
        """Initializes the data of the server."""
        self.data = []
        self.current_run = None
        self.last_run = None
        self.current_data: Union[DataCollection, None] = None
        self.dummy_counter = 0

        self.session = str(int(time.time()))
        self.auto_save = auto_save

        if not auto_save:
            Logger().info("No data is will be auto-saved during this session.")

        success = False
        if import_path:
            success = self.import_session(import_path)
            if not success:
                Logger().warning(f"Data was not imported from {import_path}.")

        if auto_save and not success:
            self.create_session(save_path)

    def import_session(self, path):
        """Imports a previous session into the aggregator.

        If the import failed, False is returned. If sucessful, True is returned.
        """

        json_file = None
        try:
            json_file = open(os.path.join(path, "session_metadata.json"), "r")
        except OSError as e:
            Logger().error(
                f"Could not open `session_metadata.json` from {path}."
                f" The following error occured {e.strerror}"
            )
            return False

        metadata = json.load(json_file)

        if "session_id" not in metadata:
            Logger().error("Could not find `session_id` in session_metadata.json.")
            return False

        if "collections" not in metadata:
            Logger().error("Could not find `collections` in session_metadata.json.")
            return False

        if not isinstance(metadata["collections"], list):
            Logger().error("`collections` in session_metadata.json should be a list.")
            return False

        collections = []
        for collection in metadata["collections"]:
            if not isinstance(collection, dict):
                Logger().error("A collection in session_metadata.json should be a dict.")
                return False
            if "start" not in collection or "end" not in collection or "id" not in collection:
                Logger().error("Missing keywords in collection (should be start, end, id).")
                return False

            collection_obj = DataCollection()
            collection_obj.set_start_time(collection["start"])
            collection_obj.set_end_time(collection["end"])

            Logger().info("Importing collection " + str(collection["id"]) + " into session...")

            counter_path = os.path.join(path, "counter_data." + str(collection["id"]) + ".csv")
            task_data_path = os.path.join(path, "task_data." + str(collection["id"]) + ".csv")
            try:
                open(counter_path, "r")
            except OSError as e:
                Logger().error(f"Could not open {counter_path}: {e.strerror}.")
            try:
                open(counter_path, "r")
            except OSError as e:
                Logger().error(f"Could not open {task_data_path}: {e.strerror}.")

            # For counter data, reading a csv line by line is faster than opening the csv file
            # in a pd DataFrame and reading it line by line.
            # Because the collection object is building a tree-like structure, we can not simply
            # copy the data of the csv directly into the counter data of the collection.
            # This method is fast enough for general purpose
            with open(counter_path, "r") as csvfile:
                reader = csv.reader(csvfile, delimiter=",")
                next(reader)
                for row in reader:
                    if len(row) != 10:
                        Logger().error(f"Csv file {counter_path} should have 10 columns.")
                        return False
                    (
                        _,
                        sequence_number,
                        timestamp,
                        timestamp_unit,
                        value,
                        value_unit,
                        countername,
                        locality,
                        pool,
                        thread,
                    ) = row

                    collection_obj.add_line(
                        countername,
                        format_instance(locality, pool, thread),
                        "",
                        sequence_number,
                        timestamp,
                        timestamp_unit,
                        value,
                        value_unit,
                    )

            # However, for task data, which can get quite large, adding row by row will take a long
            # time. This is why a special import task data from dataframe has been built in the
            # DataCollection object.
            task_data = pd.read_csv(task_data_path)
            collection_obj.import_task_data(task_data)

            collections.append(collection_obj)

        self.path = path
        self.session = metadata["session_id"]
        self.data = collections
        self.last_run = len(self.data) - 1
        self.current_run = None
        self.current_data = None
        self.metadata = metadata
        self.metadata_path = os.path.join(self.path, "session_metadata.json")
        Logger().info(f"Succesfully imported data from {path}.")
        return True

    def create_session(self, path):
        """Creates a folder with the correct structure for saving sessions.

        hpx_data.<timestamp>/
            session_metadata.json
            counter_data.<timestamp>.csv
            task_data.<timestamp>.csv
            ...
        """
        self.path = os.path.join(path, "hpx_data." + self.session)
        try:
            os.mkdir(self.path)
        except OSError as e:
            Logger().warning(
                f"Could not create the directory {self.path} for auto-saving"
                f" the data because the following error occured: {e.strerror}."
            )
            Logger().warning("No auto-saving is enabled during this session.")
            self.path = None
            return

        self.metadata_path = os.path.join(self.path, "session_metadata.json")
        self.metadata = {"session_id": self.session, "collections": [], "custom_widget_config": {}}
        self._save_metadata()

        Logger().info(f"Session data will be saved in {self.path}")

    def _save_metadata(self):
        if self.path:
            with open(self.metadata_path, "w") as json_file:
                json.dump(self.metadata, json_file)

    def _load_metadata(self):
        if self.path:
            with open(self.metadata_path, "r") as json_file:
                self.metadata = json.load(json_file)

    def set_custom_widget_config(self, widget_config):
        """Saves the state of the custom counter widget to the session."""
        if self.path:
            self.metadata["custom_widget_config"] = widget_config
            self._save_metadata()

    def get_custom_widget_config(self):
        """Returns the custom counter widget config saved in the session in json txt."""
        if self.path:
            self._load_metadata()
            if "custom_widget_config" in self.metadata:
                return json.dumps(self.metadata["custom_widget_config"])
        return None

    def set_counter_infos(self, counter_infos: dict):
        """Sets the counter informations of the current collection.

        If there is no active collection, this function does nothing

        Parameters
        ----------
        counter_infos
            dictionnary of descriptions for each available counter of the hpx application
        """
        if self.current_run is not None:
            self.data[self.current_run].set_counter_infos(counter_infos)

    def get_last_run(self) -> Union[DataCollection, None]:
        """Returns the last active DataCollection.
        If there was no active collection, None is returned.
        """
        if self.last_run is not None:
            return self.data[self.last_run]
        else:
            return None

    def get_live_collection(self):
        """Returns the most recent collection in memory.

        If there is a live collection, then it is returned. Otherwise, the most recent collection
        is returned.
        """
        collection = None
        if self.get_current_run():
            collection = self.get_current_run()
        elif self.get_last_run():
            collection = self.get_last_run()
        return collection

    def get_all_runs(self):
        """Returns all current and past data collection runs"""
        return self.data

    def get_current_run(self):
        """Returns the current active collection.
        If there is no collection going on, then None is returned.
        """
        if self.current_data:
            return self.current_data
        else:
            return None

    def finalize_current_collection(self, end_time: float) -> None:
        """Finalizes the current collection of data

        Parameters
        ----------
        end_time
            time of when the collection has finished"""
        self.data[self.current_run].set_end_time(end_time)
        self.last_run = self.current_run
        self.current_data = None
        self.current_run = None

        # Save the collected data
        if self.auto_save and self.path:
            collection = self.data[self.last_run]

            counter_data = collection.export_counter_data()
            task_data = collection.export_task_data()
            start = collection.start_time
            end = collection.end_time

            self.metadata["collections"].append(
                {
                    "start": start,
                    "end": end,
                    "id": int(start),
                }
            )

            counter_data.to_csv(os.path.join(self.path, f"counter_data.{int(start)}.csv"))
            task_data.to_csv(os.path.join(self.path, f"task_data.{int(start)}.csv"))

            self._save_metadata()

    def new_collection(self, start_time: float) -> None:
        """Adds a new DataCollection along with a timestamp to the aggregator.

        Parameters
        ----------
        start_time
            time of the beginning of the collection
            (should be sent by the hpx-dashboard agent)
        """
        self.data.append(DataCollection())
        self.data[-1].set_start_time(start_time)
        self.current_run = len(self.data) - 1
        self.current_data = self.data[-1]
