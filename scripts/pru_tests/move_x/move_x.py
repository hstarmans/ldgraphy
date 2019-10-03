from time import sleep
import Adafruit_BBIO.GPIO as GPIO

# INPUT
XSTEPSPERMM = 76.2
STEPSPEED = round(1*XSTEPSPERMM)
STEPS = round(100*XSTEPSPERMM)
DIRECTION = True # false is direction home for x-axis

x_direction_pin = "P9_42"
enable_pin = "P9_12"
step_pin = "P9_41"

GPIO.setup(enable_pin, GPIO.OUT)


GPIO.setup(x_direction_pin, GPIO.OUT)

GPIO.setup(step_pin, GPIO.OUT)
if DIRECTION:
    GPIO.output(x_direction_pin, GPIO.HIGH)
else:
    GPIO.output(x_direction_pin, GPIO.LOW)

#GPIO.output(enable_pin, GPIO.LOW)


#GPIO.output(step_pin, GPIO.HIGH)
#GPIO.cleanup()

#GPIO.output(step_pin, GPIO.LOW)
#input()

HALF_PERIOD = 1/(STEPSPEED*2)

for step in range(0,STEPS):
    sleep(HALF_PERIOD)
    GPIO.output(step_pin, GPIO.LOW)
    GPIO.output(step_pin, GPIO.LOW)
    sleep(HALF_PERIOD)
    GPIO.output(step_pin, GPIO.HIGH)

    
