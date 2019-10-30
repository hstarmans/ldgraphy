'''
Function which can be used to print layer

Run as standalone script

@company: Hexastorm
@author: Rik Starmans
'''
import numpy as np
from machine import Machine
from time import sleep

FILENAME = 'test.bin' 
FACETS_IN_LANE = 5377
LANEWIDTH = 8.34751
BYTES_IN_LINE = 790
MULTIPLIER = 1
MOVE = False

prototype = Machine()

if MOVE:
    print("Homing x")
    prototype.home('x')
    print("Homing y")
    prototype.home('y')
    print("Moving to start")
    prototype.move([prototype.position[0], prototype.position[1]+70, 0])
print("Reading binary")
data = np.fromfile(FILENAME, dtype = np.uint8)
bytes_inlane = FACETS_IN_LANE * BYTES_IN_LINE
prototype.enable_scanhead()
for lane in range(1, round(len(data)/(bytes_inlane))):
    print("Exposing lane {}".format(lane))
    if lane > 0:
        print("Moving in x-direction for next lane")
        if MOVE:
            prototype.move([prototype.position[0]+LANEWIDTH, prototype.position[1], 0])
    if lane % 2 == 1:
        direction = False 
        print("Start exposing forward lane")
    else:
        direction = True # disabled direction
        print("Start exposing back lane")
    line_data = data[lane*bytes_inlane:(lane+1)*bytes_inlane]
    # reverse, as exposure is inversed
    line_data = line_data[::-1]
    prototype.expose(line_data, direction, MULTIPLIER, move=MOVE)
prototype.disable_scanhead()
print("Finished exposure")

    
