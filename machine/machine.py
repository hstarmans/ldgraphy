'''
@company: Hexastorm
@author: Rik Starmans
'''
from copy import deepcopy
from time import sleep
from ctypes import c_uint32, Structure

from pyuio.ti.icss import Icss
from pyuio.uio import Uio
import Adafruit_BBIO.GPIO as GPIO
import numpy as np
from bidict import bidict


class Machine:
    def __init__(self):
        self.position = [0,0]
        self.steps_per_mm = 76.2
        self.setuppins()
        self.setuppru()


    def loadconstants(self):
        '''
        loads COMMANDS and Errors
        '''
        self.COMMANDS = ['CMD_EMPTY', 'CMD_SCAN_DATA', 'CMD_SCAN_DATA_NO_SLED']
        self.COMMANDS += ['CMD_EXIT', 'CMD_DONE']
        self.COMMANDS = bidict(enumerate(self.COMMANDS))
        self.ERRORS = ['ERROR_NONE', 'ERROR_DEBUG_BREAK', 'ERROR_MIRROR_SYNC']
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
        self.pixelsinline = 230  #TODO: shared with interpolator


    def setuppins(self):
        '''
        creates dictionary for motor pins and disables motors
        '''
        self.pins = {'x_dir': "P9_12",
                     'x_enable' : "P9_15",
                     'y_dir': "P9_20",
                     'y_enable': "P9_19"}

        for key, value in self.pins.items():
            GPIO.setup(key, GPIO.OUT)
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
        params0.steps = round(distance * self.steps_per_mm)
        CPU_SPEED = 200E6
        INST_PER_LOOP = 2
        params0.halfperiodstep = round(CPU_SPEED/(2*speed*INST_PER_LOOP))


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


    def home(self, direction='x', speed = '2'):
        '''
        homes axis in direction at given speed

        :param direction; homing direction, x or y
        :param speed; homing speed in mm/s
        '''
        if direction == 'x':
            GPIO.output(self.pins['x_dir'], GPIO.LOW)
            self.pruss.core0.load('home_x.bin')
        else:
            GPIO.output(self.pins['y_dir'], GPIO.HIGH)
            self.pruss.core0.load('home_y.bin')
        
        self.write_params(200, speed)
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
    

    def move(self, target_position, speed = '2'):
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
            self.write_params(displacement[0], speed)
            self.pruss.core0.load('move_x.bin')
            self.runcore0('x')


        if displacement[1]:
            direction = GPIO.LOW if displacement[0] > 0 else GPIO.HIGH
            GPIO.output(self.pins['y_dir'], direction)
            self.write_params(displacement[1], speed)
            self.pruss.core0.load('move_y.bin')
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
        self.pruss.core0.load('./stabilizer.bin')
        self.pruss.core0.dram.write([0]*self.pixelsinline*8+[0]*5)
        self.pruss.core0.run()


    def receive_command(self, byte):
        self.pruss.intc.out_enable_one(self.IRQ) 
        self.irq.irq_recv()
        self.pruss.intc.ev_clear_one(self.pruss.intc.out_event[self.IRQ])
        self.pruss.intc.out_enable_one(self.IRQ)
        command_index = self.pruss.core0.dram.map(length = 1, offset = byte)
        return command_index


    def disable_scanhead(self):
        '''
        disables scanhead

        function sleeps to offset is START_RINGBUFFER
        '''
        data = [self.COMMANDS.inv['CMD_EXIT']]
        START_RINGBUFFER = 5
        self.pruss.core0.dram.write(data, offset = START_RINGBUFFER)
        command_index = self.receive_command(START_RINGBUFFER)
        while not self.pruss.core0.halted:
            pass
        if self.COMMANDS[command_index] != 'CMD_DONE':
            print("Unexpected command received; {}".format(self.COMMANDS[command_index]))
        
    
    def error_received(self):
        '''
        prints errors received and returns error index

        can be used to read out errors from the laser scanner
        '''
        ERROR_RESULT_POS = 0
        error_index = self.pruss.core0.dram.map(length = 1, offset = ERROR_RESULT_POS)[0]
        if error_index:
            try:
                print("Error received; {}".format(self.ERRORS[error_index]))
            except IndexError:
                print("Error, error out of index")
        return error_index

    
    def expose(self, line_data, multiplier = 1):
        '''
        expose given line_data to substrate

        :param line_data; data to write to scanner, 1D binary numpy array
        :param multiplier; amount of times a line is exposed
        '''
        # constants needed from  laser-scribe-constants.h
        line_data = 255 * line_data   # in effect we divide our laserfrequency by 8
        QUEUE_LEN = 8
        if len(line_data) < QUEUE_LEN * self.pixelsinline or len(line_data) % self.pixelsinline:
            raise Exception('Data send to scanner seems invalid.')
        # you start by writing 8 lines
        write_data = [self.ERRORS.inv['ERROR_NONE']] + [0]*4
        counter = 0
        line = 0
        GPIO.output(self.pins['x_dir'], GPIO.LOW) # motor on

        while counter < QUEUE_LEN:
            extra_data = [self.COMMANDS.inv['CMD_SCAN_DATA']]
            extra_data += list(line_data[line*self.pixelsinline:(line+1)*self.pixelsinline])
            if multiplier > 1:
                null_data = deepcopy(extra_data)
                null_data[0] = self.COMMANDS.inv['CMD_SCAN_DATA_NO_SLED']
                if counter+multiplier < QUEUE_LEN:
                    extra_data += null_data*(multiplier-1)
                else:
                    extra_data += null_data*(QUEUE_LEN-counter)
            write_data += extra_data
            counter += multiplier
            line += 1
            if len(write_data) == 8*(1 + self.pixelsinline):
                self.pruss.core0.dram.write(write_data)
            else:
                raise Exception('Preparation data incorrect')
        
        def receive_command(byte):
            command_index = self.receive_command(byte)
            if self.COMMANDS[command_index] != 'CMD_EMPTY':
                raise Exception('Line not empty')        


        SCANLINE_DATA_SIZE = 1 + self.pixelsinline
        byte = START_RINGBUFFER = 5
        for line in range(QUEUE_LEN, len(line_data)):
            receive_command(byte)
            extra_data = list(line_data[line*self.pixelsinline:(line+1)*self.pixelsinline])
            write_data = [self.COMMANDS.inv['CMD_SCAN_DATA']] + extra_data
            self.pruss.core0.dram.write(write_data, offset = byte)
            byte += SCANLINE_DATA_SIZE
            if byte > SCANLINE_DATA_SIZE * QUEUE_LEN:
                byte = START_RINGBUFFER
            for counter in range(1, multiplier):
                receive_command(byte)
                write_data = [self.COMMANDS.inv['CMD_SCAN_DATA_NO_SLED']] + extra_data
                self.pruss.core0.dram.write(write_data)
                byte += SCANLINE_DATA_SIZE
                if byte > SCANLINE_DATA_SIZE * QUEUE_LEN:
                    byte = START_RINGBUFFER
        
        SYNC_FAIL_POS = 1
        sync_fails = self.pruss.core0.dram.map(c_uint32, offset = SYNC_FAIL_POS).value
        if sync_fails:
            print("There have been {} sync fails".format(sync_fails))  #TODO: write to log
        GPIO.output(self.pins['x_dir'], GPIO.HIGH) # motor off


            



    



