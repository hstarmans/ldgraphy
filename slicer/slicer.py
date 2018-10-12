'''
@company: Hexastorm
@author: Rik Starmans
'''

import math
import numpy as np
import os
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
        self.laserfrequency = 2.6E6       # the laser frequency [Hz]
        self.rotationfrequency = 1000     # rotation frequency [Hz]
        self.facets = 4                   # number of facets
        self.inradius = 15                # inradius polygon [mm]
        self.n = 1.49                     # refractive index
        self.pltfxsize = 200              # platform size scanning direction [mm]
        self.pltfysize = 200              # platform size stacking direction [mm]
        self.samplegridsize = 0.05        # height/width of the sample gridth [mm]
        self.stagespeed = 100             # mm/s
        # STORAGE LOCATIONS
        # Two locations are distinguished; 1. Storage location of patternfiles
        #                                  2. Storage location of uploadfiles
        # The scripts was envisoned to be controlled via a webserver, e.g. Flask
        currentdir = os.path.dirname(os.path.realpath(__file__))
        self.uploadfolder = os.path.join(currentdir, 'static','upload')
        self.patfolder = os.path.join(currentdir,'static','patternfiles')
        # DERIVED CONSTANTS
        self.TSTEP = 1/self.laserfrequency
        self.FACETANGLE = np.radians((180-360/self.n)) # facet angle in radians [rad]


    def pstoarray(self, url):
        '''converts postscript file to an array

        :param url: path to postcript file
        '''
        psppoint = 0.3527777778 # 1 post script in mm
        tmp = Image.open(url)
        x_size, y_size = [i*psppoint for i in tmp.size]
        if x_size > self.pltfxsize or y_size > self.pltfysize:
            raise Exception('Object does not fit on platform')
        scale = psppoint/self.samplegridsize
        tmp.load(scale = scale)
        tmp_array = np.array(tmp.convert('1'))
        if tmp_array.max() == 0:
            raise Exception("Slice is empty")
        return tmp_array

    def displacement(self, pixel):
        '''
        returns the displacement for a given pixel

        :param pixel; the pixelnumber
        '''
        angle = (self.rotationfrequency*4*np.pi*self.TSTEP*pixel)%self.FACETANGLE-self.FACETANGLE/2
        # NOTE:
        # In an earlier version, the angles which were not projected were skipped in the
        # interpolation. It could be beneficial to kill of angles outside say -30 and +30 degrees.
        # This does make the code more cumbersome and reduces some clarity.
        # One most also take care that this function is turned of in the plot function
        disp = (self.inradius*2*np.sin(angle)*(1-np.power((1-np.power(np.sin(angle),2))/
                                            (np.power(self.n,2)-np.power(np.sin(angle),2)),0.5)))
        return disp


    def fxpos(self, pixel, xstart):
        '''
        returns the laserdiode x-position in pixels type int
        :param i: the pixelnumber
        :param xstart: the x-start position [mm]
        '''
        xpos = np.sin(self.tiltangle)*self.displacement(pixel)+xstart
        #NOTE: float leadis to additional patterns in final slice
        return xpos//self.samplegridsize


    def fypos(self, pixel, ystart):
        '''
        returns the laserdiode y-position in pixels type int
        :param pixel: the pixelnumber
        :param ystart: the y-start position in [mm]
        '''
        ypos = np.cos(self.tiltangle)*self.displacement(pixel)+self.TSTEP*pixel*self.stagespeed+ystart
        #NOTE: float leads to additional patterns in the final slice
        return ypos//self.samplegridsize


    def createcoordinates(self, xstart, ystart):
        '''
        returns the x.y position of the laserdiode for each pixel
        :param xstart: the x-start position in [mm]
        :param ystart: the y-start position in [mm]
        '''
        self.nofpixels = round(self.pltfysize/self.stagespeed*self.laserfrequency)
        #TODO: correct for the fact that you don't use all pixels!
        #NOTE: round should be replaced with upper limit
        vfxpos = np.vectorize(self.fxpos)
        vfypos = np.vectorize(self.fypos)
        xpos = vfxpos(range(0,self.nofpixels), xstart)
        ypos = vfypos(range(0,self.nofpixels), ystart)
        # concatenate; result [[x0,x1],[y0,y1]]
        ids = np.concatenate(([xpos],[ypos]))
        return ids


    def patternfile(self, url, xstart, ystart):
        '''returns the pattern file as numpy array, shape (pixels,)

        The postscript file is interpolated, for the x-start and y-start position.
        :param url: path to postscript file
        :param xstart: the x-start position in mm
        :param ystart: the y-start position in mm
        '''
        from time import time
        ctime = time()

        
        layerarr = self.pstoarray(url)
        print(layerarr.shape)
        print("Retrieved layerarr")
        print("elapsed {}".format(time()-ctime))
        ids = self.createcoordinates(xstart, ystart)
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
    ptrn = slic3r.patternfile(url,0,0)
    # diodes which are on
    # lst=[i for i in range(ptrn0.shape[0]) if ptrn0[i,:].sum()>0]
    # [i for i in range(ptrn1.shape[0]) if ptrn1[i,:].sum()>0]
    # [x[0] for x in enumerate(lst) if x[1]==2]
    slic3r.writebin(ptrn,"test.bin")
    pat = slic3r.readbin("test.bin")
    # testing the slices can only be done at 64 bit, VTK is however installed for 32 bit
    #slic3r.plotptrn(pat, 0, 0, 1)
