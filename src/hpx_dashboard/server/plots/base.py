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

from abc import ABCMeta
import random
import hashlib
import time

from bokeh.plotting import Figure
from bokeh import palettes


def get_figure_options():
    """"""
    o = Figure.properties()
    o.add("tools")
    return o


def get_colors(palette, names, shuffle=True):
    """"""
    palette_lookup = palettes.all_palettes[palette]

    # Take the biggest palette available
    max_key = max(list(sorted(palette_lookup.keys())))
    palette = palette_lookup[max_key]

    # Some bokeh palettes repeat colors, we want just the unique set
    palette = list(set(palette))

    if shuffle:
        # Consistently shuffle palette - prevents just using low-range
        random.Random(42).shuffle(palette)

    # Quick and dirty hash table
    return [
        palette[int(hashlib.sha256(n.encode("utf-8")).hexdigest(), 16) % len(palette)]
        for n in names
    ]


class BasePlot(metaclass=ABCMeta):
    """"""

    def __init__(self, doc, refresh_rate=500):
        """"""
        self._root = None
        self._buffer = None
        self._refresh_rate = refresh_rate
        self._doc = doc

    def start_update(self):
        self._doc.add_periodic_callback(self.update, self._refresh_rate)

    def stop_update(self):
        self._doc.remove_periodic_callback(self.update)

    def update(self):
        pass

    def plot(self):
        return self._root


class ThrottledEvent:
    _callback = None
    _lastcall = 0
    _numcalls = 0
    _total_time = 0

    def __init__(self, doc, fire_rate=None, refresh_rate=50):
        """fire_rate in ms"""
        self._doc = doc
        self._doc.add_periodic_callback(self._fire_event, refresh_rate)

        if fire_rate:
            self._dynamic_fire_rate = False
            self._fire_rate = fire_rate / 1000
        else:
            self._dynamic_fire_rate = True
            self._fire_rate = 0.05

    def add_event(self, callback):
        self._callback = callback
        self._lastcall = time.time()
        if time.time() - self._lastcall > self._fire_rate:
            self._doc.add_next_tick_callback(self._call_and_measure)

    def _call_and_measure(self):
        self._numcalls += 1
        self._lastcall = time.time()

        prev = time.time()
        self._callback()
        self._callback = None
        self._total_time += time.time() - prev

        if self._dynamic_fire_rate:
            # Use buffer (10)
            self._fire_rate = self._total_time / self._numcalls

    def _fire_event(self):
        if self._callback and time.time() - self._lastcall > self._fire_rate:
            self._doc.add_next_tick_callback(self._call_and_measure)
            self._lastcall = time.time()
