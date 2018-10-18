#!/bin/sh
set -x
set -e
#rm hexastorm.dtbo
#rm /lib/firmware/hexastorm.dtbo
dtc -W no-unit_address_vs_reg -O dtb -o hexastorm.dtbo -b 0 -@ hexastorm.dts
cp hexastorm.dtbo /lib/firmware/
