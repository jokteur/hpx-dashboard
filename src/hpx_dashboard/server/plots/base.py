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
from itertools import cycle

from bokeh.plotting import Figure
from bokeh import palettes

default_colors = [
    "#a6cee3",
    "#1f78b4",
    "#d93b43",
    "#999d9a",
    "#e08d49",
    "#eaeaea",
    "#f1d4Af",
    "#599d7A",
]


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
    return [palette[hash(n) % len(palette)] for n in names]


class BasePlot(metaclass=ABCMeta):
    """"""

    def __init__(self, doc, title, refresh_rate=500):
        """"""
        self.layout = None
        self.title = title
        self.buffer = None
        self.refresh_rate = refresh_rate
        self.doc = doc

    def start_update(self):
        self.doc.add_periodic_callback(self.update, self.refresh_rate)

    def stop_update(self):
        self.doc.remove_periodic_callback(self.update)

    def update(self):
        pass

    def plot(self):
        return self.layout
