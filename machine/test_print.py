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
MULTIPLIER = 1
MOVE = False

prototype = Machine(stepper=MOVE)

if MOVE:
    print("Homing x")
    prototype.home('x')
    print("Homing y")
    prototype.home('y')
    print("Moving to start")
    prototype.move([prototype.position[0], prototype.position[1]+70, 0])

print("Reading binary")
data = np.fromfile(FILENAME, dtype = np.uint8)
bytes_inlane = FACETS_IN_LANE * prototype.SCANLINE_DATA_SIZE
if len(data)%(bytes_inlane):
    raise Exception("Number of lanes is not an integer {}".format(len(data)/bytes_inlane))

prototype.enable_scanhead()
for lane in range(0, round(len(data)/bytes_inlane)):
    print("Exposing lane {}".format(lane))
    if lane > 0:
        print("Moving in x-direction for next lane")
        if MOVE:
            prototype.move([prototype.position[0]+LANEWIDTH, prototype.position[1], 0])
    if lane % 2 == 1:
        direction = False 
        print("Start exposing forward lane")
    else:
        direction = True 
        print("Start exposing back lane")
    line_data = data[lane*bytes_inlane:(lane+1)*bytes_inlane]
    # this reversion should not be needed and indicates something is off at the slicer
    line_data = line_data[::-1]
    byte = prototype.expose(line_data, direction, multiplier=MULTIPLIER, move=MOVE)

prototype.disable_scanhead()
print("Finished exposure")

    
