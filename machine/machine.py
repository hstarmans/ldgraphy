'''
Class which can be used to be interact with instrument

@company: Hexastorm
@author: Rik Starmans
'''
from copy import deepcopy
from time import sleep
from ctypes import c_uint32, Structure
from os.path import join, dirname, realpath

from pyuio.ti.icss import Icss
from pyuio.uio import Uio
import Adafruit_BBIO.GPIO as GPIO
import Adafruit_GPIO.I2C as I2C
import numpy as np
from bidict import bidict


class Machine:
    def __init__(self):
        self.position = [0, 0]
        self.steps_per_mm = 76.2
        self.pixelsinline = 171
        
        currentdir = dirname(realpath(__file__))
        self.bin_folder = join(currentdir, 'binaries')
        
        self.setuppins()
        self.setuppru()
        self.loadconstants()

        self.digipot = I2C.get_i2c_device(0x28)


    #TODO: do via getter / setter?
    def set_laser_power(self, value):
        '''
        sets laser power to given value

        :param value: laser power
        '''
        if value < 0 or value > 255:
            raise Exception('Invalid laser power')
        self.digipot.write8(0, value)
    

    def get_laser_power(self):
        '''
        get current laser power
        '''
        return abs(self.digipot.readU8(0))


    def switch_laser(self, value):
        '''
        switches laser 0%, 50% or 100% on.
        
        :param value: {0:0, 1:50, 2:100} 
        '''
        self.pruss.core0.load(join(self.bin_folder,
            'switch_laser.bin'))

        class Params( Structure ):
            _fields_ = [
                    ("power", c_uint32)
        ]
        params0 = self.pruss.core0.dram.map(Params)
        params0.power = int(round(value))
        self.pruss.core0.run()
        while not self.pruss.core0.halted:
            pass


    def loadconstants(self):
        '''
        loads COMMANDS and Errors
        '''
        self.COMMANDS = ['CMD_EMPTY',
                'CMD_SCAN_DATA', 'CMD_SCAN_DATA_NO_SLED']
        self.COMMANDS += ['CMD_EXIT', 'CMD_DONE']
        self.COMMANDS = bidict(enumerate(self.COMMANDS))
        self.ERRORS = ['ERROR_NONE',
                'ERROR_DEBUG_BREAK', 'ERROR_MIRROR_SYNC']
        self.ERRORS += ['ERROR_TIME_OVERRUN']
        self.ERRORS = bidict(enumerate(self.ERRORS))


    def setuppru(self):
        '''
        creates interface for pruss and irq
        '''
        self.IRQ = 2
        self.pruss = Icss('/dev/uio/pruss/module')
        self.irq = Uio("/dev/uio/pruss/irq%d" % self.IRQ )
        self.pruss.initialize()


    def setuppins(self):
        '''
        creates dictionary for motor pins and disables motors
        '''
        self.pins = {'y_dir': "P9_12",
                     'y_enable' : "P9_15",
                     'x_dir': "P9_20",
                     'x_enable': "P9_19"}

        for key, value in self.pins.items():
            GPIO.setup(value, GPIO.OUT)
        # disable motors
        GPIO.output(self.pins['x_dir'], GPIO.HIGH)
        GPIO.output(self.pins['y_dir'], GPIO.HIGH)


    def write_params(self, distance, speed):
        '''
        writes parameters to pru0

        in moving distance defines a length
        in homing distance defines a limit
        :param distance; distance in mm
        :param speed; speed in mm/s
        '''
        class Params( Structure ):
            _fields_ = [
                    ("steps", c_uint32),  # upper limit
                    ("halfperiodstep", c_uint32) # speed
        ]
        params0 = self.pruss.core0.dram.map(Params)
        # round(np.float64(3.0)) -> 3.0, round(3.0) -> 3
        params0.steps = int(round(distance * self.steps_per_mm))
        CPU_SPEED = 200E6
        INST_PER_LOOP = 2
        params0.halfperiodstep = int(round(CPU_SPEED
            /(2*speed*self.steps_per_mm*INST_PER_LOOP)))


    def runcore0(self, direction):
        if direction == 'x':
            enablepin = self.pins['x_enable']
        else:
            enablepin = self.pins['y_enable']
        GPIO.output(enablepin, GPIO.LOW)
        self.pruss.core0.run()
        while not self.pruss.core0.halted:
            pass
        GPIO.output(enablepin, GPIO.HIGH)


    def home(self, direction='x', speed = 2):
        '''
        homes axis in direction at given speed

        :param direction; homing direction, x or y
        :param speed; homing speed in mm/s
        '''
        if direction == 'x':
            GPIO.output(self.pins['x_dir'], GPIO.LOW)
            self.pruss.core0.load(join(self.bin_folder,
                'home_x.bin'))
        else:
            GPIO.output(self.pins['y_dir'], GPIO.LOW)
            self.pruss.core0.load(join(self.bin_folder,
                'home_y.bin'))
        
        self.write_params(300, speed)
        self.runcore0(direction)
        
        if self.pruss.core0.r2:
            raise Exception('Homing failed')
        else: 
        # update current position, move so homing switch is disabled
            if direction == 'x':
                self.position[0] = 0
                self.move([40, self.position[1]], 4)
                self.position[0] = 0
            else:
                self.position[1] = 0
                self.move([self.position[0], 10], 4)
                self.position[1] = 0
    

    def move(self, target_position, speed = 2):
        '''
        moves axis into position at given speed

        :param target position; list, [x, y] in mm
        :param speed; homing speed in mm/s
        '''
        if target_position[0] < 0 or target_position[0] > 200:
            raise Exception('Target out of bounds')
        elif target_position[1] < 0 or target_position[1] > 200:
            raise Exception('Target out of bounds')


        displacement = np.array(target_position) - np.array(self.position)
        if displacement[0]:
            direction = GPIO.HIGH if displacement[0] > 0 else GPIO.LOW
            GPIO.output(self.pins['x_dir'], direction)
            self.write_params(abs(displacement[0]), speed)
            self.pruss.core0.load(join(self.bin_folder, 'move_x.bin'))
            self.runcore0('x')


        if displacement[1]:
            direction = GPIO.HIGH if displacement[1] > 0 else GPIO.LOW
            GPIO.output(self.pins['y_dir'], direction)
            self.write_params(abs(displacement[1]), speed)
            self.pruss.core0.load(join(self.bin_folder, 'move_y.bin'))
            self.runcore0('y')


        self.position = target_position
    

    def enable_scanhead(self):
        '''
        enables scanhead, ensure scanhead is not above substrate
        '''
        PRU0_ARM_INTERRUPT = 19
        self.pruss.intc.ev_ch[PRU0_ARM_INTERRUPT] = self.IRQ
        self.pruss.intc.ev_clear_one(PRU0_ARM_INTERRUPT)
        self.pruss.intc.ev_enable_one(PRU0_ARM_INTERRUPT)
        self.pruss.core0.load(join(self.bin_folder, './stabilizer.bin'))
        #self.pruss.core0.dram.write([0]*self.pixelsinline*8+[0]*5)
        #self.pruss.core0.run()


    def receive_command(self, byte):
        self.pruss.intc.out_enable_one(self.IRQ) 
        self.irq.irq_recv()
        self.pruss.intc.ev_clear_one(self.pruss.intc.out_event[self.IRQ])
        self.pruss.intc.out_enable_one(self.IRQ)
        [command_index] = self.pruss.core0.dram.map(length = 1,
                offset = byte)
        return command_index


    def disable_scanhead(self, byte=1):
        '''
        disables scanhead

        function sleeps to offset is START_RINGBUFFER
        '''
        data = [self.COMMANDS.inv['CMD_EXIT']]
        self.pruss.core0.dram.write(data, offset = byte)
        #TODO: no longer works as you removed trigger! add again
        #command_index = self.receive_command(START_RINGBUFFER)
        while not self.pruss.core0.halted:
            pass
        #if self.COMMANDS[command_index] != 'CMD_DONE':
        #    print("Unexpected command received; {}".format(
        #        self.COMMANDS[command_index]))
        
    
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

    
    def expose(self, line_data, direction, multiplier = 1, move=False):
        '''
        expose given line_data to substrate in given direction
        each line is exposed multiplier times.

        :param line_data; data to write to scanner, 1D binary numpy array
        :param multiplier; amount of times a line is exposed
        :param direction; direction of exposure,
                          True is postive y (away from home)
        :param move; if enabled moves stage
        '''
        self.enable_scanhead()
        QUEUE_LEN = 8
        if (len(line_data) < QUEUE_LEN * self.pixelsinline 
                or len(line_data) % self.pixelsinline):
            raise Exception('''Data send to scanner seems invalid,
                    sanity check 1.''')
        if (line_data.max() < 2 or line_data.min() < 0
                or line_data.max() > 255):
            raise Exception('''Data send to scanner seems invalid,
                    sanity check 2''')
        if move:
            GPIO.output(self.pins['y_enable'], GPIO.LOW)
        else:
            GPIO.output(self.pins['y_enable'], GPIO.HIGH)
        
        if direction:
            GPIO.output(self.pins['y_dir'], GPIO.HIGH)
        else:
            GPIO.output(self.pins['y_dir'], GPIO.LOW)
        # prep scanner by writing 8 lines to buffer
        write_data = [self.ERRORS.inv['ERROR_NONE']] + [0]*4
        counter = 0
        line = 0
        while counter < QUEUE_LEN:
            extra_data = [self.COMMANDS.inv['CMD_SCAN_DATA']]
            extra_data += list(line_data[line*self.pixelsinline:
                (line+1)*self.pixelsinline])
            counter += 1
            if multiplier > 1:
                null_data = deepcopy(extra_data)
                #null_data[0] = self.COMMANDS.inv['CMD_SCAN_DATA_NO_SLED']
                if counter+(multiplier-1) < QUEUE_LEN:
                    extra_data += null_data*(multiplier-1)
                else:
                    extra_data += null_data*(QUEUE_LEN-counter)
            write_data += extra_data
            counter += multiplier-1
            line += 1

        if len(write_data) == 5 + QUEUE_LEN*(1 + self.pixelsinline):
            self.pruss.core0.dram.write(write_data)
        else:
            print(len(write_data))
            raise Exception('Preparation data incorrect')
        
        
        def receive_command(byte):
            #TODO: add timeout
            command_index = self.receive_command(byte)
            if self.COMMANDS[command_index] != 'CMD_EMPTY':
                print("Received {}".format(self.COMMANDS[command_index]))
                raise Exception('Line not empty')        

        
        SCANLINE_DATA_SIZE = self.pixelsinline
        SCANLINE_HEADER_SIZE = 1
        SCANLINE_ITEM_SIZE = SCANLINE_HEADER_SIZE + SCANLINE_DATA_SIZE
        byte = START_RINGBUFFER = 1
        self.pruss.core0.run()
        # clean up the rest which remains
        for counter in range(QUEUE_LEN, line-1+multiplier):
            receive_command(byte)
            extra_data = [self.COMMANDS.inv['CMD_SCAN_DATA_NO_SLED']]
            extra_data += list(line_data[(line-1)*self.pixelsinline:
                (line)*self.pixelsinline])
            self.pruss.core0.dram.write(extra_data, offset = byte)
            byte += SCANLINE_ITEM_SIZE
            if byte > SCANLINE_DATA_SIZE * QUEUE_LEN:
                byte = START_RINGBUFFER

        for line in range(line, len(line_data)//self.pixelsinline):
            receive_command(byte)
            extra_data = list(line_data[line*self.pixelsinline
                :(line+1)*self.pixelsinline])
            write_data = ([self.COMMANDS.inv['CMD_SCAN_DATA']] 
            + extra_data)
            self.pruss.core0.dram.write(write_data, offset = byte)
            byte += SCANLINE_ITEM_SIZE
            if byte > SCANLINE_DATA_SIZE * QUEUE_LEN:
                byte = START_RINGBUFFER
            for counter in range(1, multiplier):
                receive_command(byte)
                write_data = ([self.COMMANDS.inv['CMD_SCAN_DATA_NO_SLED']
                    ] + extra_data)
                self.pruss.core0.dram.write(write_data, offset = byte)
                byte += SCANLINE_ITEM_SIZE
                if byte > SCANLINE_DATA_SIZE * QUEUE_LEN:
                    byte = START_RINGBUFFER

        self.disable_scanhead(byte)
        GPIO.output(self.pins['y_enable'], GPIO.HIGH) # motor off


            



    



