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
import numpy as np

from machine import Machine


class Calibrator(Machine):


    def __init__(self, camera = True):
        super().__init__(camera)


    def check_laserspotbare(self, power=90, ms=0.12, repetitions=10):
        '''
        max travel laserdiode spot over repitions, polygon disabled

        preliminary experiments indicate ellipse is more stable measure
        :param power: laser power
        :param ms: exposure time camera in miliseconds
        :param repetitions: number of repitions
        '''
        self.set_laser_power(power)
        self.camera.set_exposure(ms)
        positions = list()
        axes = np.zeros(2)
        for i in range(0, repetitions):
            self.switch_laser(1)
            spotinfo = self.camera.get_spotinfo()
            if not spotinfo:
                print("Can't detect spot")
                return
            positions.append(spotinfo['position'])
            axes += spotinfo['axes']
            self.switch_laser(0)

        return axes/repetitions, self.max_distance(positions)


    def check_laserspotmoving(self, power=100, pixel=3600,  
                        ms=30, repetitions=1, polygonswitch=False,
                        singlefacet=False):
        '''
        max travel laserdiode spot, polygon enabled

        :param power: laser power, use None for boards without digipot
        :param pixel: pixel number, starts at zero
        :param ms: exposure time camera in miliseconds
        :param repetitions: number of repetitions
        :param polygonswich: turn on/off polygon each iteration 
        '''
        self.line = np.zeros(self.bytesinline, dtype=np.uint8)
        self.line[pixel//8] = 1 << (7-pixel%8)
        if singlefacet:
            self.fourlines = np.concatenate(self.line, np.zeros(self.bytesinline*3,
                dtype=np.uint8))
        else:
            self.fourlines = np.tile(self.line, 4).astype(np.uint8)
        if power:
            self.set_laser_power(power)
        self.camera.set_exposure(ms)
        positions = list()
        centroids = list()
        print("Waiting for enable to finish")
        axes = np.zeros(2)
        for i in range(0, repetitions):
            time.sleep(1)
            if polygonswitch:
                print("Switching on polygon at switch true")
                self.enable_scanhead()
            line_data = np.tile(self.fourlines, 160).astype(np.uint8)
            spotinfo = self.expose(line_data,
                    takepicture = True)
            if not spotinfo:
                if polygonswitch:
                    self.disable_scanhead()
                return
            positions.append(spotinfo['position'])
            centroids.append(spotinfo['centroid'])
            axes += spotinfo['axes']
            if polygonswitch:
                print("Switching off polygon at switch true")
                self.disable_scanhead()
        #NOTE: you're killing data in axes... might not be good
        return axes/repetitions, positions, centroids

    # compute average and distance, STDV from mean point
    # code below is sort of maxim
    def max_distance(self, lst):
        '''
        returns maximum distance and maximum pair
        of an array of points as dict

        not suited for large data sets, in this case use min,
        max combinations.
        :param lst: list with x,y points, e.g. [[1,2],[2,3]]
        '''
        if len(lst) == 1:
            return {'distance': 0, 'pair': 'one element'}
        def square_distance(x,y): 
            return sum([(xi-yi)**2 for xi, yi in zip(x,y)])

        max_square_distance = 0
        for pair in combinations(lst,2):
            if square_distance(*pair) > max_square_distance:
                max_square_distance = square_distance(*pair)
                max_pair = pair  

        return {'distance': pow(max_square_distance, 0.5),
                'pair': max_pair}
