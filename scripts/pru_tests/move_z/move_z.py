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
z_enable_output = "P8_18"
z_step_output = "P8_16"


GPIO.setup(z_direction_output, GPIO.OUT)
if DIRECTION:
    GPIO.output(z_direction_output, GPIO.HIGH)
else:
    GPIO.output(z_direction_output, GPIO.LOW)

# enable motors
GPIO.setup(z_enable_output, GPIO.OUT)
GPIO.output(z_enable_output, GPIO.LOW)

#TODO: port this to other stepper actions
#spio_csx = "P9_17"
spio_csy = "P9_11"
spio_csz = "P8_14"
spi = SPI(1,0)
#spi.no_cs = True
spi.cshigh = True
spio_selects = [spio_csy, spio_csz]
for select in spio_selects:
    GPIO.setup(select, GPIO.OUT)
    GPIO.output(select, GPIO.HIGH)

GPIO.output(spio_csz, GPIO.LOW)
spi.mode = 3
spi.msh = int(16000000/8)
#spi.msh = 1000

def controlledwrite(lst, chipselect):
    spi.writebytes(lst)
    GPIO.output(chipselect, GPIO.HIGH)
    sleep(1)
    GPIO.output(chipselect, GPIO.LOW)
    spi.readbytes(len(lst))
    GPIO.output(chipselect, GPIO.HIGH)
    sleep(1)
    GPIO.output(chipselect, GPIO.LOW)
    spi.writebytes(lst)
    GPIO.output(chipselect, GPIO.HIGH)
    sleep(1)
    GPIO.output(chipselect, GPIO.LOW)
    print("Target: {}", lst)
    res = spi.readbytes(len(lst))
    print(res)
    print("The status bit: {}", bin(res[0]))


# het kan zijn dat je naar chopconf moet schrijven
# om je motor van microstepping 256 te halen
# makerturm raad ook aan om TBL en TOFF te zetten
#     --> set_tbl
#     --> set_toff to 8
controlledwrite([0xEC, 0x01, int('110000',2), 0x00, 0x08], chipselect=spio_csz)
# convert to binary

# set current
# write access add 0x80
# REGISTER IHOLD_IRUN ; addr 0x10
# bit 4..0 to 22  --> 0x10 (ihold current)
# bit 12.8 to 31  --> 0x10 (irun current)
# bit 19..16 to max


# status bits seem to be able to equal to zero
controlledwrite([0x10+0x80, 0, 0xFF, 0x1F, 0x16], chipselect=spio_csz)
# no stealth chop bit 2 to zero
# REGISTER general configuration; addr 0x00
# set_I_scale_analog  bit 0 to 1
# bit 2 to 1  int('0101',2)
controlledwrite([0x00+0x80, 0, 0, 0, int('0101',2)], chipselect=spio_csz)

GPIO.setup(z_step_output, GPIO.OUT)
for step in range(0, steps):
    GPIO.output(z_step_output, GPIO.LOW)
    sleep(halfperiodstep)
    GPIO.output(z_step_output, GPIO.HIGH)
    sleep(halfperiodstep)

GPIO.output(spio_csz, GPIO.HIGH)
GPIO.output(z_enable_output, GPIO.HIGH)  



