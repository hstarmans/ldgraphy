""" blinkled.py - test script for the PyPRUSS library
blinks the laser 3 times with a period of 6 seconds
"""

import pypruss

#pypruss.modprobe()        # This only has to be called once pr boot
pypruss.init()                                      
pypruss.open(0)                                     
pypruss.pruintc_init()                              
pypruss.exec_program(0, "./blinklaser.bin")    
pypruss.wait_for_event(0)                           
pypruss.clear_event(0,pypruss.PRU0_ARM_INTERRUPT)    
pypruss.pru_disable(0)                              
pypruss.exit()                                      
