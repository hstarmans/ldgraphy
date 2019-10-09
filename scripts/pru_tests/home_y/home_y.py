#!/usr/bin/python3
""" home_y.py - test script for the Firestarter
moves the y-motor for a given amount of steps and stepspeed
unless it hits the y-home switch
"""
from uio.ti.icss import Icss
import ctypes
import Adafruit_BBIO.GPIO as GPIO

# INPUT
STEP_PER_MM = 76.2
STEPSPEED = round(3*STEP_PER_MM)
STEPS = round(200*STEP_PER_MM) 
DIRECTION = False # False is homing direction 

y_direction_pin = "P8_15"
enable_pin = "P9_12"

GPIO.setup(y_direction_pin, GPIO.OUT)
GPIO.setup(enable_pin, GPIO.OUT)


if DIRECTION:
    GPIO.output(y_direction_pin, GPIO.HIGH)
else:
    GPIO.output(y_direction_pin, GPIO.LOW)

GPIO.output(enable_pin, GPIO.LOW)

# DERIVED
CPU_SPEED = 200E6
INST_PER_LOOP = 2
HALF_PERIOD_STEP = round(CPU_SPEED/(2*STEPSPEED*INST_PER_LOOP))

class Params( ctypes.Structure ):
    _fields_ = [
            ("steps", ctypes.c_uint32),  
            ("halfperiodstep", ctypes.c_uint32)
]

pruss = Icss('/dev/uio/pruss/module')
pruss.initialize()
params0 = pruss.core0.dram.map(Params)
params0.steps = STEPS
params0.halfperiodstep = HALF_PERIOD_STEP
pruss.core0.load('home_y.bin')
pruss.core0.run()
print('Waiting for move to finish')
while not pruss.core0.halted:
    pass
GPIO.output(enable_pin, GPIO.HIGH)
if pruss.core0.r2:
    print("Homing failed")
else:
    print("Touched home switch")

GPIO.output(enable_pin, GPIO.HIGH)
