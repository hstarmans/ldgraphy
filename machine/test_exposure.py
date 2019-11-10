'''
Function which can be used to print a test exposure

Run as standalone script. There are four ways in which
the dosage can be altered; revolutions per minute or prism,
multiple exposures per line, the current setting of the 
laser driver and the downsample factor in the slicer.
The test creates squares with a size of 8x8 mm, using
different multiplier settings from one up to five. 

@company: Hexastorm
@author: Rik Starmans
'''
import numpy as np
from machine import Machine
from time import sleep

MOVE = False 

prototype = Machine(stepper=MOVE)

FILENAME = 'test.bin' 
FACETS_IN_LANE = 100
LANEWIDTH = 8.34751  # measured
HEIGHT = 10          # height 
ZONE_THICKNESS  = 1  # 
LINES_PER_ZONE = round((ZONE_THICKNESS/prototype.SLED_SPEED)*(prototype.RPM/60)*prototype.FACETS)
# idea is a pattern
# * ------- * ----  (lines per zone thick) 
# ----------------  (lines per zone thick)
# ...  (repeated until height is filled)
TOTAL_LANES = 4
MULTIPLIER = 1

# expose data creation
# downsample factor in slicer is 5, so 5x1 is one pixel
data_byte = [int('11111000', 2)]*1+[int('00000000',2)]*31
data_line = (data_byte*(prototype.SCANLINE_DATA_SIZE//len(data_byte)) + 
        prototype.SCANLINE_DATA_SIZE%len(data_byte)*[int('00000000',2)])
blank_line = [0]*prototype.SCANLINE_DATA_SIZE
forward_block = data_line*LINES_PER_ZONE + blank_line * LINES_PER_ZONE
forwardlane_data = np.array(round(HEIGHT/(2*ZONE_THICKNESS))*forward_block, dtype='uint8')
backward_block = blank_line * LINES_PER_ZONE + data_line*LINES_PER_ZONE
backwardlane_data = np.array(round(HEIGHT/(2*ZONE_THICKNESS))*backward_block, dtype='uint8')

if MOVE:
    print("Homing x")
    prototype.home('x')
    print("Homing y")
    prototype.home('y')
    print("Moving to start")
    prototype.move([prototype.position[0], prototype.position[1]+70, prototype.position[2]])


prototype.enable_scanhead()
for lane in range(1, TOTAL_LANES):
    print("Exposing lane {}".format(lane))
    if lane > 0:
        print("Moving in x-direction for next lane")
        if MOVE:
            prototype.move([prototype.position[0]+LANEWIDTH, prototype.position[1], prototype.position[2]])
    if lane % 2 == 1:
        print("Start exposing forward lane")
        direction = False 
    else:
        print("Start exposing back lane")
        direction = True 
    prototype.expose(backwardlane_data, direction, multiplier = lane, move = MOVE)

prototype.disable_scanhead()
print("Finished exposure")
