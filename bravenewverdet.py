#!/usr/bin/python

import logging as trace
import fotonowy
#import komunikacja as fotokom
import time
import re
import numpy as np
import matplotlib.pyplot as plt




if __name__ == "__main__":
    trace.basicConfig(format="[%(asctime)s](%(module)s:%(funcName)s:%(lineno)d) %(message)s",
                      datefmt='%I:%M:%S',
                      level=trace.ERROR)
    kom = fotonowy.Communication()
    kom.connect( port_name="/dev/ttyUSB0")
    monochromator=fotonowy.Monochromator(kom)
    potentiostat=fotonowy.Potentiostat(kom)


    #monochromator.shutter_open()


    #kom.write_command_stdr("START", 249)
    #time.sleep(0.1)
    #kom.write_command_stdr("STOP", 249)
    #time.sleep(1)
    #print(kom.data)
    #for i in range(10):
    #   print(potentiostat.get_current_value()*1e9)

    print(kom.write_command_ret("IN 1", 250))
    print(potentiostat.io_read(1))
    potentiostat.io_set(1)
    time.sleep(1)
    potentiostat.io_clear(1)

    kom.disconnect()
