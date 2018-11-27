import logging as trace
import re

# Note: all logging (trace) messages
# are in debug mode in this file




class Potentiostat:
    address = 250
    kom = None

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

        # sometimes device send some strange respond (numbers with additional error chars)
        # using regexp to leave only numeric values.
        # 0-9 can be replaced with \d because that matches all numerical characters,
        # and the '.' is necessary because the . character is a wildcard.
        value = float(re.sub('[^\d.]', '', output[:-2]))

        return_value = value * {'nA': 1e-9,
                                'uA': 1e-6,
                                'mA': 1e-3,
                                }.get(output[-2:], 1)
        trace.debug("Current value: " + str(return_value) + " A")
        return return_value


    # pass values in volts
    def set_volt(self, value):

        if value>-5 and value < 5:
            trace.debug("Set VOLT " + str(int(value/1000.)))
            self.kom.write_command_stdr("VOLT " + str(int(value/1000.)), self.address-1)
        else:
            trace.error("VOLT not in range")


    # pass values in Hz
    def set_freq(self, value):

        if value>=0 and value <= 1000:
            if value==0:    trace.debug("Set FREQ 0 - sine lockin mode enabled")
            else:           trace.debug("Set FREQ " + str(int(value)))
            self.kom.write_command_stdr("FREQ " + str(int(value)), self.address-1)
        else:
            trace.error("FREQ not in range")


    def io_read(self, pin):

        output=self.kom.write_command_stdr("IN " + str(int(pin)), self.address)
        return int(output)

    def io_set(self,pin):
        self.kom.write_command_stdr("SET " + str(int(pin)), self.address)

    def io_clear(self,pin):
        self.kom.write_command_stdr("CLR " + str(int(pin)), self.address)


