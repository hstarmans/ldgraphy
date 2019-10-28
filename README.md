# Hexastorm - Laser Direct Lithography


https://www.hexastorm.com/

A process known as Laser Direct Imaging. <br>

<img src="https://cdn.hackaday.io/images/7106161566426847098.jpg" align="center" height="300"/>

The code is based upon [LDGraphy](http://ldgraphy.org/). 


The BOM of the scan head can be found on [Hackaday](https://hackaday.io/project/21933-open-hardware-fast-high-resolution-laser).


## Work in Progress
The project is work on progress. Currently, it is possible to reach a phase-locked loop with the Hexastorm and sent lines to the scanner via Python 3. A resolution below 100 micrometers can be obtained. The stepper motors can be moved and homed via the limit switches. The scanhad is mounted on a frame. The power of the laser can be set via a 
digital potentiometer.
The machine.py file in the machine folder allows you to play around with the machine. The idea is that you work with the machine from the python terminal. The interpolator folder contains a script to calculate the data that needs to be sent to the laser head. The interpolate script cannot be run on the beaglebone as it currently blows through the memory.

## To Do
* if you enable the scan head, you must send some additional stabilization blanks. Ideally, there would be some internal check.
* if the laser module is on for longer than an hour a buffer overflows
* check z-limits and z-homing offset, z home pin doesn't work
* use asyncio loop for stabilizer
* check the speed of polygon in hertz; this might explain why different polygon vendors have such different behavior
* remove state idle from stabilizer
* modify bytes in line
* you need to decide what to do with sync_fail pos
* add updated stabilizer to machine class
* constants are now sprinkled over the python code and duplicate. This is confusing, also see above.

## Install notes

### Image used
The following image was used https://rcn-ee.net/rootfs/bb.org/testing/2019-09-08/stretch-iot/bone-debian-9.10-iot-armhf-2019-09-08-4gb.img.xz

### Steps
Check wether the uio_pruss driver is loaded.
```
lsmod | grep uio
```
There should be something called uio_pruss. If it is not loaded load the module and check again.
```
sudo modprobe uio_pruss 
```
To enable the uio_pruss module on each boot add it to /etc/modules-load.d/modules.conf by adding the line uio_pruss.
An alternative is to load the PRU via the Python module.
Check if you have /dev/uio1 /dev/uio2 etc. 
```
ls /dev/uio*
```
If not modify /boot/uEnv.txt, comment the proc line
```
uboot_overlay_pru=/lib/firmware/AM335X-PRU-RPROC-4-4-TI-00A0.dtbo 
```
uncomment pruss line
```
uboot_overlay_pru=/lib/firmware/AM335X-PRU-UIO-00A0.dtbo .
```
Reboot and check again.
You can get an overview of your beaglebone configuration via
```
sudo /opt/scripts/tools/version.sh .
```
If this doesn't change, your old bootloader in the eMMC might be blocking u-boot overlays, you can fix it via:
```
sudo dd if=/dev/zero of=/dev/mmcblk1 bs=1M count=10
```
Install wheel, Adafruit_BBIO, Adafruit_GPIO and bidict.
```
pip3 install Adafruit_BBIO Adafruit_GPIO bidict
```
Clone [py-uio](https://github.com/mvduin/py-uio) and copy `uio-pruss.rules` file to `/etc/udev/rules.d/` and reboot.
```
pip3 install --src . -e 'git+https://github.com/mvduin/py-uio.git#egg=py-uio'
```
Install the python library for the stepper motors, see [TMC2130Stepper](https://github.com/hstarmans/TMC2130Stepper). <br>
Optionally, install zmq for interaction with a remote camera
```
sudo apt install python3-zmq
```
Install the PRU assembler and prussdrv library as follows:
```
cd ~
git clone https://github.com/beagleboard/am335x_pru_package
cd am335x_pru_package
make
make install
```
Hexastorm works with cape universal. Ensure you allow overlays at ```/boot/uEnv.txt``` and have cape universal enabled. The pins are configured by applying the file hexastorm.bbio from the config-pin directory.
```
config-pin -f hexastorm.bbio
```

## Pins
The status of a pin can be obtained via 
```
config-pin -q 9.91
```
A good pinout view of the [beagle bone](https://beagleboard.org/bone) is available here: <br/>
[P8 header](http://exploringbeaglebone.com/wp-content/uploads/resources/BBBP8Header.pdf) <br/>
[P9 header](http://exploringbeaglebone.com/wp-content/uploads/resources/BBBP9Header.pdf) <br/>


## Slicer
The STL capabilities of the slicer have been removed for now. The slicer used [VTK](https://vtk.org/).
Look into the git history for inspiration.
```
sudo apt install imagemagick
```

[case-pic]: https://www.hexastorm.com/static/laserscanner.jpg
