# @Author: Rik Starmans
# @Company: Hexastorm
# Notes:
#   c++ class here https://github.com/teemuatlut/TMC2130Stepper, class is easy to test on Arduino
#   you must apply power to motor or driver will not work, all it will return is 255
from Adafruit_BBIO.SPI import SPI
import Adafruit_BBIO.GPIO as GPIO
# disable y-select
spio_csy = "P9_11"
GPIO.setup(spio_csy, GPIO.OUT)
GPIO.output(spio_csy, GPIO.HIGH) 
# disable z-select
spio_csz = "P8_14"
GPIO.setup(spio_csz, GPIO.OUT)
GPIO.setup(spio_csz, GPIO.HIGH)
# connect to SPI
spi = SPI(1,0)

# use SPI mode 3
spi.mode = 3
# stepper motor cannot handle default speed
# you can also set this in cape
spi.msh = int(16000000/8)
# lists send through xfer2 are altered!
#  so
#  data = [0xEC, 1 , 2, 3, 4]
#  res = spi.xfer2(data) --> data is changed!!
# 
def test():
    # datasheet; https://www.trinamic.com/fileadmin/assets/Products/ICs_Documents/TMC2130_datasheet.pdf
    # let's try example on page 22
    # write to chopconf and see if data is returned
    spi.writebytes([0xEC, 1, 2, 3, 4])
    res = spi.readbytes(5)
    spi.writebytes([0xEC, 1, 2, 3, 4])
    res = spi.readbytes(5)[1:5]
    print("Check 1 is {}".format(res==[1,2,3,4]))
print("Checking SPIO communication with steppers")
print("Checking x-stepper")
test()
# check if you receive 1,2,3,4
print("Checking y-stepper")
spi.cshigh = True
GPIO.output(spio_csy, GPIO.LOW)
test()
print("Checking z-stepper")
GPIO.output(spio_csy, GPIO.HIGH)
GPIO.output(spio_csz, GPIO.LOW)
test()
spi.close()