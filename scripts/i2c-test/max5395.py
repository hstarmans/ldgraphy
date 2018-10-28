import Adafruit_GPIO.I2C as I2C
i2c = I2C.get_i2c_device(0x28)
i2c.write8(0, 128)
print("Value in registry {}".format(abs(i2c.readU8(0))))
