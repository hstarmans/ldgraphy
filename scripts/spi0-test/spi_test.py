# @Author: Rik Starmans
# @Company: Hexastorm
# Notes:
#   arduino test class https://github.com/teemuatlut/TMC2130Stepper
#   beaglebone test class https://github.com/hstarmans/TMC2130Stepper
#   you must apply power to motor or driver will not work, all it will return is 255
from Adafruit_BBIO.SPI import SPI
# script to check communication with motors
import Adafruit_BBIO.GPIO as GPIO
# pin definitions
motor_dict = {
        #spio_csx is connected via default SPI chip select"
        'x_step': "P9_41",
        'x_dir': "P9_42",
        'enable': "P9_12",
        'spio_csy': "P9_11",
        'y_step': "P8_12",
        'y_dir': "P8_15",
        'spio_csz': "P8_14",
        'z_step': "P8_16",
        'z_dir': "P8_17",
}

for key in motor_dict.keys():
    # setup pins
    GPIO.setup(motor_dict[key], GPIO.OUT)
spi = SPI(1,0)
spi.mode = 3
# you can also set this via the overlay
spi.msh = int(16000000/8)

def checkcommunication(drive):
    if drive not in ['x', 'y', 'z']:
        print("invalid drive symbol")
        return
    if drive == 'y':
        GPIO.output(motor_dict['spio_csy'], GPIO.LOW)
    else:
        GPIO.output(motor_dict['spio_csy'], GPIO.HIGH) 
    if drive == 'z':
        GPIO.output(motor_dict['spio_csz'], GPIO.LOW)
    else:
        GPIO.output(motor_dict['spio_csz'], GPIO.HIGH)
    if drive == 'x':
        spi.cshigh = False
    else:
        spi.cshigh = True
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
        print("Check is {}".format(res==[1,2,3,4]))
    print("Checking SPI communcation with drive {}".format(drive))
    test()

for drive in ['x', 'y', 'z']:
    checkcommunication(drive)

spi.close()
