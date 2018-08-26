#!/bin/sh
set -x
set -e
dtc -O dtb -o blinklaser.dtbo -b 0 -@ blinklaser.dts
cp blinklaser.dtbo /lib/firmware/
