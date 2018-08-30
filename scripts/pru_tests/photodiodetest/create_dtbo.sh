#!/bin/sh
set -x
set -e
dtc -O dtb -o photodiodetest.dtbo -b 0 -@ photodiodetest.dts
cp photodiodetest.dtbo /lib/firmware/
