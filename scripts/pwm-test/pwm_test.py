import Adafruit_BBIO.PWM as PWM
from time import sleep

PWM.start("P8_19", 50, 1)
sleep(10)
PWM.stop("P8_19")
PWM.cleanup()
