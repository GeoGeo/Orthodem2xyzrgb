'''
Created on 24 Feb 2015
Given to identically projected rasters... an orthomosaic and a dsm/dem,
generate an x,y,z,r,g,b file at a specified resolution
@author: steven
'''
from osgeo import ogr
from osgeo import osr
import gdal
from gdalconst import *
import time
import argparse

class RasterReader(object):
    
    '''
    Handles reading of rasters 
    '''
    
    def __init__(self, filename, bandnum, tilesize):
        self.filename = filename
        self.bandnum = bandnum
        self.tilesize = tilesize
        self._load()
        
    def _load(self):
        self.ds = gdal.Open(self.filename, GA_ReadOnly)
        if self.ds is None:
            print 
            raise Exception('Could not open ' + self.filename)
        else:
            self.band = self.ds.GetRasterBand(self.bandnum)
            self.cols = self.ds.RasterXSize               
            self.rows = self.ds.RasterYSize
            self.trans = self.ds.GetGeoTransform()
            self.topleftx = self.trans[0] # top left
            self.xtiles = 1+(self.cols/self.tilesize)
            self.ytiles = 1+(self.rows/self.tilesize)
            self.affine = self.ds.GetGeoTransform()
            self.xpixelsize = self.affine[1]
            self.ypixelsize = self.affine[5]
    
    def getmaxsamples(self):
        '''
        find max size of grid, to help with progress 
        ''' 
        return self.xtiles * self.ytiles
        
    def gettile(self, tilecol, tilerow):
        xoff = tilecol * self.tilesize
        yoff = tilerow * self.tilesize 
        maxx = min(xoff+self.tilesize, self.cols)
        maxy = min(yoff+self.tilesize, self.rows)
        wid = maxx-xoff
        hite = maxy - yoff
        return self.band.ReadAsArray(xoff, yoff, 1,1)
    
    def getrealcoord(self, tilecol, tilerow, col, row):
        '''
        convert x,y pixel coord to geographic coord
        assumes 0 degrees rotation (the case with our rasters)
        If we need to handle rotated rasters in future, we'll need a more complicated affine transformation
            poDS->dGeoTransform[0] = originX + cellSizeX/2.0;
            poDS->dGeoTransform[1] = cos(rotation) * cellSizeX;
            poDS->dGeoTransform[2] = -sin(rotation) * cellSizeX;
            poDS->dGeoTransform[3] = originY - cellSizeY/2.0;
            poDS->dGeoTransform[4] = sin(rotation) * cellSizeY;
            poDS->dGeoTransform[5] = cos(rotation) * cellSizeY;
        '''
        realx = (self.tilesize*tilecol)+col
        realy = (self.tilesize*tilerow)+row
        x = self.affine[0]+(self.affine[1]*realx)
        y = self.affine[3]+(self.affine[5]*realy)
        return ((x,y))
        
    def close(self):
        del self.ds


class RastersToXYZRGB(object):
    
    '''
    Given 
    - a sampling resolution (e.g. 64 = sample point at top left corner of each 64x64 pixel block)
    - filename of ortho mosaic tiff
    - filename of DSM tif 
    - optional nodata (list of integers representing missing data)
    provides a generator which yields a series of (x,y,z,r,g,b) values
    
    assumptios:-
    - identical CRS and extents for both images
    - images don't have rotation applied
    - rgb are in bands 1,2 and 3 respectively
    - DSM is in band 1 
    '''
    
    def __init__(self, filenameOrtho, filenameDSM, resolution, writenodata = False, nodata = [0], outputnodata = -100):
        self.resolution = resolution
        self.filenameOrtho = filenameOrtho
        self.filenameDSM = filenameDSM
        self.nodata = nodata
        self.dropped = 0
        self.red = RasterReader(filenameOrtho, 1, resolution)
        self.green = RasterReader(filenameOrtho, 2, resolution)
        self.blue = RasterReader(filenameOrtho, 3, resolution)
        self.dsm = RasterReader(filenameDSM, 1, resolution)
        self.outputnodata = outputnodata
        self.writenodata = writenodata
        print "Successfully read!"
        
    def getPoints(self):
        '''
        iterate over this to get all the points as an (x,y,z,r,g,b) tuple
        assumptions:
        - no raster rotation
        - using same CRS and extents for both images
        '''
        cnt = 0

        for col in range(0,self.red.xtiles):
            for row in range(0,self.red.ytiles):
                r = self.red.gettile(col, row)
                g = self.green.gettile(col, row)
                b = self.blue.gettile(col, row)
                x,y = self.red.getrealcoord(col, row, 0, 0)
                z = self.dsm.gettile(col,row)
                if not int(z) in self.nodata:
                    yield (x,y,z,r,g,b) 
                    cnt += 1          
                    
    def getPointsAndProgress(self):
        '''
        iterate over this to get all the points as a tuple
        (percentcomplete, (x,y,z,r,g,b))
        '''
        cnt = 0
        self.dropped = 0
        numpts = float(self.red.getmaxsamples())
        for col in range(0,self.red.xtiles-1):
            for row in range(0,self.red.ytiles-1):
                try:
                    r = self.red.gettile(col, row)
                    g = self.green.gettile(col, row)
                    b = self.blue.gettile(col, row)
                    x,y = self.red.getrealcoord(col, row, 0, 0)   
                    z = self.dsm.gettile(col,row)
                    progress = int((float(cnt)/numpts)*100.0)
                    if not self.writenodata:
                        # default, only write pixels w/ data
                        if not int(z) in self.nodata:
                            yield (progress,(x,y,z,r,g,b)) 
                            cnt += 1
                        else:
                            cnt += 1
                            self.dropped += 1
                            yield (progress,())
                    else:
                        if int(z) in self.nodata:
                            yield (progress,(x,y,self.outputnodata,r,g,b)) 
                            cnt += 1
                        else:
                            yield (progress,(x,y,z,r,g,b)) 
                            cnt += 1
                except:
                    # read outside of raster
                    pass


