Hexastorm - Laser Direct Lithography
===================================

http://www.hexastorm.com/

A process known as Laser Direct Imaging.

<img src="https://www.hexastorm.com/static/laserscanner.jpg" align="center" height="300"/>

The code is based upon [LDGraphy](http://ldgraphy.org/).

Goal is to have this Open Source/Open Hardware laser scanner easy to reproduce with
commonly available parts. The BOM is in the order of $200 including the
Beaglebone Green.

  * 500mW 405nm laser ($30)
  * Commonly available polygon mirror scanner (from laser printers) ($20)
  * Beaglebone Black/Green to control it all (using the PRU to generate precise
    timings for motors and laser) ($40)
  * quartz optical window, 2 mm thick, 30x30 mm ($55)
  * Photo-diode to determine start-of-line (as the polygon mirrors have
    slightly different long faces and also phase-drift over time) (BPW34-B) ($5)
  * Hexastorm hat ($50)


Work in Progress
----------------
The project is work on progress. The first goal is to modify the original LDgraphy code and reach a phase-lock loop.

Compile
-------
This compiles on a BeagleBone Green/Black; it requires the PRU on these
computers for hard realtime-switching of the Laser.

```
git clone --recursive https://github.com/hzeller/ldgraphy.git
```

Install relevant packages. We are reading png-images as input, so we need the
library that helps us with that (probably already installed on your system):
```
sudo apt-get update
sudo apt-get install libpng-dev -y
```
The pru package must be cloned manually
```
git clone https://github.com/hzeller/am355x_pru_package.git
```
Then compile:
```
cd ldgraphy/src
make
```

To properly prepare the GPIOs and the PRU to be used, you have to install
the device tree overlay on your Beaglebone:
```
cd ldgraphy/device-tree
sudo ./start-devicetree-overlay.sh LDGraphy.dts
```
You can check whether it is working via;
```
cat /sys/kernel/debug/pinctrl/44e10800.pinmux/pins
cat /sys/devices/platform/bone_capemgr/slots
```
Enable the PRU
https://gist.github.com/jonlidgard/1d9e0e92b4f219f3f40edfed260b851e
https://www.cs.sfu.ca/CourseCentral/433/bfraser/other/2014-student-howtos/pru-guide.pdf

The command you tried is sudo ./ldgraphy -S -D0.15:0.04,0.01

The input is a PNG image. For converting Gerber files to PNG, see the
`gerber2png` tool in the [scripts/](./scripts) directory.

Usage:
```
Usage:
./ldgraphy [options] <png-image-file>
Options:
        -d <val>   : Override DPI of input image. Default -1
        -i         : Inverse image: black becomes laser on
        -x<val>    : Exposure factor. Default 1.
        -o<val>    : Offset in sled direction in mm
        -R         : Quarter image turn left; can be given multiple times.
        -h         : This help
Mostly for testing or calibration:
        -S         : Skip sled loading; assume board already loaded.
        -E         : Skip eject at end.
        -F         : Run a focus round until Ctrl-C
        -M         : Testing: Inhibit sled move.
        -n         : Dryrun. Do not do any scanning; laser off.
        -j<exp>    : Mirror jitter test with given exposure repeat
        -D<line-width:start,step> : Laser Dot Diameter test chart. Creates a test-strip 10cm x 2cm with 10 samples.
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


Current issues
--------------
i2c is already in use; so you can't modify it you have to disable i2c
http://www.embedded-things.com/bbb/enable-canbus-on-the-beaglebone-black/


[case-pic]: https://www.hexastorm.com/static/laserscanner.jpg
