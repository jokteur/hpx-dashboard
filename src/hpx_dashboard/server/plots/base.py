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

from bokeh.plotting import Figure

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


def get_colors(palette, funcs):
    """"""
    from bokeh import palettes
    from bisect import bisect_left
    import random
    from itertools import cycle

    unique_funcs = list(sorted(set(funcs)))

    n_funcs = len(unique_funcs)
    palette_lookup = palettes.all_palettes[palette]
    keys = list(sorted(palette_lookup.keys()))
    index = keys[min(bisect_left(keys, n_funcs), len(keys) - 1)]
    palette = palette_lookup[index]
    # Some bokeh palettes repeat colors, we want just the unique set
    palette = list(set(palette))
    if len(palette) > n_funcs:
        # Consistently shuffle palette - prevents just using low-range
        random.Random(42).shuffle(palette)
    color_lookup = dict(zip(unique_funcs, cycle(palette)))
    return [color_lookup[n] for n in funcs]


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
