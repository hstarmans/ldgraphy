'''
Function which can be used to measure accuracy of Hexastorm via camera

Connects to PiZero Camera and takes pictures
Server side, first start client at Pizero camera.
@company: Hexastorm
@author: Rik Starmans
'''
import sys
import time
from itertools import combinations

from machine import Machine


class Calibrator(Machine):


    def __init__(self):
        super.__init__()


    def check_laserspotbare(self):
        '''
        max travel laserdiode spot over 10 seconds
        if polygon does not move
        '''
        self.set_laser_power(125)
        self.switch_laser(1)
        for i in range(0, 10):
            time.sleep(1)
            self.camera.get_spotinfo()
        pass

    def check_laserspotmoving(self):
        '''
        max travel laserdiode spot over 10 seconds
        if polygon moves
        '''
        pass


    def max_distance(self, lst):
        '''
        returns maximum distance and maximum pair
        of an array of points as dict

        not suited for large data sets, in this case use min,
        max combinations.
        :param lst: list with x,y points, e.g. [[1,2],[2,3]]
        '''
        def square_distance(x,y): 
            return sum([(xi-yi)**2 for xi, yi in zip(x,y)])

        max_square_distance = 0
        for pair in combinations(lst,2):
            if square_distance(*pair) > max_square_distance:
                max_square_distance = square_distance(*pair)
                max_pair = pair  

        return {'distance': max_square_distance, 'pair': max_pair}




