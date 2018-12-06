import serial
import time
import struct
import logging as trace
import threading

class Communication(object):
    data_chars = [b'!', b'"', b'#', b'$', b'%', b'&', b"'", b'(']
    response_timeout = 2 #second
    _handle = serial.Serial()
    _error_counter = 0
    _done = False
    _thread = None

    def __init__(self, address=None):
        # Initialize class parameters

        # perform port configuration at start-up
        self._handle.port = "/dev/ttyUSB0"
        self._handle.baudrate = 115200
        self._handle.bytesize = serial.EIGHTBITS  # number of bits per bytes
        self._handle.parity = serial.PARITY_NONE  # set parity check: no parity
        self._handle.stopbits = serial.STOPBITS_ONE  # number of stop bits

        self._handle.timeout = 0.25  # non-block read
        self._handle.writeTimeout = 0.25  # timeout for write

        trace.debug('serial port configuration done')

        # self._address = address

        # Only one data stream per port
        self.data = []
        self.devices = {}
        self.sync_data_ready = threading.Event()
        self.async_data_ready = threading.Event()
        self.bin_data_ready = threading.Event()
        self._thread = threading.Thread(name='serial_thr', target= self._read_from_device)

    def __del__(self):
        self.disconnect()

    def connect(self, port_name="/dev/ttyUSB0"):
        """
        Connect device
        :param port_name: Specify serial port name if different
                          than /dev/ttyUSB0
        :return: True if connected, False if connection failed
        """

        # if port is different than default use it
        if self._handle.port != port_name:
            self._handle.port = port_name

        # start connecting
        trace.debug("Trying to connect..")
        try:
            self._handle.open()
        except Exception as e:
            trace.error("error open serial port: " + str(e))
            return False

        if self._handle.isOpen():
            trace.debug('serial port opened')
        else:
            trace.debug('serial port not opened')
            return False

        # flush buffers at start-up
        try:
            self._handle.flushInput()
            self._handle.flushOutput()
        except Exception as e:
            trace.error("error flushing input " + str(e))

        # at this point device should be connected
        self._thread.start()
        return True

    def disconnect(self):

        # mark job as done (this flag is for background thread)
        self._done = True

        # wait until background thread is done
        # if it is still running
        self._thread.join()

        # close serial port
        if self._handle.isOpen():
            self._handle.close()
            trace.debug('serial port closed')

    def init_device(self, idn):
        self.devices[idn] = {'sync': [], 'async': []}

    def write_command(self, command, idn):
        """
        Write command to device
        :param command: self-explanatory
        :return: None
        """

        # add prefix and CR on the end
        command = str(idn) + ":" + command + '\n'
        trace.debug('writing command: ' + command)
        self._handle.write(bytes(command, 'utf8'))

    def write_command_ret(self, command, idn):
        """
        Writes a command to device and waits for standard response
        :param command: self-explanatory
        :return: None
        """
        self.sync_data_ready.clear()
        self.write_command(command,idn)
        self.sync_data_ready.wait(self.response_timeout)
        if not bool(self.devices.get(idn).get('sync')):
            resp=self.devices.get(idn).get('sync').pop()
            trace.debug("Command: \""+str(command)+"\" successfully sent. Response: \""+str(resp)+"\"")
            return resp
        else:
            trace.debug("No response for command: \"" + str(command) + "\"")
            return None


    def write_command_stdr(self, command, idn):
        """
        Writes a command to device and waits for standard response
        :param command: self-explanatory
        :return: None
        """
        self.sync_data_ready.clear()
        self.write_command(command,idn)
        self.sync_data_ready.wait(self.response_timeout)
        if not bool(self.devices.get(idn).get('sync')):
            resp=self.devices.get(idn).get('sync').pop()
            if resp.rsplit()[0] == command.rsplit()[0]:
                trace.debug("Command: \""+str(command)+"\" successfully sent. Response: \""+str(resp)+"\"")
            else:
                trace.error("Wrong response for command: \"" + str(command) + "\". Response: \"" + str(resp) + "\" , expected: \""+str(command.rsplit()[0]))
            if len(resp.rsplit()) > 1:
                return resp.rsplit()[1]
            else:
                return None

    def decode_binvalue(self,seq):
        # Data format is: CSHHHHH\r
        # C - is a prefix that also serves as a 3 bit-long counter (starts with prefix0)
        # S - status byte (6 bits: 1 + negated 5 bits representing input lines)
        # HHHHH - is a 18-bit hex value (should be treated as value with sign)
        # \r - terminating CR
        # Extended format is: CSHHHHHhH\r
        # where CSH are as above and h is H (hex digit) with highest bit set
        # this signals the fact that also fractional part is sent so the bit should
        # be cleared, whole value treated as int and later divided by 256
        ptr = 0
        c = seq[ptr]
        value = (-1 if c >= ord('8') else 0)  # test for sign bit (in hex digit)
        shift = False

        for c in list(seq):
            if (c & 0x80):
                c &= 0x7F
                shift = True

            if c >= ord('0') and c <= ord('9'):
                nibble = c - ord('0')
            elif c >= ord('A') and c <= ord('F'):
                nibble = c - (ord('A') - 10)
            else:
                break
            value <<= 4
            value |= nibble

        return (float(value) / 256   if shift else float(value))* 6.25 / 65536

    def read_line(self, line):
        coms = line.split(b'\r')
        for com in coms:
            if com[0] > 32 and com[0] <= 40:
                value = self.decode_binvalue(com[2:])
                self.data.append(value)
                self.bin_data_ready.set()
                trace.info('Data value:'+ str(value))
            else:
                idn, com_type, message = tuple(com.partition(b'.'))
                # First char after the id number
                if com_type == b'.':
                    com_type = 'sync'
                else:
                    # if not, try other ordering character
                    idn, com_type, message = tuple(com.partition(b';'))
                    if com_type == b';':
                        com_type = 'async'
                    else:
                        trace.error('Major parsing fuckup, good luck')
                    return -1

                idnn = int(idn)
                if idnn not in self.devices.keys():
                    self.init_device(idnn)
                message=message.decode('ascii') #convert bytes to string
                self.devices[idnn][com_type].append(message)
                if com_type == 'sync':
                    self.sync_data_ready.set()
                elif com_type == 'async':
                    self.async_data_ready.set()
                trace.debug('Device ID: %d Communication type: %s Message: %s', idnn, com_type, message)

    def _read_from_device(self):
        """
        Read from device. This function is executed in separate
        thread. Function also updates necessary parameters for
        this class
        """
        data = bytearray()
        while not self._done:

            # if incoming bytes are waiting to be
            # read from the serial input buffer
            if self._handle.inWaiting():
                # read and remove all whitespaces
                # on the right side, including '\n'
                data.extend( self._handle.read(self._handle.inWaiting()))
                line,sep,rest=tuple(data.partition(b'\r'))
                if sep == b'\r':
                    trace.debug("new data to parse: " + str(line))
                    self.read_line(line.strip())
                    data=rest


            # sleep for a moment (pseudo-yield in python)
            time.sleep(0.001)
