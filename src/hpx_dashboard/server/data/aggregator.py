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
from typing import Union

from ...common.singleton import Singleton
from ...common.logger import Logger
from .collection import DataCollection


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

        if import_path:
            self._import_session(import_path)
        elif auto_save:
            self._create_session(save_path)

    def _import_session(self, path):
        """Imports a previous session into the aggregator.

        If the import failed, False is returned. If sucessful, True is returned.
        """
        self.path = path
        Logger().info(f"Succesfully imported data from {path}.")
        return False

    def _create_session(self, path):
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
