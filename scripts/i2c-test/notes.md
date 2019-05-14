#
I2C device 2 is automatically enabled, so you dont need to do this by the overlay.
Firestarter v0.1 disabled I2c device 2 and enabled I2C device 1.
I2C device 0 is always active, so you typically use device 1 or 2 on your board.

# list devices
i2cdetect -l
i2cdetect -r 2
