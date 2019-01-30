#!/usr/bin/python

import logging as trace
import fotonowy
#import komunikacja as fotokom
import time
import re
import numpy as np

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
# implement the default mpl key bindings
from matplotlib.backend_bases import key_press_handler


from matplotlib.figure import Figure

import matplotlib
matplotlib.use('TkAgg')

from numpy import arange, sin, pi
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
# implement the default mpl key bindings
from matplotlib.backend_bases import key_press_handler


from matplotlib.figure import Figure

import sys
if sys.version_info[0] < 3:
    import Tkinter as Tk
else:
    import tkinter as Tk



def meas_ref():
    potentiostat.io_set(1)
    time.sleep(.1)
    result = potentiostat.get_current_value()
    potentiostat.io_clear(1)
    return result

def meas_sum():
    potentiostat.io_set(4)
    time.sleep(.1)
    result = potentiostat.get_current_value()
    potentiostat.io_clear(4)
    return result

def meas_diff():
    potentiostat.io_set(3)
    time.sleep(.1)
    result=potentiostat.get_current_value()
    potentiostat.io_clear(3)
    return result





if __name__ == "__main__":
    trace.basicConfig(format="[%(asctime)s](%(module)s:%(funcName)s:%(lineno)d) %(message)s",
                      datefmt='%I:%M:%S',
                      level=trace.INFO)

    root = Tk.Tk()
    root.wm_title("Embedding in TK")

    f = Figure(figsize=(5, 4), dpi=100)
    a = f.add_subplot(111)


    kom = fotonowy.Communication()
    kom.connect( port_name="/dev/ttyUSB0")
    monochromator=fotonowy.Monochromator(kom)
    potentiostat=fotonowy.Potentiostat(kom)


    monochromator.shutter_open()
    print("Range "+ str(potentiostat.set_range(4)))
    potentiostat.set_avg(1)
    #potentiostat.set_freq(0)
    #kom.write_command_stdr("CEOFF 3", 249)


    canvas = FigureCanvasTkAgg(f, master=root)
    canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
    canvas._tkcanvas.pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)

    toolbar = NavigationToolbar2TkAgg(canvas, root)
    toolbar.update()

    X=np.arange(-1,1,.1)
    Y=np.zeros_like(X)

    plt, = a.plot(X, Y)
    canvas.show()

    for i, x in enumerate(X):

        potentiostat.set_volt(x, 51, 1)
        Y[i] = potentiostat.meas_lockin_a(1)
        print(Y[i])
        plt.set_ydata(Y)

        a.relim()
        a.autoscale_view(True, True, True)
        canvas.draw()



    # a tk.DrawingArea



    def on_key_event(event):
        print('you pressed %s' % event.key)
        key_press_handler(event, canvas, toolbar)


    canvas.mpl_connect('key_press_event', on_key_event)


    def _quit():
        root.quit()  # stops mainloop
        root.destroy()  # this is necessary on Windows to prevent
        # Fatal Python Error: PyEval_RestoreThread: NULL tstate


    button = Tk.Button(master=root, text='Quit', command=_quit)
    button.pack(side=Tk.BOTTOM)

    Tk.mainloop()
    # If you put root.destroy() here, it will cause an error if
    # the window is closed with the window manager.


    kom.disconnect()