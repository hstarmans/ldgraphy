'''
@company: Hexastorm
@author: Rik Starmans
'''

import math
import os

import numpy as np
from scipy import ndimage
from PIL import Image


class slicer(object):
    '''
    This object creates the slices for the Hexastorm.

    A post script file is converted to an numpy array. 
    The positions of the laserdiode are calculated via the function createcoordinates. The function patternfiles interpolates
    the array created. These values are either 0 (laser off) or 1 (laser on). The slicer object has functions to write binary files
    which can be pushed to the PRU. The slicer can also read binary files and render them and
    saves it as image.
    '''

    def __init__(self):
        # PARAMETERS
        self.tiltangle = np.radians(90)   # angle [radians]
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
        # pixelsfacet is a known
        # STORAGE LOCATIONS
        # Two locations are distinguished; 1. Storage location of patternfiles
        #                                  2. Storage location of uploadfiles
        # The scripts was envisoned to be controlled via a webserver, e.g. Flask
        currentdir = os.path.dirname(os.path.realpath(__file__))
        self.uploadfolder = os.path.join(currentdir, 'static','upload')
        self.patfolder = os.path.join(currentdir,'static','patternfiles')
        


    def pstoarray(self, url):
        '''converts postscript file to an array

        :param url: path to postcript file
        '''
        psppoint = 0.3527777778 # 1 post script in mm
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

        assumes the line starts at the positive plane
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
        returns the laserdiode x-position in pixels type int
        :param pixel: the pixelnumber in the line
        :param xstart: the x-start position [mm], typically your xstart is larger than 0
                       as the displacement can be negative
        '''
        line_pixel = self.startpixel + pixel % self.pixelsinline
        xpos = np.sin(self.tiltangle)*self.displacement(line_pixel) + xstart
        #NOTE: float leads to additional patterns in final slice
        return xpos//self.samplegridsize


    def fypos(self, pixel, direction, ystart = 0):
        '''
        returns the laserdiode y-position in pixels type int
        :param pixel: the pixelnumber in the line
        :param direction: True is +, False is -
        :param ystart: the y-start position in [mm]
        '''
        line_pixel = self.startpixel + pixel % self.pixelsinline
        if direction:
            ypos = np.cos(self.tiltangle)*self.displacement(line_pixel)
            ypos += line_pixel/self.laserfrequency*self.stagespeed + ystart
        else:
            ypos = np.cos(self.tiltangle)*self.displacement(line_pixel) 
            ypos -= line_pixel/self.laserfrequency*self.stagespeed + ystart
        #NOTE: float leads to additional patterns in the final slice
        return ypos//self.samplegridsize


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
        lanes = math.ceil(self.samplexsize/(lanewidth))
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
            ypos_forwardtemp = ypos_forwardfacet + facet/(self.facets*self.rotationfrequency)*self.stagespeed
            ypos_backwardtemp = ypos_backwardfacet + (facets_inlane - facet)/(self.facets*self.rotationfrequency)*self.stagespeed
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
        print(layerarr.shape)
        print("Retrieved layerarr")
        print("elapsed {}".format(time()-ctime))
        ids = self.createcoordinates()
        print(ids.shape)
        print("Retrieved coordinates")
        print("elapsed {}".format(time()-ctime))
        #TODO: test
        # values outside image are mapped to 0
        ptrn = ndimage.map_coordinates(input=layerarr, output=np.uint8, coordinates=ids, order=1, mode="constant",cval=0)
        # max array is set to one
        print("Completed interpolation")
        print("elapsed {}".format(time()-ctime))
        return ptrn

    def plotptrn(self, ptrn, xstart, ystart, step):
        '''
        function can be used to plot a pattern file. The result is return as numpy array
        and stored in the patfolder under the name "plot.png"

        :param ptrnfile: result of the functions patternfiles
        :param step: pixel step, can be used to lower the number of pixels that are plotted 
        '''
        # the positions are constructed
        vfxpos = np.vectorize(self.fxpos) #TODO: fxpos should be vectorized, now done twice
        vfypos = np.vectorize(self.fypos)
        xcor = vfxpos(range(0,ptrn.shape[0], step), xstart)
        ycor = vfypos(range(0,ptrn.shape[0], step), ystart)
        # here the output of the array is defined
        # if this is not done, operation becomes too slow
        xcor = xcor.astype(np.int32, copy=False)
        ycor = ycor.astype(np.int32, copy=False)
        #ycor=ycor+abs(ycor.min())
        # x and y cannot be negative
        if xcor.min()<0:
            xcor+=abs(xcor.min())
        if ycor.min()<0:
            ycor+=abs(ycor.min())
        # number of pixels ptrn.shape[0]
        img = np.zeros((ycor.max()+1, xcor.max()+1),dtype=np.uint8)
        img[ycor[:], xcor[:]]=ptrn[0:len(ptrn):step]
        #img[:,113]=1 #the line is at 113
        img = img*255
        cv2.imwrite(os.path.join(self.patfolder,"plot.png"),img)
        return img

    def readbin(self, name):
        '''
        reads a binary file, which can be
        written to the SDRAM

        :param name
        '''
        pat=np.fromfile(os.path.join(self.patfolder,name), dtype=np.uint8)
        return pat

    def writebin(self, pixeldata, filename):
        '''
        writes pixeldata to a binary file, which can
        be opened with IntelHex and pushed to the SDRAM

        :param pixeldata must have uneven length
        :param filename name of file
        '''
        pixeldata=pixeldata.astype(np.uint8)
        pixeldata.tofile(os.path.join(self.patfolder, filename))

#TODO: the coordinates had a different type in the original --> np.int32
# a line resutts from / or // in return

if __name__ == "__main__":
    slic3r=slicer()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    url = os.path.join(dir_path, 'test-patterns', 'line-resolution-test.ps')
    #NOTE: pstoarray, createcoordinates is handled by the function patternfile
    ptrn = slic3r.patternfile(url)
    # diodes which are on
    # lst=[i for i in range(ptrn0.shape[0]) if ptrn0[i,:].sum()>0]
    # [i for i in range(ptrn1.shape[0]) if ptrn1[i,:].sum()>0]
    # [x[0] for x in enumerate(lst) if x[1]==2]
    slic3r.writebin(ptrn,"test.bin")
    pat = slic3r.readbin("test.bin")
    # testing the slices can only be done at 64 bit, VTK is however installed for 32 bit
    #slic3r.plotptrn(pat, 0, 0, 1)
