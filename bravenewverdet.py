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

def meas_lockin_d(kom):
    kom.data=[]
    kom.write_command_stdr("START", 249)
    time.sleep(2.2)
    kom.write_command_stdr("STOP", 249)
    time.sleep(.1)
    trace.info("Data in buffer: "+str(len(kom.data)))
    first=None
    pha=0
    s = np.array(kom.data)[:, (0, 3)]
    start=0
    mid=0
    stop=0
    osc_count=0
    for i in range(len(s)):
        if(first is None): first=s[i,1]
        else:
            if s[i,1] != first:
                start=i
                mid=i
                stop=i
                break

    s=s[start:]
    start=0
    first = s[0, 1]
    trace.debug("Start index: "+str(start))

    for i in range(len(s)):
        if s[i, 1] != first:
            first=s[i,1]
            pha+=1
            if pha==2:
                pha=0
                if mid-start == i-mid:
                    start=i
                    stop=i
                    osc_count+=1
                    trace.debug("Found osc prd="+str(start-mid))
                else:
                    trace.error("Inconsistent prd: "+str(start)+" "+str(mid)+" "+str(stop))
            mid = i
    trace.info("Oscillations: "+str(osc_count)+" Samples left: "+str(len(s)-stop))

    mult=2*(s[:stop,1]-0.5)
    sig=s[:stop,0]


    return np.dot(sig,mult)/stop



if __name__ == "__main__":
    trace.basicConfig(format="[%(asctime)s](%(module)s:%(funcName)s:%(lineno)d) %(message)s",
                      datefmt='%I:%M:%S',
                      level=trace.INFO)
    kom = fotonowy.Communication()
    kom.connect( port_name="/dev/ttyUSB0")
    monochromator=fotonowy.Monochromator(kom)
    potentiostat=fotonowy.Potentiostat(kom)


    monochromator.shutter_open()
    print("Range "+ str(potentiostat.set_range(2)))
    potentiostat.set_avg(20)
    potentiostat.set_freq(1000)
    potentiostat.set_volt(2)#,10,3.5)


    for i in range(10):
        kom.write_command_stdr("LOCKIN 200 0", 250)
        print(meas_lockin_d(kom))