#!/bin/sh
set -x
set -e
dtc -O dtb -o hexastorm.dtbo -b 0 -@ hexastorm.dts
cp hexastorm.dtbo /lib/firmware/
