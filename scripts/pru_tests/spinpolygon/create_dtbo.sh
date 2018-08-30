#!/bin/sh
set -x
set -e
dtc -O dtb -o spinpolygon.dtbo -b 0 -@ spinpolygon.dts
cp spinpolygon.dtbo /lib/firmware/
