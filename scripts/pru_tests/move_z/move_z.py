#!/usr/bin/python3
""" move_z.py - test script for the Firestarter v0.2
moves the z-motor for a given amount of steps and stepspeed
"""
from pyuio.ti.icss import Icss
import ctypes
import Adafruit_BBIO.GPIO as GPIO
from time import sleep

# INPUT
STEPSPERMM = 76.2
MICROSTEPPING = 1
STEPSPEED = round(3*STEPSPERMM) 
STEPS = round(10 * STEPSPERMM)
DIRECTION = False  # False is in the homing direction


z_direction_output = "P8_17"
GPIO.setup(z_direction_output, GPIO.OUT)
if DIRECTION:
    GPIO.output(z_direction_output, GPIO.HIGH)
else:
    GPIO.output(z_direction_output, GPIO.LOW)

z_enable_output = "P8.11"
GPIO.setup(z_enable_output, GPIO.OUT)
GPIO.output(z_enable_output, GPIO.LOW)

steps = round(STEPS)
halfperiodstep = 1/(2*STEPSPEED)

z_dir_output = "P8.17"
GPIO.setup(z_dir_output, GPIO.OUT)

#TODO: load settings into stepper


for step in range(0, steps):
    GPIO.output(z_dir_output, GPIO.LOW)
    sleep(halfperiodstep)
    GPIO.output(z_dir_output, GPIO.HIGH)
    sleep(halfperiodstep)

GPIO.output(z_enable_output, GPIO.HIGH)  # disable motors



