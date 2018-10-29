import numpy as np
from machine import Machine


FILENAME = 'test.bin' 
FACETS_IN_LANE = 5377
LANEWIDTH = 9.33999
PIXELS_IN_LINE = 171
MULTIPLIER = 10

prototype = Machine()
print("Homing x")
prototype.home('x')
print("Homing y")
prototype.home('y')
print("Reading binary")
data = np.fromfile(FILENAME, dtype = np.uint8)
pix_inlane = FACETS_IN_LANE * PIXELS_IN_LINE
for lane in range(0, round(len(data)/(pix_inlane))):
    if lane > 0:
        print("Moving in x-direction for next lane")
        prototype.move([prototype.position[0]+LANEWIDTH, prototype.position[1]])
    if lane % 2 == 1:
        direction = False
        print("Start exposing back lane")
    else:
        direction = True
        print("Start exposing forward lane")
    prototype.expose(data[lane*pix_inlane:(lane+1)*pix_inlane], direction, MULTIPLIER, move=True)
print("Finished exposure")

    
