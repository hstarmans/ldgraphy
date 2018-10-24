'''
@company: Hexastorm
@author: Rik Starmans
'''

import math
import os

import numpy as np
from scipy import ndimage
from PIL import Image


class Interpolator:
    '''
    This object calculates the binanry laser diode information for the Hexastorm.

    A post script file is converted to a numpy array. 
    The positions of the laserdiode are calculated via the function createcoordinates. The function patternfiles interpolates
    the array created. These values are either 0 (laser off) or 1 (laser on). The slicer object has convenience functions 
    to write and read the binary files which can be pushed to the PRU.
    '''

    def __init__(self):
        # PARAMETERS
        self.tiltangle = np.radians(90)   # angle [radians], for a definition see figure 7
                                          # https://reprap.org/wiki/Transparent_Polygon_Scanning
        self.laserfrequency = 42720       # the laser frequency [Hz]
        self.rotationfrequency = 2400/60  # rotation frequency polygon [Hz]
        self.facets = 4                   # number of facets
        self.inradius = 15                # inradius polygon [mm]
        self.n = 1.49                     # refractive index
        self.pltfxsize = 200              # platform size scanning direction [mm]
        self.pltfysize = 200              # platform size stacking direction [mm]
        self.samplexsize = 0              # sample size scanning direction [mm]
        self.sampleysize = 0              # sample size stacking direction [mm] 
        self.samplegridsize = 0.05        # height/width of the sample gridth [mm]
        self.stagespeed = 4.8             # mm/s
        self.startpixel = 10              # pixel determine via camera
        self.pixelsinline = 230           # number of pixels in a line


    def pstoarray(self, url):
        '''converts postscript file to an array

        :param url: path to postcript file
        '''
        psppoint = 0.3527777778 # post script pixel in mm
        tmp = Image.open(url)
        x_size, y_size = [i*psppoint for i in tmp.size]
        if x_size > self.pltfxsize or y_size > self.pltfysize:
            raise Exception('Object does not fit on platform')
        #NOTE: this is only a crude approximation
        self.samplexsize, self.sampleysize = x_size, y_size
        scale = psppoint/self.samplegridsize
        tmp.load(scale = scale)
        tmp_array = np.array(tmp.convert('1'))
        if tmp_array.max() == 0:
            raise Exception("Postscript file is empty")
        return tmp_array


    def displacement(self, pixel):
        '''
        returns the displacement for a given pixel

        The x-axis is parallel to the scanline if the stage does not move.
        It is assumed, the laser bundle traverses in the negative direction if the polygon rotates.
        :param pixel; the pixelnumber, in range [0, self.pixelsfacet]
        '''
        # interiorangle = 180-360/self.n
        # max_angle = 180-90-0.5*interiorangle
        max_angle = 180/self.facets
        pixelsfacet = round(self.laserfrequency/(self.rotationfrequency*self.facets))
        angle = np.radians(- 2 * max_angle * (pixel/pixelsfacet) + max_angle)
 
        disp = (self.inradius*2*np.sin(angle)*(1-np.power((1-np.power(np.sin(angle),2))/
                                            (np.power(self.n,2)-np.power(np.sin(angle),2)),0.5)))
        return disp


    def fxpos(self, pixel, xstart = 0):
        '''
        returns the laserdiode x-position in pixels

        The x-axis is parallel to the scanline if the stage does not move.
        :param pixel: the pixelnumber in the line
        :param xstart: the x-start position [mm], typically your xstart is larger than 0
                       as the displacement can be negative
        '''
        line_pixel = self.startpixel + pixel % self.pixelsinline
        xpos = np.sin(self.tiltangle)*self.displacement(line_pixel) + xstart
        return xpos/self.samplegridsize


    def fypos(self, pixel, direction, ystart = 0):
        '''
        returns the laserdiode y-position in pixels

        The y-asis is orthogonal to the scanline if the stage does not move.
        :param pixel: the pixelnumber in the line
        :param direction: True is +, False is -
        :param ystart: the y-start position [mm]
        '''
        line_pixel = self.startpixel + pixel % self.pixelsinline
        if direction:
            ypos = -np.cos(self.tiltangle)*self.displacement(line_pixel)
            ypos += line_pixel/self.laserfrequency*self.stagespeed + ystart
        else:
            ypos = -np.cos(self.tiltangle)*self.displacement(line_pixel) 
            ypos -= line_pixel/self.laserfrequency*self.stagespeed + ystart
        
        return ypos/self.samplegridsize


    def createcoordinates(self):
        '''
        returns the x, y position of the laserdiode for each pixel, for all lanes

        assumes the line starts at the positive plane 
        '''
        if not self.sampleysize or not self.samplexsize:
            raise Exception('Sampleysize or samplexsize are set to zero.')
        if self.fxpos(0) < 0 or self.fxpos(self.pixelsinline-1) > 0:
            raise Exception('Line seems ill positioned')
        lanewidth = (self.fxpos(0)-self.fxpos(self.pixelsinline-1))*self.samplegridsize  # mm
        lanes = math.ceil(self.samplexsize/lanewidth)
        facets_inlane = math.ceil(self.rotationfrequency * self.facets * (self.sampleysize/self.stagespeed))
        # single facet
        vfxpos = np.vectorize(self.fxpos)
        vfypos = np.vectorize(self.fypos)
        xstart = self.fxpos(self.pixelsinline-1)*self.samplegridsize
        # you still don't account for ystart
        xpos_facet = vfxpos(range(0, self.pixelsinline), xstart)
        ypos_forwardfacet = vfypos(range(0, self.pixelsinline), True)
        ypos_backwardfacet = vfypos(range(0, self.pixelsinline), False)
        # single lane
        xpos_lane = xpos_facet.tolist() * facets_inlane
        ypos_forwardlane = []
        ypos_backwardlane = []
        for facet in range(0, facets_inlane):
            ypos_forwardtemp = ypos_forwardfacet + (facet*self.stagespeed)/(self.facets*self.rotationfrequency*self.samplegridsize)
            ypos_backwardtemp = ypos_backwardfacet + ((facets_inlane-facet)*self.stagespeed)/(self.facets*self.rotationfrequency*self.samplegridsize)
            ypos_forwardlane += ypos_forwardtemp.tolist()
            ypos_backwardlane += ypos_backwardtemp.tolist()
        # all lanes
        xpos_lane = np.array(xpos_lane)
        xpos = []
        ypos = []
        for lane in range(0, lanes):
            xpos_temp = xpos_lane + lane * (self.fxpos(0)-self.fxpos(self.pixelsinline-1))
            if lanes % 2 == 1:
                ypos_temp = ypos_backwardlane
            else:
                ypos_temp = ypos_forwardlane
            xpos += xpos_temp.tolist()
            ypos += ypos_temp
        #NOTE: float leads to additional patterns in the final slice
        print(max(xpos))
        print(max(ypos))
        ids = np.concatenate(([np.array(xpos)], [np.array(ypos)]))
        return ids


    def patternfile(self, url):
        '''returns the pattern file as numpy array

        mostly a convenience function which wraps other functions in this class
        :param url: path to postscript file
        '''
        from time import time
        ctime = time()
        layerarr = self.pstoarray(url)
        print("Retrieved layerarr")
        print("elapsed {}".format(time()-ctime))
        ids = self.createcoordinates()
        print("Retrieved coordinates")
        print("elapsed {}".format(time()-ctime))
        #TODO: test
        # values outside image are mapped to 0
        print(layerarr.min())
        print(layerarr.max())
        print(layerarr.shape)
        ptrn = ndimage.map_coordinates(input=layerarr, output=np.uint8, coordinates=ids, order=1, mode="constant", cval=0)
        print(ptrn.min())
        print(ptrn.max())
        # max array is set to one
        print("Completed interpolation")
        print("elapsed {}".format(time()-ctime))
        print("Final shape {}".format(ptrn.shape))
        return ptrn


    def plotptrn(self, ptrn, step, filename = 'plot'):
        '''
        function can be used to plot a pattern file. The result is return as numpy array
        and stored in script folder under the name "plot.png"

        :param ptrnfile: result of the functions patternfiles
        :param step: pixel step, can be used to lower the number of pixels that are plotted 
        :param filename: filename to store pattern
        '''
        currentdir = os.path.dirname(os.path.realpath(__file__))
        # the positions are constructed
        vfxpos = np.vectorize(self.fxpos) 
        vfypos = np.vectorize(self.fypos)

        # NOTE: coordinates are created similarly to create coordinates
        lanewidth = (self.fxpos(0)-self.fxpos(self.pixelsinline-1))*self.samplegridsize  # mm
        lanes = math.ceil(self.samplexsize/lanewidth)
        facets_inlane = math.ceil(self.rotationfrequency * self.facets * (self.sampleysize/self.stagespeed))
        # single facet
        vfxpos = np.vectorize(self.fxpos)
        vfypos = np.vectorize(self.fypos)
        xstart = self.fxpos(self.pixelsinline-1) #TODO: make sure you account for this in your movement
        xpos_facet = vfxpos(range(0, self.pixelsinline), xstart)
        ypos_forwardfacet = vfypos(range(0, self.pixelsinline), True)
        ypos_backwardfacet = vfypos(range(0, self.pixelsinline), False)
        # single lane
        xpos_lane = xpos_facet.tolist() * facets_inlane
        ypos_forwardlane = []
        ypos_backwardlane = []
        for facet in range(0, facets_inlane):
            ypos_forwardtemp = ypos_forwardfacet + (facet*self.stagespeed)/(self.facets*self.rotationfrequency*self.samplegridsize)
            ypos_backwardtemp = ypos_backwardfacet + ((facets_inlane-facet)*self.stagespeed)/(self.facets*self.rotationfrequency*self.samplegridsize)
            ypos_forwardlane += ypos_forwardtemp.tolist()
            ypos_backwardlane += ypos_backwardtemp.tolist()
        # all lanes
        xpos_lane = np.array(xpos_lane)
        xpos = []
        ypos = []
        for lane in range(0, lanes):
            xpos_temp = xpos_lane + lane * (self.fxpos(0)-self.fxpos(self.pixelsinline-1))
            if lanes % 2 == 1:
                ypos_temp = ypos_backwardlane
            else:
                ypos_temp = ypos_forwardlane
            xpos += xpos_temp.tolist()
            ypos += ypos_temp
        #NOTE: end note
        # if this is not done, operation becomes too slow
        # conversion to int needed, as array indices must be integer
        xcor = np.array(xpos[::step]).astype(np.int32, copy=False)
        ycor = np.array(ypos[::step]).astype(np.int32, copy=False)
        # x and y cannot be negative
        if xcor.min()< 0:
            xcor += abs(xcor.min())
        if ycor.min()< 0:
            ycor += abs(ycor.min())
        # number of pixels ptrn.shape[0]
        arr = np.zeros((ycor.max() + 1, xcor.max() + 1), dtype=np.uint8)
        arr[ycor[:], xcor[:]] = ptrn[0 : len(ptrn): step]
        #img[:,113]=1 #the line is at 113
        arr = arr * 255
        img = Image.fromarray(arr)
        img.save(filename + '.png')
        return img


    def readbin(self, name='test.bin'):
        '''
        reads a binary file

        :param name
        '''
        currentdir = os.path.dirname(os.path.realpath(__file__))
        pat=np.fromfile(os.path.join(currentdir, name), dtype=np.uint8)
        return pat


    def writebin(self, pixeldata, filename='test.bin'):
        '''
        writes pixeldata to a binary file

        :param pixeldata must have uneven length
        :param filename name of file
        '''
        currentdir = os.path.dirname(os.path.realpath(__file__))
        pixeldata=pixeldata.astype(np.uint8)
        pixeldata.tofile(os.path.join(currentdir, filename))


#TODO: the coordinates had a different type in the original --> np.int32
# a line resutts from / or // in return

if __name__ == "__main__":
    interpolator = Interpolator()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    url = os.path.join(dir_path, 'test-patterns', 'line-resolution-test.ps')
    ptrn = interpolator.patternfile(url)
    interpolator.writebin(ptrn, "test.bin")
    pat = interpolator.readbin("test.bin")
    print("The shape of the pattern is {}".format(pat.shape))
    # testing the slices can only be done at 64 bit, VTK is however installed for 32 bit
    interpolator.plotptrn(pat, 1)
