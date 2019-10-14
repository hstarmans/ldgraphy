#!/usr/bin/python3
""" move_z.py - test script for the Firestarter v0.2
moves the z-motor for a given amount of steps and stepspeed
"""
from time import sleep
import ctypes

from uio.ti.icss import Icss
import Adafruit_BBIO.GPIO as GPIO
from Adafruit_BBIO.SPI import SPI

# INPUT
STEPSPERMM = 76.2
MICROSTEPPING = 1  # STANDAARD STAAT JE MOTOR OP 256
STEPSPEED = round(3 * STEPSPERMM) 
STEPS = round(10 * STEPSPERMM)
DIRECTION = False  # False is in the homing direction
steps = round(STEPS)
halfperiodstep = 1/(2*STEPSPEED)
#TODO: overwrite
halfperiodstep = 10E-6
steps = 10000

# PINS
z_direction_output = "P8_17"
enable_output = "P9_12"
z_step_output = "P8_16"

GPIO.setup(z_direction_output, GPIO.OUT)
GPIO.setup(enable_output, GPIO.OUT)
GPIO.setup(z_step_output, GPIO.OUT)

if DIRECTION:
    GPIO.output(z_direction_output, GPIO.HIGH)
else:
    GPIO.output(z_direction_output, GPIO.LOW)

# enable motors
GPIO.output(enable_output, GPIO.LOW)

for step in range(0, steps):
    GPIO.output(z_step_output, GPIO.LOW)
    sleep(halfperiodstep)
    GPIO.output(z_step_output, GPIO.HIGH)
    sleep(halfperiodstep)

GPIO.output(enable_output, GPIO.HIGH)  
