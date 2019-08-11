import Adafruit_GPIO.I2C as I2C
set_value = 80
i2c = I2C.get_i2c_device(0x28, busnum=2) ## 0x28.. changes 0x28 <-> 0x29
i2c.write8(0, set_value)
assert 80 == abs(i2c.readU8(0))
print("Value in registry {}".format(abs(i2c.readU8(0))))
