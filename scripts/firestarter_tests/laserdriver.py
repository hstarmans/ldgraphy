import Adafruit_BBIO.GPIO as GPIO
from time import sleep

laser_output = "P9_29"
loops = 3

GPIO.setup(laser_output, GPIO.OUT)
print("Loop runs " + str(loops) + " times")
for i in range(0,loops):
    print("Loop "+str(i))
    print("Turning laser on for 3 seconds")
    GPIO.output(laser_output, GPIO.HIGH)
    sleep(3)
    print("Turning laser off for 3 seconds")
    GPIO.output(laser_output, GPIO.LOW)
    sleep(3)

