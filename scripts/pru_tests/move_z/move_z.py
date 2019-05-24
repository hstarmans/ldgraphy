#!/usr/bin/python3
""" move_z.py - test script for the Firestarter v0.2
moves the z-motor for a given amount of steps and stepspeed
"""
from time import sleep
import ctypes

from pyuio.ti.icss import Icss
import Adafruit_BBIO.GPIO as GPIO
from Adafruit_BBIO.SPI import SPI

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
# enable motors
GPIO.output(z_enable_output, GPIO.LOW)

steps = round(STEPS)
halfperiodstep = 1/(2*STEPSPEED)

z_dir_output = "P8.17"
GPIO.setup(z_dir_output, GPIO.OUT)

#TODO: port this to other stepper actions
spio_csx = "P9.17"
spio_csy = "P9.11"
spio_csz = "P8.14"
spio_selects = [spio_csx, spio_csy, spio_csz]
for select in spio_selects:
    GPIO.setup(select, GPIO.OUT)
    GPIO.setup(select, GPIO.HIGH)
GPIO.setup(spio_csz, GPIO.LOW)
spi = SPI(1,0)
spi.mode = 3
spi.msh = int(16000000/8)
# set current
# write access add 0x6c
# REGISTER IHOLD_IRUN ; addr 0x10
# bit 4..0 to 16  --> 0x10 (ihold current)
# bit 12.8 to 16  --> 0x10 (irun current)
spi.writebytes([(0x10+0x6C), 0, 0, 0x10, 0x10])
spi.readbytes(5)
spi.writebytes([(0x10+0x6C), 0, 0, 0x10, 0x10])
print("Target: {}", [0x10+0x6C, 0, 0, 0x10, 0x10])
print(spi.readbytes(5))
# stealth chop --> en_pwm mode
# REGISTER general configuration; addr 0x00
# bit 2 to 1  b'0100' = 4
spi.writebytes([(0x00+0x6C), 0, 0, 0, 4])
spi.readbytes(5)
spi.writebytes([(0x00+0x6C), 0, 0, 0, 4])
print("Target: {}", [0x10+0x6C, 0, 0, 0x10, 0x10])
print(spi.readbytes(5))

for step in range(0, steps):
    GPIO.output(z_dir_output, GPIO.LOW)
    sleep(halfperiodstep)
    GPIO.output(z_dir_output, GPIO.HIGH)
    sleep(halfperiodstep)

GPIO.output(spio_csz, GPIO.HIGH)
GPIO.output(z_enable_output, GPIO.HIGH)  



