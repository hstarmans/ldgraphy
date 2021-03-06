'''
Class which can be used to be to send data to the laser head and move it

It is also possible to take pictures with a remote camera.

@license: GPLv3
@company: Hexastorm
@author: Rik Starmans
'''
from copy import deepcopy
from time import sleep
from ctypes import c_uint32, c_uint16, c_uint8, Structure
from os.path import join, dirname, realpath
import pickle
import subprocess

from uio.ti.icss import Icss
from uio.device import Uio
import Adafruit_BBIO.GPIO as GPIO
import Adafruit_GPIO.I2C as I2C
import numpy as np
from bidict import bidict
import steppers




class Machine:
    def __init__(self, stepper=True, camera = False):
        if camera:
            from camera import Camera
            self.camera = Camera()
        self.loadconstants()
        self.position = [0, 0, 0]
        self.pindictionary()
        self.init_pru()
        self.currentdir = dirname(realpath(__file__))
        self.bin_folder = join(self.currentdir, 'binaries')
        self.laserchannels = 0
        self.configure_pins()
        if stepper:
            self.motor_spi = [self.init_stepper(label) for label in ['x','y','z']] 
        # digipot is used to set laser power
        self.digipot = I2C.get_i2c_device(0x28, busnum=2)


    def configure_pins(self):
        '''
        pins are configured via config-pin -f pinfile.bbio

        This relies on cape-universal. Cape-universal allows pins to be
        changed on the fly without reboot.
        '''
        path = join(self.currentdir, 'config-pin', 'firestarter.bbio')
        MyOut = subprocess.Popen(['config-pin', '-f', path ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT)
        stdout, stderr = MyOut.communicate()
        if stdout or stderr:
            raise Exception("Configuring pins via config-pin failed")


    @property
    def laser_power(self):
        '''
        gets power set for laser driver chip can be in range [0-255] 
        '''
        return abs(self.digipot.readU8(0))


    @laser_power.setter
    def laser_power(self, value):
        '''
        set laser power to given value in range [0-255]
        for the laser driver chip. This does not turn on or off the laser.

        The laser power can be changed in two ways.
        First by using one or two channels. Second by settings a value between
        0-255 at the laser driver chip.
        '''
        if value < 0 or value > 255:
            raise Exception('Invalid laser power')
        self.digipot.write8(0, value)


    @property
    def laserchannels(self):
        '''
        returns the number of laser channels turned on

        channels can be [0,1,2]
        '''
        return self._laserchannels


    @laserchannels.setter
    def laserchannels(self, channels):
        '''
        sets 0, 1 or 2 channels on.
        
        The laser power can be changed in two ways.
        First by using one or two channels. Second by setting a value in 
        range [0-255] at the laser driver chip. Here the amount of channels 
        used is set.
        :param channels: number of channels to be turned max is 2. 
        '''
        channels = int(round(channels))
        if channels<0 or channels>2:
            raise Exception("Channels is not within set [0,1,2]")

        self.pruss.core0.load(join(self.bin_folder,
            'switch_laser.bin'))

        class Params( Structure ):
            _fields_ = [
                    ("power", c_uint32)
        ]
        variables = self.pruss.core0.dram.map(Params)
        variables.power = int(round(channels))
        self.pruss.core0.run()
        while not self.pruss.core0.halted:
            pass
        self._laserchannels = int(round(channels))


    def test_photodiode(self):
        """
        The laser is turned on. The polygon is spun at a rate of 1000 Hz
        for 5 seconds. The photodiode is measured for three seconds, if 
        high within these three seconds test is succesfull, otherwise 
        unsuccesfull. The laser is turned off.
        """
        GPIO.output(self.pins['prism_enable'], GPIO.LOW)
        self.pruss.core0.load(join(self.bin_folder,
                        'photodiodetest.bin'))
        self.pruss.core0.run()
        print("Waiting for core to halt")
        while not self.pruss.core0.halted:
            pass
        byte0 = self.pruss.core0.dram.map(c_uint32)
        return_value = int(byte0.value)
        if return_value == 0:
            print("Laser detected with photodiode, test successfull")
        elif return_value == 1:
            print("Photo diode connected but no signal")
        else:
            print("Photo diode not connected")
        GPIO.output(self.pins['prism_enable'], GPIO.HIGH)


    def test_polygonmotor(self):
        """
        spins the polygon at a rate of x Hz for 5 seconds
        """
        GPIO.output(self.pins['prism_enable'], GPIO.LOW)
        self.pruss.core0.load(join(self.bin_folder,
                        'spinpolygon.bin'))
        self.pruss.core0.run()
        print("Spinning polygon for 5 seconds")
        while not self.pruss.core0.halted:
            pass
        GPIO.output(self.pins['prism_enable'], GPIO.HIGH)


    def test_createline(self):
        """
        spins the polygon at a rate of x Hz for 5 seconds
        while laser channel 1 is enabled.
        As such a line is created without a phase lock loop.
        """
        GPIO.output(self.pins['prism_enable'], GPIO.LOW)
        self.pruss.core0.load(join(self.bin_folder,
                        'createline.bin'))
        self.pruss.core0.run()
        print("Turning on channel 1 and spinning polygon for 5 seconds")
        while not self.pruss.core0.halted:
            pass
        GPIO.output(self.pins['prism_enable'], GPIO.HIGH)


    def loadconstants(self):
        '''
        loads COMMANDS and Errors
        '''
        # commands accepted by scanhead also defined in laserscribe constants
        self.COMMANDS = ['CMD_EMPTY',
                'CMD_SCAN_DATA', 'CMD_SCAN_DATA_NO_SLED']
        self.COMMANDS += ['CMD_EXIT', 'CMD_DONE']
        self.COMMANDS = bidict(enumerate(self.COMMANDS))
        # errors accepted by scanhead also defined in laserscribe constants
        self.ERRORS = ['ERROR_NONE',
                'ERROR_DEBUG_BREAK', 'ERROR_MIRROR_SYNC']
        self.ERRORS += ['ERROR_TIME_OVERRUN']
        self.ERRORS = bidict(enumerate(self.ERRORS))

        #TODO: place this in a dictionary or a named tuple

        # key variables
        self.RPM = 2400                           # revolutions per minute 
        self.TICK_DELAY = 100                # cpu cycles in loop
        PRU_SPEED = 200E6                    # cpu cycles per second
        self.FACETS = 4                           # number of sides of prism
        self.TICKS_START = 4375              # laser starts in off state
        self.SCANLINE_DATA_SIZE = 790        # there are 8 pixels per byte 
                                             # so TICKS = 8*SCANLINE_DATA_SIZE
        # dependent variables
        self.TICKS_PER_PRISM_FACET = round(PRU_SPEED//  # ticks per prism facet
        (self.TICK_DELAY*(self.RPM*self.FACETS)/60)) 
        # time in seconds used to spinup prism
        self.SPINUP_TICKS = round(1.5 * PRU_SPEED / self.TICK_DELAY) 
        # time in seconds waited for laser stabilization
        self.MAX_WAIT_STABLE_TICKS = round(1.125 * PRU_SPEED / self.TICK_DELAY) 
        # ticks per half period of prism motor
        self.TICKS_HALF_PERIOD_MOTOR=int(round((self.TICKS_PER_PRISM_FACET*self.FACETS/6)/2))
        self.SCANLINE_HEADER_SIZE = 1        # each line starts with a self.COMMAND
        self.START_RINGBUFFER = 1            # the zero byte is an error code, ringbuffer starts at 1
        self.QUEUE_LEN = 8                   # length of the ringbuffer
        # length of an item in the ringbuffer in bytes
        self.SCANLINE_ITEM_SIZE = self.SCANLINE_HEADER_SIZE + self.SCANLINE_DATA_SIZE
        # the prism is spin up, it is determined if the jitter per prism is within a certain threshold
        self.JITTER_THRESH = round(self.TICKS_PER_PRISM_FACET / 400 )
        # after spinup the jitter allow is set smaller this leads to better results
        self.JITTER_ALLOW = round(self.TICKS_PER_PRISM_FACET / 3000 )

        self.STEPSPERMM = {'x': 76.2, 'y': 76.2, 'z': 1600}
        # These things are needed in interpolator
        self.SLED_SPEED = 1/self.STEPSPERMM['y']*(self.RPM*self.FACETS/60)
        #print("Sled speed is fixed at {} mm/s".format(SLED_SPEED))
        #print("Laser freq is {} Hz".format(200e6/TICK_DELAY))
        


    def init_stepper(self, drive='x', mA=600, microsteps=16, stealthchop=True):
        '''
        connects to stepper motor with current in miliamperes, number of microsteps
        and steatlchop, drive can be x, y or z.
        '''
        GPIO_0_BASE = 0x44E07000
        # pins order is x,y,z
        pindict = {'x':GPIO_0_BASE | 5,'y':GPIO_0_BASE | 30, 'z': GPIO_0_BASE | 26} 
        try:
            motor = steppers.TMC2130(pindict[drive])
        except KeyError:
            raise Exception("Invalid drive value")
        motor.begin()
        if motor.test_connection():
            raise Exception("Failed to connent to {} motor".format(drive))
        motor.rms_current(mA)
        motor.microsteps(microsteps)
        motor.toff(3)
        motor.stealthChop(stealthchop)
        return motor


    def init_pru(self):
        '''
        creates interface for pruss and irq
        '''
        self.IRQ = 2
        self.pruss = Icss('/dev/uio/pruss/module')
        self.irq = Uio("/dev/uio/pruss/irq%d" % self.IRQ, blocking=False)
        self.pruss.initialize(fill_memories=True)


    def pindictionary(self):
        '''
        creates dictionary for motor pins
        '''
        self.pins = {'x_dir': "P9_42",
                     'y_dir': "P8_15",
                     'z_dir': "P8_17",
                     'step_enable': "P9_12",
                     'prism_enable': "P9_23"}

        for key, value in self.pins.items():
            GPIO.setup(value, GPIO.OUT)


    def write_params(self, axis, distance, speed, core=0):
        '''
        writes parameters to pru0

        in moving distance defines a length
        in homing distance defines a limit

        :param axis; can be 'x', 'y' or 'z' used to determine steps per mm
        :param distance; distance in mm
        :param speed; speed in mm/s
        :param core; pru core map parameters to
        '''
        try:
            steps_per_mm = self.STEPSPERMM[axis]
        except KeyError:
            raise Exception("Axis {} invalid".format(axis))

        class Params( Structure ):
            _fields_ = [                         #1 steps moved in case of move
                    ("steps", c_uint32),         #1 max amount steps moved for home
                    ("halfperiodstep", c_uint32) #2 speed
        ]
        if core == 0:
            params = self.pruss.core0.dram.map(Params)
        else:
            params = self.pruss.core1.dram.map(Params)
        # round(np.float64(3.0)) -> 3.0, round(3.0) -> 3
        params.steps = int(round(distance * steps_per_mm))
        CPU_SPEED = 200E6
        INST_PER_LOOP = 2
        params.halfperiodstep = int(round(CPU_SPEED
            /(2*speed*steps_per_mm*INST_PER_LOOP)))


    def enable_steppers(self):
        '''
        enables stepper motors by setting enable pin to low
        '''
        GPIO.output(self.pins['step_enable'], GPIO.LOW)


    def disable_steppers(self):
        '''
        disables stepper motors by setting enable pin to high
        '''
        GPIO.output(self.pins['step_enable'], GPIO.HIGH)


    def home(self, direction='x', speed = 2):
        '''
        homes axis in direction at given speed
        
        :param direction; homing direction, x or y
        :param speed; homing speed in mm/s
        '''
        if direction == 'x':
            self.write_params('x', 300, speed, core=1)
            GPIO.output(self.pins['x_dir'], GPIO.LOW)
            self.pruss.core1.load(join(self.bin_folder,
                'home_x.bin'))
            self.pruss.core1.run()
            while not self.pruss.core1.halted:
                pass
            if self.pruss.core1.r10:
                raise Exception("Homing x failed")
        elif direction == 'y':
            self.write_params('y', 300, speed, core=0)
            GPIO.output(self.pins['y_dir'], GPIO.LOW)
            self.pruss.core0.load(join(self.bin_folder,
                'home_y.bin'))
            self.pruss.core0.run()
            while not self.pruss.core0.halted:
                pass
            if self.pruss.core0.r2:
                raise Exception("Homing y failed")
        elif direction == 'z':
            self.write_params('z', 300, speed, core=1)
            # home in the down direction
            GPIO.output(self.pins['z_dir'], GPIO.HIGH)
            self.pruss.core1.load(join(self.bin_folder,
                'home_z.bin'))
            self.pruss.core1.run()
            while not self.pruss.core1.halted:
                pass
            if self.pruss.core1.r10:
                raise Exception("Homing z failed")
        else:
            raise Exception("Direction invalid")
        # update current position, move so homing switch is disabled
        if direction == 'x':
            self.position[0] = 0
            self.move([40, self.position[1], self.position[2]], 4)
            self.position[0] = 0
        elif direction == 'y':
            self.position[1] = 0
            self.move([self.position[0], 10, self.position[2]], 4)
            self.position[1] = 0
        else: # must be z exception already cared in homing procedure
            self.position[2] = 0
            self.move([self.position[0], self.position[2], 10], 4)  
            self.position[2] = 0


    def move(self, target_position, speed = 2):
        '''
        moves axis into position at given speed

        :param target position; list, [x, y, z] in mm
        :param speed; homing speed in mm/s
        '''
        if target_position[0] < 0 or target_position[0] > 200:
            raise Exception('Target out of bounds')
        elif target_position[1] < 0 or target_position[1] > 200:
            raise Exception('Target out of bounds')
        elif target_position[2] < 0 or target_position[2] > 200:
            raise Exception('Target out of bounds')
        displacement = np.array(target_position) - np.array(self.position)
        
        if displacement[0]:
            direction = GPIO.HIGH if displacement[0] > 0 else GPIO.LOW
            GPIO.output(self.pins['x_dir'], direction)
            self.write_params('x', abs(displacement[0]), speed, core=1)
            self.pruss.core1.load(join(self.bin_folder, 'move_x.bin'))
            self.pruss.core1.run()
            while not self.pruss.core1.halted:
                pass

        if displacement[1]:
            direction = GPIO.HIGH if displacement[1] > 0 else GPIO.LOW
            GPIO.output(self.pins['y_dir'], direction)
            self.write_params('y', abs(displacement[1]), speed, core=0)
            self.pruss.core0.load(join(self.bin_folder, 'move_y.bin'))
            self.pruss.core0.run()
            while not self.pruss.core0.halted:
                pass

        if displacement[2]:
            direction = GPIO.LOW if displacement[2] > 0 else GPIO.HIGH
            GPIO.output(self.pins['z_dir'], direction)
            self.write_params('z', abs(displacement[2]), speed, core=1)
            self.pruss.core1.load(join(self.bin_folder, 'move_z.bin'))
            self.pruss.core1.run()
            while not self.pruss.core1.halted:
                pass

        self.position = target_position


    def enable_scanhead(self, singlefacet=False):
        '''
        enables scanhead, ensure scanhead is not above substrate
        :param singlefacet; if true singlefacet exposure enabled
        '''
        GPIO.output(self.pins['prism_enable'], GPIO.LOW)
        PRU0_ARM_INTERRUPT = 19
        self.pruss.intc.ev_ch[PRU0_ARM_INTERRUPT] = self.IRQ
        self.pruss.intc.ev_clear_one(PRU0_ARM_INTERRUPT)
        self.pruss.intc.ev_enable_one(PRU0_ARM_INTERRUPT)
        self.pruss.core0.load(join(self.bin_folder, './stabilizer.bin'))
        # map and set parameters
        class Variables( Structure ):
            _fields_ = [
                    ("ringbuffer_size", c_uint32),  
                    ("item_size", c_uint32),
                    ("start_sync_after", c_uint32),
                    ("global_time", c_uint32),
                    ("polygon_time", c_uint32),
                    ("wait_countdown", c_uint32),
                    ("hsync_time", c_uint32),
                    ("item_start", c_uint32),
                    ("item_pos", c_uint32),
                    ("state", c_uint16),
                    ("bit_loop", c_uint8),
                    ("last_hsync_bit", c_uint8),
                    ("single_facet", c_uint8),
                    ("current_facet", c_uint8),
                    ("ticks_half_period_motor", c_uint16),
                    ("low_thresh_prism", c_uint16),
                    ("high_thresh_prism", c_uint16),
                    ("ticks_start", c_uint16),
                    ("tick_delay", c_uint16),
                    ("spinup_ticks", c_uint32),
                    ("max_wait_stable_ticks", c_uint32)
                ]
        variables = self.pruss.core0.dram.map(Variables)
        if singlefacet:
            variables.single_facet = 1
        else:
            variables.single_facet = 0
        variables.item_size = self.SCANLINE_ITEM_SIZE
        variables.ringbuffer_size = self.SCANLINE_ITEM_SIZE * self.QUEUE_LEN
        variables.start_sync_after = self.TICKS_PER_PRISM_FACET - self.JITTER_ALLOW - 1
        variables.ticks_half_period_motor = self.TICKS_HALF_PERIOD_MOTOR
        variables.low_thresh_prism = self.TICKS_PER_PRISM_FACET - self.JITTER_THRESH
        variables.high_thresh_prism = self.TICKS_PER_PRISM_FACET + self.JITTER_THRESH
        variables.ticks_start = self.TICKS_START
        variables.tick_delay = self.TICK_DELAY
        variables.max_wait_stable_ticks = self.MAX_WAIT_STABLE_TICKS
        variables.spinup_ticks = self.SPINUP_TICKS
        self.pruss.core0.run()
        #TODO: add check polygon is enabled and stable
        # if you can't disable does not work
        sleep(4)


    def receive_command(self, byte = None, check = False):
        '''
        receives command at given offset

        :param byte; byte to read after trigger is received this is the command
        :param check; check wether the command equals command empty
        '''
        if byte == None:
            byte = self.START_RINGBUFFER

        self.pruss.intc.out_enable_one(self.IRQ) 
        # while loop is used in case irc_recv call is non-blocking
        while True:
            result = self.irq.irq_recv()
            if result:
                break
            else:
                sleep(1E-3)
        self.pruss.intc.ev_clear_one(self.pruss.intc.out_event[self.IRQ])
        self.pruss.intc.out_enable_one(self.IRQ)
        [command_index] = self.pruss.core0.dram.map(length = 1,
                                    offset = byte)

        if check:
            received_command = self.COMMANDS[command_index]
            if  received_command != 'CMD_EMPTY':
                error = ('Command not empty but {} '.format(received_command) +
                         'you could overwrite line not written to substrate yet.')
                raise Exception(error)
        
        return command_index


    def disable_scanhead(self):
        '''
        disables scanhead

        function sleeps to offset is START_RINGBUFFER
        '''
    
        data = [self.COMMANDS.inv['CMD_EXIT']]
        self.pruss.core0.dram.write(data, offset = self.START_RINGBUFFER)
        while not self.pruss.core0.halted:
            pass
        GPIO.output(self.pins['prism_enable'], GPIO.HIGH)


    def error_received(self):
        '''
        prints errors received and returns error index

        can be used to read out errors from the laser scanner
        '''
        ERROR_RESULT_POS = 0
        error_index = self.pruss.core0.dram.map(length = 1,
                offset = ERROR_RESULT_POS)[0]
        if error_index:
            try:
                print("Error received; {}".format(
                    self.ERRORS[error_index]))
            except IndexError:
                print("Error, error out of index")
        return error_index


    def expose(self, line_data, direction = True,
            multiplier = 1, move = False, takepicture = False):
        '''
        expose given line_data to substrate in given direction
        each line is exposed multiplier times.
        returns result of takepicture

        :param line_data; data to write to scanner, uint8
        :param multiplier; amount of times a line is exposed
        :param direction; direction of exposure,
                          True is postive y (away from home)
        :param move; if enabled moves stage
        :param takepicture; if enabled takes picture
        '''
        if line_data.dtype != np.uint8:
            raise Exception('Dtype must be uint8')
        if len(line_data) % self.SCANLINE_DATA_SIZE:
            raise Exception('Data invalid, length should be multilple'
                            + ' of scanline size')
        if (line_data.max() < 1 or line_data.max() > 255):
            raise Exception('Data invalid, values out of range.')
        if move:
            self.enable_steppers()
        else:
            self.disable_steppers()

        if direction:
            GPIO.output(self.pins['y_dir'], GPIO.HIGH)
        else:
            GPIO.output(self.pins['y_dir'], GPIO.LOW)
        
        byte = self.START_RINGBUFFER

        for scanline in range(0, len(line_data)//self.SCANLINE_DATA_SIZE):
            for counter in range(0, multiplier):
                self.receive_command(byte, True)
                # you start the picture where the laser is just off again
                if scanline == self.QUEUE_LEN and takepicture:
                    self.camera.get_spotinfo(wait=False)
                extra_data = list(line_data[scanline*self.SCANLINE_DATA_SIZE
                    :(scanline+1)*self.SCANLINE_DATA_SIZE])
                if counter == 0:
                    write_data = ([self.COMMANDS.inv['CMD_SCAN_DATA']] 
                    + extra_data)
                else:
                    write_data = ([self.COMMANDS.inv['CMD_SCAN_DATA_NO_SLED']] 
                    + extra_data)
                self.pruss.core0.dram.write(write_data, offset = byte)
                byte += self.SCANLINE_ITEM_SIZE
                if byte > self.SCANLINE_DATA_SIZE * self.QUEUE_LEN:
                    byte = self.START_RINGBUFFER

        if takepicture: 
            return self.camera.get_answer()
        
        return byte
