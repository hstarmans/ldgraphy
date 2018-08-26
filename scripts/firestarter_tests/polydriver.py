import Adafruit_BBIO.GPIO as GPIO
from time import sleep

poly_frequency = 1000 # max is 2.1 kHz
poly_pwm = "P9_27"
poly_ready = "P9_18"
poly_enable = "P9_25"

GPIO.setup(poly_pwm, GPIO.OUT)
GPIO.setup(poly_enable, GPIO.OUT)
poly_time = 1.0/(poly_frequency*2)
print("Polygon spins indefinitely at " + str(poly_frequency) + " Hertz.")
while True:
    GPIO.output(poly_pwm, GPIO.HIGH)
    sleep(poly_time)
    GPIO.output(poly_pwm, GPIO.LOW)
    sleep(poly_time)

