after applying cape (dts file), SPIO will present under /dev/spidev1.0, no additional options are needed

registers are volatile, you will have to apply settings every boot

two related libraries;
https://github.com/alangibson/steppyr
https://github.com/makertum/Trinamic_TMC2130

only option seems
https://github.com/teemuatlut/TMC2130Stepper

port this library to beaglebone

