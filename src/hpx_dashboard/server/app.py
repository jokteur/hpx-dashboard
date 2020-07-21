from bokeh.layouts import column

# from bokeh.models import Button
# from bokeh.palettes import RdYlBu3
# from bokeh.plotting import figure

from .plots.threads import Threads2, Memory


def app(doc):
    threads_count = Threads2(doc)
    memory = Memory(doc)

    # put the button and plot in a layout and add to the document
    p = column(threads_count.get_plot(), memory.get_plot())
    doc.add_root(p)
    return p
