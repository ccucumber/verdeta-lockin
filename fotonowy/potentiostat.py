import logging as trace
import numpy as np
import time
import re

# Note: all logging (trace) messages
# are in debug mode in this file


class Potentiostat:
    address = 250
    kom = None
    range_multiplier = 1e-9
    time_multiplier = 5e-3
    _freq=1000
    _avg=20
    _sample_number=0


    def __init__(self, kom):
        self.kom=kom

    def set_address(self, value):
        self.address=value

    def set_kom(self, value):
        self.kom=value


    def get_current_value(self):
        output = self.kom.write_command_ret("CURR?", self.address-1)
        if output == None:
            return None
        # we do expect respond in format "<value><range>", i.e. "5.367nA"

        # # sometimes device send some strange respond (numbers with additional error chars)
        # # using regexp to leave only numeric values.
        # # 0-9 can be replaced with \d because that matches all numerical characters,
        # # and the '.' is necessary because the . character is a wildcard.
        # value = float(re.sub('[^\d.]', '', output[:-2]))
        #
        # return_value = value * {'nA': 1e-9,
        #                         'uV': 1e-6,
        #                         'mA': 1e-3,
        #                         }.get(output[-2:], 1)
        value=float(output[:-1])  #Markas poprawkas

        trace.debug("Current value: " + str(return_value) + " A")

        return return_value

    # pass values in Hz
    def set_range(self, value):

        if value>=0 and value <= 6:
            self.range_multiplier = {6: 1e-2,
                                     5: 1e-3,
                                     4: 1e-4,
                                     3: 1e-5,
                                     2: 1e-6,
                                     1: 1e-7,
                                     0: 1e-8
                                     }.get(value)

            trace.debug("Set RANGE " + str(int(value)))
            self.kom.write_command_stdr("RANGE " + str(int(value)), self.address-1)
        else:
            trace.error("FREQ not in range")
        return self.range_multiplier

    def get_range(self, pin):

        output=self.kom.write_command_stdr("RANGE?", self.address)
        self.range_multiplier = {7: 1e-2,
                                6: 1e-3,
                                5: 1e-4,
                                4: 1e-5,
                                3: 1e-6,
                                2: 1e-7,
                                1: 1e-8
                                }.get(int(output))
        return self.range_multiplier





    # pass values in volts
    def set_volt(self, value, f=None, a=None):

        if value>-5 and value < 5:
            command = "VOLT " + str(int(value*1000.))
            if f is not None:
                command = command + " " + str(int(f))
            if a is not None:
                command = command + " " + str(int(a*1000.))

            trace.debug("Set " + command)
            self.kom.write_command_stdr(command, self.address-1)
        else:
            trace.error("VOLT not in range")


    # pass values in Hz
    def set_freq(self, value):

        if value>=0 and value <= 1000:
            self._freq = value
            self.time_multiplier = 1. / self._freq * self._avg
            trace.debug("Set FREQ " + str(int(value)))
            self.kom.write_command_stdr("FREQ " + str(int(value)), self.address-1)
        else:
            trace.error("FREQ not in range")

    def set_avg(self, value):

        if value >= -1 and value <= 1000:
            command = "AVG " + str(int(value))
            self._avg=value
            self.time_multiplier = 1. / self._freq * self._avg
            trace.debug("Set " + command)
            self.kom.write_command_stdr(command, self.address-1)
        else:
            trace.error("AVG not in range")


    def io_read(self, pin):

        output=self.kom.write_command_stdr("IN " + str(int(pin)), self.address)
        return int(output)

    def io_set(self,pin):
        self.kom.write_command_stdr("SET " + str(int(pin)), self.address)

    def io_clear(self,pin):
        self.kom.write_command_stdr("CLR " + str(int(pin)), self.address)


    def meas_lockin_a(self,sample_time):

        self._sample_number+=1

        self.kom.data=[]


        self.kom.write_command_stdr("RUN", 249)

        time.sleep(sample_time)
        self.kom.write_command_stdr("STOP", 249)
        time.sleep(.002)
        trace.debug("Data in buffer: "+str(len(self.kom.data)))
        first=None
        pha=0
        s = np.array(self.kom.data)[:, (0, 2)]
        self.sig = s
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

        first = s[0, 1]
        trace.debug("Start index: "+str(start))
        start = 0

        for i in range(len(s)):
            if s[i, 1] != first:
                first=s[i,1]
                pha+=1
                if pha==2:
                    pha=0
                    if mid-start < 1 + i-mid and mid-start >  i-mid - 1:
                        start=i
                        stop=i
                        osc_count+=1
                        trace.debug("Found osc prd="+str(start-mid))
                    else:
                        trace.error("Inconsistent prd: "+str(start)+" "+str(mid)+" "+str(stop))
                mid = i
        trace.debug("Oscillations: "+str(osc_count)+" Samples left: "+str(len(s)-stop))
        #stop=len(s)
        mult=2*(s[:stop,1]-0.5)
        sig=s[:stop,0]

        # save data to text file

        timestamp = time.strftime("%Y%m%d-%H%M%S")

        #np.savetxt('probe_' + str(osc_count) + "_"+ timestamp + '.txt',  np.c_[sig,mult,s[:stop,1]], header='U[V] Status')
        np.savetxt('raw_a'+ str(self._sample_number)+'.txt', np.c_[sig, mult, s[:stop, 1]],
                   header='U[V] Multiplier Status_bit')



        return np.dot(sig,mult)/stop


    def meas_lockin_d(kom,t):
        self.kom.write_command_stdr("LOCKIN 60 3", 250)
        self.kom.data=[]
        self.kom.write_command_stdr("START", 249)
        time.sleep(t)
        self.kom.write_command_stdr("STOP", 249)
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

        # save data to text file

        np.savetxt('raw_d' + str(self._sample_number) + '.txt', np.c_[sig, mult, s[:stop, 1]],
                   header='U[V] Multiplier Status_bit')

        return np.dot(sig,mult)/stop