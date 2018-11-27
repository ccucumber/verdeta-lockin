
#TODO attaching function (e.g from Monochromator class) to async channel in komunikacja
#so incoming async communicate will trigger an event in attached function

# Note: all logging (trace) messages
# are in debug mode in this file




class Monochromator:
    address = 30
    kom = None

    def __init__(self, kom):
        self.kom=kom

    def set_address(self, value):
        self.address=value

    def set_kom(self, value):
        self.kom=value

    # pass values in nanometers
    def set_wavelength(self, value):

        self.kom.write_command_stdr("WAV " + str(int(value*10.)), self.address)

    def shutter_open(self):

        self.kom.write_command_stdr("OPEN", self.address)

    def shutter_close(self):

        self.kom.write_command_stdr("CLOSE", self.address)
