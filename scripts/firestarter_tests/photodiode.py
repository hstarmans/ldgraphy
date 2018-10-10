# code does not work!! due to library failure
# laser should be turned on, polygon spinned and then photodiode measured

import Adafruit_BBIO.GPIO as GPIO
from time import sleep

laser_output = "P9_29"
photodiode_input = "P9_41"
loops = 3

GPIO.setup(laser_output, GPIO.OUT)
GPIO.output(laser_output, GPIO.HIGH)
print("Turning laser on")
GPIO.setup(photodiode_input, GPIO.IN)
old = False
while True:
    new = GPIO.input(photodiode_input)
    if new is not old:
        old = new
        if new:
            print("Photodiode HIGH")
        else:
            print("Photodiode LOW")
    sleep(1)

