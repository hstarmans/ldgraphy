#!/bin/sh
set -x
set -e
dtc -O dtb -o stabilizer.dtbo -b 0 -@ stabilizer.dts
cp stabilizer.dtbo /lib/firmware/
