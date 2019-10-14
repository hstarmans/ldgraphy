#!/usr/bin/python3
""" move_z.py - test script for the Firestarter
moves the z-motor for a given amount of steps and stepspeed
"""
from uio.ti.icss import Icss
import ctypes
import Adafruit_BBIO.GPIO as GPIO

# INPUT
XSTEPSPERMM = 76.2 
STEPSPEED = round(1*XSTEPSPERMM)
STEPS =  round(1*XSTEPSPERMM) 
DIRECTION = True   # false is in direction home

z_direction_pin = "P8_17"
enable_pin = "P9_12"

GPIO.setup(enable_pin, GPIO.OUT)
GPIO.setup(z_direction_pin, GPIO.OUT)

if DIRECTION:
    GPIO.output(z_direction_pin, GPIO.HIGH)
else:
    GPIO.output(z_direction_pin, GPIO.LOW)

GPIO.output(enable_pin, GPIO.LOW)

# DERIVED
CPU_SPEED = 200E6
INST_PER_LOOP = 2
HALF_PERIOD_STEP = CPU_SPEED/(2*STEPSPEED*INST_PER_LOOP)

class Params( ctypes.Structure ):
    _fields_ = [
            ("steps", ctypes.c_uint32),  
            ("halfperiodstep",    ctypes.c_uint32),
]

pruss = Icss('/dev/uio/pruss/module')
pruss.initialize()
params0 = pruss.core1.dram.map(Params)
params0.steps = round(STEPS)
params0.halfperiodstep = round(HALF_PERIOD_STEP)
pruss.core1.load('move_x.bin')
pruss.core1.run()
print('Waiting for move to finish')
while not pruss.core1.halted:
    pass

GPIO.output(enable_pin, GPIO.HIGH)
