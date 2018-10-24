'''
@company: Hexastorm
@author: Rik Starmans
'''
from pyuio.ti.icss import Icss
import ctypes
import Adafruit_BBIO.GPIO as GPIO
import numpy as np


class Motors:
    def __init__(self):
        self.position = [0,0]
        self.steps_per_mm = 76.2
        self.setuppins()


    def setupru(self):
        self.pruss = Icss('/dev/uio/pruss/module')
        self.pruss.initialize()


    def setuppins(self):
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
        class Params( ctypes.Structure ):
            _fields_ = [
                    ("steps", ctypes.c_uint32),  # upper limit
                    ("halfperiodstep",    ctypes.c_uint32) # speed
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
        else:  # update current position
            if direction == 'x':
                self.position[0] = 0
            else:
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
        


