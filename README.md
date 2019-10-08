Hexastorm - Laser Direct Lithography
===================================

http://www.hexastorm.com/

A process known as Laser Direct Imaging. <br>

<img src="https://cdn.hackaday.io/images/7106161566426847098.jpg" align="center" height="300"/>

The code is based upon [LDGraphy](http://ldgraphy.org/). 


The BOM of the scan head can be found on [Hackaday](https://hackaday.io/project/21933-open-hardware-fast-high-resolution-laser).


Work in Progress
----------------
The project is work on progress. Currently, it is possible to reach a phase-locked loop with the Hexastorm and sent lines to the scanner via Python 3. A resolution below 100 micrometers can be obtained. The stepper motors can be moved and homed via the limit switches. The scanhad is mounted on a frame. The power of the laser can be set via a 
digital potentiometer.
If someone wants to work with the project it is best to start with the script folder. Here different features can be tested like rotating the prism or setting the power of the laser. 
The interpolator folder contains a script to calculate the data that needs to be sent to the laser head.

To Do
-------------
One program is executed on the CPU side which checks for events and sends lines to the PRU.
This program has influence on the execution of the PRU. This can be deduced from the noise produced by the mirror motor.
A time-out has been set which partly mitigates this problem. Still it exists!!


Image used
--------------
The following image was used https://rcn-ee.net/rootfs/bb.org/testing/2019-09-08/stretch-iot/bone-debian-9.10-iot-armhf-2019-09-08-4gb.img.xz

Enable the PRU
--------------
Check wether the uio_pruss driver is loaded.
```
lsmod | grep uio
```
There should be something called uio_pruss. If it is not loaded load the module and check again.
```
sudo modprobe uio_pruss 
```
To enable the uio_pruss module on each boot add it to /etc/modules-load.d/modules.conf where by adding the line uio_pruss.
An alternative is to load the PRU via the Python module.
check 
```
ls /dev/uio*
```
and see if you have /dev/uio1 /dev/uio2 etc.
If not modify /boot/uEnv.txt, comment the proc line
```
uboot_overlay_pru=/lib/firmware/AM335X-PRU-RPROC-4-4-TI-00A0.dtbo 
```
uncomment pruss line
```
uboot_overlay_pru=/lib/firmware/AM335X-PRU-UIO-00A0.dtbo .
```
Reboot and check again.
You can get an overview your config via
```
sudo /opt/scripts/tools/version.sh .
```
If it doesnt' work, your old bootloader in the eMMC is blocking u-boot overlays, you can fix it via:
```
sudo dd if=/dev/zero of=/dev/mmcblk1 bs=1M count=10
```
Hexastorm works with cape universal. The pins are configured by applying the file hexastorm.bbio from the config-pin directory.
```
config-pin -f hexastorm.bbio
```
Clone [py-uio](https://github.com/mvduin/py-uio) and copy `uio-pruss.rules` file to `/etc/udev/rules.d/` and reboot.
```
pip3 install --src . -e 'git+https://github.com/mvduin/py-uio.git#egg=py-uio'
```
Install Adafruit_BBIO
```
pip3 install Adafruit_BBIO
```
Install Adafruit_GPIO
```
pip3 install Adafruit_GPIO
```

Install pasm
------------
Install the PRU assembler and prussdrv library as follows:
```
cd ~
git clone https://github.com/beagleboard/am335x_pru_package
cd am335x_pru_package
make
make install
```

Device tree overlay
--------------------
To properly prepare the GPIOs and the PRU to be used, you have to install
the device tree overlay on your Beaglebone.
Compile the DTS to a DTBO and move it to /lib/firmware folder.
Load the DTS via uboot with the custom cape variable, dtboverlay.
In the laser test we have
```
dtb_overlay=/lib/firmware/hexastorm.dtbo
```
You can check whether it is working via;
```
export PINS=/sys/kernel/debug/pinctrl/44e10800.pinmux/pins
cat $PINS | grep 'pin 101'
```
A good pinout view of the beagle bone is available here: <br/>

[P8 header](http://exploringbeaglebone.com/wp-content/uploads/resources/BBBP8Header.pdf) <br/>
[P9 header](http://exploringbeaglebone.com/wp-content/uploads/resources/BBBP9Header.pdf) <br/>


Slicer
-------
The STL capabilities of the slicer has been removed for now. Look into the git history for inspiration.
```
sudo apt install imagemagick
```



Tests
--------------
Laser <br />
Plug in the 5V and 12V source for the cape, so the laser driver has power.
Hook the fan to the board, it should spin. Run the following lines of code;
```
echo 110 > /sys/class/gpio/export
echo high > /sys/class/gpio/gpio110/direction
echo low > /sys/class/gpio/gpio110/direction
cat /sys/class/gpio/gpio110/direction
cat /sys/class/gpio/gpio110/value
ls -al /sys/class/gpio
```
If the laserdiode does not turn on it could be broken or the laserdiode driver could be broken.
Hook the fan to the laserdiode output and see if it spins. If it does the laserdiode is broken.
There is also a test script, 
ldgraphy/scripts/firestarter_tests/laserdriver.py <br/>
Polygon driver <br/>
Run the test script ldgraphy/scripts/firestarter_tests/polydriver.py <br/>
The polygon should spin. Two types of polygon were considered.
The MASQ6DF15RS which are sold with a maximum speed of 24000 RPM although a label indicates they spin at 20787 RPM. A Chinese sticker has been placed to cover this number. The chip used is Panasonic AN44000A. The MASQ0DF9RV rotate at 21000 RPM. The chip used is NBC3111.
It was found at that both the input and output of these chips are different and the Panasonic chip rotates the polygon faster than what would be expected of a given pulse rate. We therefore chose to proceed with the NBC3111. The pulse pin of the Panasonic is AN44000A.

Photodiode <br/>
The python library is broken, so a python test script could not be made.
Turn on the laser via the command line. 
```
echo 110 > /sys/class/gpio/export
echo high > /sys/class/gpio/gpio110/direction
```
Rotate the prism and measure the photodiode input. Pin 20 or pin 116 can be used.
```
echo 20 > /sys/class/gpio/export
echo in > /sys/class/gpio/gpio20/direction
cat /sys/class/gpio/gpio20/value
```





[case-pic]: https://www.hexastorm.com/static/laserscanner.jpg
