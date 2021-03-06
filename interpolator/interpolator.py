'''
#NOTE: DOES NOT RUN ON BEAGLEBONE; blows memory
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
    This object calculates the binary laser diode information for the Hexastorm.

    A post script file is converted to a numpy array. 
    The positions of the laserdiode are calculated via the function createcoordinates. The function patternfiles interpolates
    the array created. These values are either 0 (laser off) or 1 (laser on). The slicer object has convenience functions 
    to write and read the binary files which can be pushed to the PRU.
    '''

    def __init__(self):
        # PARAMETERS
        self.tiltangle = np.radians(90)          # angle [radians], for a definition see figure 7
                                                 # https://reprap.org/wiki/Transparent_Polygon_Scanning
        self.laserfrequency = 2e6                # the laser frequency [Hz] 
        self.rotationfrequency = 2400/60         # rotation frequency polygon [Hz]
        self.facets = 4                          # number of facets
        self.inradius = 15                       # inradius polygon [mm]
        self.n = 1.49                            # refractive index
        self.pltfxsize = 200                     # platform size scanning direction [mm]
        self.pltfysize = 200                     # platform size stacking direction [mm]
        self.samplexsize = 0                     # sample size scanning direction [mm]
        self.sampleysize = 0                     # sample size stacking direction [mm]
        # NOTE: sample below Nyquist criterion
        #       you first sample the image, you then again sample the sampled image 
        self.samplegridsize = 0.015              # height/width of the sample gridth [mm]
        self.stagespeed = 2.0997375328           # mm/s
        self.startpixel = 3467                   # pixel determine via camera 
        self.pixelsinline = 790*8                # number of pixels in a line [new 785]
        self.downsample_factor = 5               # each pixel is repeated five times, to speed up interpolation
        self.downsample(factor = self.downsample_factor)       
        currentdir = os.path.dirname(os.path.realpath(__file__))
        self.debug_folder = os.path.join(currentdir, 'debug')


    def downsample(self, factor = 5):
        ''' downsamples constants
        '''
        self.laserfrequency = round(self.laserfrequency/factor)
        self.startpixel = round(self.startpixel/factor)
        self.pixelsinline = round(self.pixelsinline/factor)
        if self.pixelsinline%8:
            raise Exception('Remainder not zero {}'.format(self.pixelsinline%8))

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

        The y-axis is orthogonal to the scanline if the stage does not move,
        and parallel to the stage movement.
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
        print("The lanewidth is {}".format(lanewidth))
        print("The facets in lane are {}".format(facets_inlane))
        # single facet
        vfxpos = np.vectorize(self.fxpos, otypes=[np.int16])
        vfypos = np.vectorize(self.fypos, otypes=[np.int16])
        xstart = abs(self.fxpos(self.pixelsinline-1)*self.samplegridsize)
        xpos_facet = vfxpos(range(0, self.pixelsinline), xstart)
        # TODO: you still don't account for ystart (you are moving in the y, so if you start at the edge you miss something)
        ypos_forwardfacet = vfypos(range(0, self.pixelsinline), True)
        ypos_backwardfacet = vfypos(range(0, self.pixelsinline), False)
        # single lane
        xpos_lane = np.tile(xpos_facet, facets_inlane)
        ypos_forwardlane = np.array([],dtype=np.int16)
        ypos_backwardlane = np.array([],dtype=np.int16)
        #TODO: this part is slow and looks suboptimal
        for facet in range(0, facets_inlane):
            ypos_forwardtemp = ypos_forwardfacet + round(
                (facet*self.stagespeed)/(self.facets*self.rotationfrequency*self.samplegridsize))
            ypos_backwardtemp = ypos_backwardfacet + round(
            ((facets_inlane-facet)*self.stagespeed)/(self.facets*self.rotationfrequency*self.samplegridsize))
            ypos_forwardlane = np.concatenate((ypos_forwardlane, ypos_forwardtemp))
            ypos_backwardlane = np.concatenate((ypos_backwardlane, ypos_backwardtemp))
        # per lane; 5000 (pixels per facet) / 5 (samplefactor) 
        #    * (200 mm/0.015 mm (resolution)*2 (16 bit = 2byte)) )/1E6 = 40 MB
        # TODO: slice per lane so it fits on beaglebone, you have on the fly slicing 
        # all lanes
        xpos = np.array([], dtype=np.int16)
        ypos = np.array([], dtype=np.int16)
        for lane in range(0, lanes):
            #TODO: why is this force needed?
            xoffset= int(round(lane * (self.fxpos(0)-self.fxpos(self.pixelsinline-1))))
            xpos_temp = xpos_lane + xoffset
            if lane % 2 == 1:
                ypos_temp = ypos_backwardlane
            else:
                ypos_temp = ypos_forwardlane
            xpos = np.concatenate((xpos, xpos_temp)) 
            ypos = np.concatenate((ypos, ypos_temp))
        # interpolation can be linear, however int are used to save space
        ids = np.concatenate(([xpos], [ypos]))
        return ids


    def patternfile(self, url, test=False):
        '''returns the pattern file as numpy array

        mostly a convenience function which wraps other functions in this class
        :param url: path to postscript file
        :param test: runs a sampling test, whether laser frequency sufficient to provide accurate sample
        '''
        from time import time
        ctime = time()
        layerarr = self.pstoarray(url).astype(np.uint8)
        if test:
            img = Image.fromarray(layerarr.astype(np.uint8)*255)
            img.save(os.path.join(self.debug_folder, 'nyquistcheck.png'))
        if test: 
            layerarr = np.ones_like(layerarr)
        print("Retrieved layerarr")
        print("elapsed {}".format(time()-ctime))
        ids = self.createcoordinates()
        print("Retrieved coordinates")
        print("elapsed {}".format(time()-ctime))
        if test:
            ptrn = ndimage.map_coordinates(input=layerarr, output=np.uint8, 
            coordinates=ids, order=1, mode="constant", cval=1)
        else:
            ptrn = ndimage.map_coordinates(input=layerarr, output=np.uint8, 
            coordinates=ids, order=1, mode="constant", cval=0)
        print("Completed interpolation")
        print("elapsed {}".format(time()-ctime))
        if ptrn.min()<0 or ptrn.max()>1:
            raise Exception('This is not a bit list.')
        ptrn = np.logical_not(ptrn)
        ptrn = np.repeat(ptrn, self.downsample_factor)
        ptrn = np.packbits(ptrn)
        return ptrn


    def plotptrn(self, ptrn, step, filename = 'plot'):
        '''
        function can be used to plot a pattern file. Result is returned as numpy array
        and stored in script folder under filename.

        :param ptrnfile: result of the functions patternfiles
        :param step: pixel step, can be used to lower the number of pixels that are plotted 
        :param filename: filename to store pattern
        '''
        #TODO: - plot with real laser spots --> convolution?
        #      - your y-step is greater than sample size so you see lines, this will not be there in
        #        reality as you spot is larger
        ids = self.createcoordinates()
        ids = np.repeat(ids, self.downsample_factor, axis = 1)
        # repeat adden
        xcor = ids[0, ::step]
        ycor = ids[1, ::step]
        if xcor.min()< 0:
            print('XCOR negative, weird!')
            xcor += abs(xcor.min())
        if ycor.min()< 0:
            print('YCOR negative, weird!')
            ycor += abs(ycor.min())
        arr = np.zeros((xcor.max() + 1, ycor.max() + 1), dtype=np.uint8)
        ptrn = np.unpackbits(ptrn)
        arr[xcor[:], ycor[:]] = ptrn[0 : len(ptrn): step]
        arr = arr * 255
        img = Image.fromarray(arr)
        img.save(os.path.join(self.debug_folder, filename + '.png'))
        return img


    def readbin(self, name='test.bin'):
        '''
        reads a binary file

        :param name
        '''
        pat=np.fromfile(os.path.join(self.debug_folder, name), dtype=np.uint8)
        return pat


    def writebin(self, pixeldata, filename='test.bin'):
        '''
        writes pixeldata to a binary file

        :param pixeldata must have uneven length
        :param filename name of file
        '''
        pixeldata=pixeldata.astype(np.uint8)
        if not os.path.exists(self.debug_folder):
            os.makedirs(self.debug_folder)
        pixeldata.tofile(os.path.join(self.debug_folder, filename))




if __name__ == "__main__":    
    interpolator = Interpolator()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    url = os.path.join(dir_path, 'test-patterns', 'line-resolution-test.ps')
    ptrn = interpolator.patternfile(url)
    interpolator.writebin(ptrn, "test.bin")
    pat = interpolator.readbin("test.bin")
    print("The shape of the pattern is {}".format(pat.shape))
    interpolator.plotptrn(ptrn = pat, step = 1)
