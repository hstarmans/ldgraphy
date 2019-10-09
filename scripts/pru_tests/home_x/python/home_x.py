from time import sleep
import Adafruit_BBIO.GPIO as GPIO

# INPUT
XSTEPSPERMM = 76.2
STEPSPEED = round(1*XSTEPSPERMM)
STEPS_LIMIT = round(100*XSTEPSPERMM)
DIRECTION = False # false is direction home for x-axis

x_direction_pin = "P9_42"
enable_pin = "P9_12"
step_pin = "P9_41"
x_endstop = "P9_15"

GPIO.setup(enable_pin, GPIO.OUT)
GPIO.setup(x_direction_pin, GPIO.OUT)
GPIO.setup(step_pin, GPIO.OUT)
GPIO.setup(x_endstop, GPIO.IN)

if DIRECTION:
    GPIO.output(x_direction_pin, GPIO.HIGH)
else:
    GPIO.output(x_direction_pin, GPIO.LOW)

GPIO.output(enable_pin, GPIO.LOW)

HALF_PERIOD = 1/(STEPSPEED*2)

for step in range(0,STEPS_LIMIT):
    if GPIO.input(x_endstop):
        break
    sleep(HALF_PERIOD)
    GPIO.output(step_pin, GPIO.LOW)
    sleep(HALF_PERIOD)
    GPIO.output(step_pin, GPIO.HIGH)
    if step == STEPS_LIMIT-1:
        print("Can't home")

GPIO.output(enable_pin, GPIO.HIGH)
