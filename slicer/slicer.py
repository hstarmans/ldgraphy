'''
@company: Hexastorm
@author: Rik Starmans
'''

import vtk
from vtk.util.numpy_support import vtk_to_numpy # install from conda-forge see github, search vtk=7.1.0=py35_2 
import math
import numpy as np
import os
from scipy import ndimage
import cv2 # conda install -c menpo opencv3
# to profile memory
# from memory_profiler import profile
# import above decorator and decorate functions with @profile

class slicer(object):
    '''
    This object creates the slices for the Hexastorm.

    VTK cuts the CAD file into a slice at a given height whereafter it is converted to an array by Numpy. The
    interior of a contour is set to 255, the exterior to 0.
    The positions of the laserdiode are calculated via the function createcoordinates. The function patternfiles interpolates
    the array created by VTK. If the laser frequency is on for two seconds with a frequency of
    100.000; there are a 200.000 xy positions and the patternfile is a list of 200.000 values.
    These values are either 0 (laser off) or 1 (laser on). The slicer object has functions to write binary files
    which can be pushed to the SDRAM. The slicer can also read binary files and render them and
    saves it as image.
    '''

    def __init__(self):
        # PARAMETERS
        self.tiltangle = np.radians(90)   # angle [radians]
        self.laserfrequency = 100000      # the laser frequency [Hz]
        self.rotationfrequency = 1000     # rotation frequency [Hz]
        self.facets = 6                   # number of facets
        self.inradius = 17.3              # inradius polygon [mm]
        self.n = 1.49                     # refractive index
        self.pltfxsize = 200              # platform size scanning direction [mm]
        self.pltfysize = 200              # platform size stacking direction [mm]
        self.layerheight = 0.1            # slice thickness [mm]
        self.samplegridsize = 0.05        # height/width of the sample gridth [mm]
        self.stagespeed = 100             # mm/s
        # STORAGE LOCATIONS
        # Two locations are distinguished; 1. Storage location of patternfiles
        #                                  2. Storage location of uploadfiles
        # The scripts was envisoned to be controlled via a webserver, e.g. Flask
        currentdir = os.path.dirname(os.path.realpath(__file__))
        self.uploadfolder = os.path.join(currentdir, 'static','upload')
        self.patfolder = os.path.join(currentdir,'static','patternfiles')
        #VTK
        self.reader = None             # STL reader, set via filename
        self.mapper = None             # polydata, set via filename
        #DERIVED CONSTANTS
        self.TSTEP = 1/self.laserfrequency
        self.FACETANGLE = np.radians((180-360/self.n)) # facet angle in radians [rad]

    @property
    def filename(self):
        return self._filename

    @filename.setter
    def filename(self, name='oshw.stl'):
        self._filename=name
        self.reader = vtk.vtkSTLReader()
        self.reader.SetFileName(os.path.join(self.uploadfolder ,self.filename))
        self.mapper = vtk.vtkPolyDataMapper()
        self.mapper.SetInputConnection(self.reader.GetOutputPort())

    def getlayers(self):
        '''
        return number of layers in the object
        '''

        bounds = self.mapper.GetBounds()
        layers = math.floor((bounds[5]-bounds[4])/self.layerheight)
        return layers

    def stltoarray(self, zheight):
        '''slices STL to an array

        The height is the position where the layer is retrieved.
        :param zheigh: z height where to take a cut in mm
        '''
        # generate contour by cutting the STL through its center axis aligned with
        # a plane
        # NOTE: an alternative might be to use the VTK imagemapper class
        contourCutter = vtk.vtkCutter()
        contourCutter.SetInputConnection(self.reader.GetOutputPort())
        cutPlane = vtk.vtkPlane()
        cntr=list(self.mapper.GetCenter())
        cutPlane.SetOrigin(cntr[0],cntr[1],zheight)
        cutPlane.SetNormal(0, 0, 1)
        contourCutter.SetCutFunction(cutPlane)
        stripper = vtk.vtkStripper()
        stripper.SetInputConnection(contourCutter.GetOutputPort())
        stripper.Update()  #updates are crucial
        # that's our contour
        contour = stripper.GetOutput()
        # prepare the binary image's voxel grid
        bounds = [0]*6
        contour.GetBounds(bounds)
        # spacing is [width, height, length]  #TODO: does the length effect the sampling?
        spacing = [self.samplegridsize, self.samplegridsize, self.layerheight]
        # compute dimensions
        dim = [0]*3
        for i in range(3):
            dim[i] = int(round(math.ceil((bounds[i * 2 + 1] - bounds[i * 2]) / spacing[i]))) + 1
            if (dim[i] < 1):
                dim[i] = 1
        inval = 255
        outval = 0
        blank=np.ones((dim[0]-1)*(dim[1]-1),dtype=np.uint8)*inval # create an array of 255
        blank_string = blank.tostring()
        dataImporter = vtk.vtkImageImport()
        dataImporter.CopyImportVoidPointer(blank_string,len(blank_string))
        dataImporter.SetDataScalarTypeToUnsignedChar()
        dataImporter.SetNumberOfScalarComponents(1)
        dataImporter.SetWholeExtent(0, dim[0]-1, 0, dim[1]-1, 0, dim[2] - 1)
        dataImporter.SetDataExtent(0, dim[0]-1, 0, dim[1]-1, 0, dim[2] - 1)
        origin = [0]*3
        origin[0] = bounds[0]
        origin[1] = bounds[2]
        origin[2] = bounds[4]

        # polygonal data - image stencil:
        pol2stenc = vtk.vtkPolyDataToImageStencil()
        pol2stenc.SetInputConnection(stripper.GetOutputPort())
        pol2stenc.DebugOn()
        pol2stenc.SetOutputOrigin(origin)
        pol2stenc.SetOutputSpacing(spacing)
        pol2stenc.SetOutputWholeExtent(dataImporter.GetDataExtent())

        # cut the corresponding white image and set the background:
        imgstenc = vtk.vtkImageStencil()
        imgstenc.SetInputConnection(dataImporter.GetOutputPort())
        imgstenc.SetStencilConnection(pol2stenc.GetOutputPort())
        imgstenc.ReverseStencilOff()
        imgstenc.SetBackgroundValue(outval)

        imgstenc.Update()
        # convert the stencil to a numpy array
        vtk_image = imgstenc.GetOutput()
        width, height, _ = vtk_image.GetDimensions()
        vtk_array = vtk_image.GetPointData().GetScalars()
        components = vtk_array.GetNumberOfComponents()
        arr = vtk_to_numpy(vtk_array).reshape(height, width, components)
        # only grab values layer 0
        arr=arr[:,:,0].astype(np.uint8, copy=False)
        # slices are extended, the object is kept at the center
        # extension is done via padding with zeroes
        padheight = round(self.pltfysize/self.samplegridsize-height)
        padwidth = round(self.pltfxsize/self.samplegridsize-width)
        arr = np.lib.pad(arr, ((round(padheight/2), math.floor(padheight/2)), (round(padwidth/2), math.floor(padwidth/2))), mode='constant', constant_values=0)
        arr = np.flipud(arr)
        return arr

    def createpreview(self, arr, filename=None):
        resized_image = cv2.resize(arr, (400, 400))
        if filename == None:
            filename = os.path.join(self.patfolder,'preview.png')
        cv2.imwrite(filename,resized_image)

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
        #NOTE: round should be replaced with upper limit
        vfxpos = np.vectorize(self.fxpos)
        vfypos = np.vectorize(self.fypos)
        xpos = vfxpos(range(0,self.nofpixels), xstart)
        ypos = vfypos(range(0,self.nofpixels), ystart)
        # concatenate; result [[x0,x1],[y0,y1]]
        ids = np.concatenate(([xpos],[ypos]))
        return ids

    def patternfile(self, zheight, xstart, ystart):
        '''returns the pattern file as numpy array, shape (pixels,)

        The CAD file is sliced at height, zheight. For the x-start and y-start position.
        :param zheight: the height in mm, typically height should be larger than 0.
        :param xstart: the x-start position in mm
        :param ystart: the y-start position in mm
        '''
        layerarr = self.stltoarray(zheight)
        if layerarr.max() == 0:
            raise Exception("Slice is empty")
        ids = self.createcoordinates(xstart, ystart)
        #TODO: test
        # values outside image are mapped to 0
        ptrn = ndimage.map_coordinates(input=layerarr, output=np.uint8, coordinates=ids, order=1, mode="constant",cval=0)
        # max array is set to one
        ptrn = ptrn//255
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
    slic3r.layerheight=0.1
    slic3r.filename='oshw.stl'
    print("There are "+str(slic3r.getlayers())+" layers.")
    arr = slic3r.stltoarray(0.1)
    slic3r.createpreview(arr)
    ids = slic3r.createcoordinates(0,0)
    #NOTE: stltoarray, createcoordinates is handled by the function patternfile
    ptrn = slic3r.patternfile(0.1,100,0)
    # diodes which are on
    # lst=[i for i in range(ptrn0.shape[0]) if ptrn0[i,:].sum()>0]
    # [i for i in range(ptrn1.shape[0]) if ptrn1[i,:].sum()>0]
    # [x[0] for x in enumerate(lst) if x[1]==2]
    slic3r.writebin(ptrn,"test.bin")
    pat = slic3r.readbin("test.bin")
    # testing the slices can only be done at 64 bit, VTK is however installed for 32 bit
    slic3r.plotptrn(pat, 0, 0, 1)
