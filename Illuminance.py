#-----------------------------------------------------------------------------#
#illuminance.py
#
#NPS Night Skies Program
#
#Last updated: 2019/01/29
#
#This script calculates the horizontal and vertical illuminance from the image 
#containing all light sources.  
#	(1) 
#	(2) 
#	(3) 
#   (4) 
#
#Note: 
#
#
#Input: 
#   (1) 
#   (2) 
#   (3) 
#
#Output:
#   (1) A txt file (illuminance_results.txt) listing the azimuth angle, vertical illuminance (mlx), and 
#       horizontal illuminance (mlx)
#   (2) 
#
#History:
#	Katie Karnes -- Created
#
#-----------------------------------------------------------------------------#

#from astropy.io import fits
#from datetime import datetime as Dtime
#from glob import glob, iglob
#from scipy.misc import imsave 
#from win32com.client import Dispatch
import archook
archook.get_arcpy()
import arcpy

#import pdb
#import matplotlib.pyplot as plt
import numpy as n
#import os
#import shutil

# Local Source
import filepath
#reload(filepath)

#-----------------------------------------------------------------------------#

#unit conversions

def nl_to_mag(x):
    """
    Converting brightness from nL to magnitude according to Dan's script
    Note: this is inconsistent to mag_to_nL_dan()
    """
    m = 26.3308 - 2.5 * n.log10(x)
    return m
    
def mag_to_nl_dan(m):
    """
    Converting brightness from magnitude to nL according to Dan's script
    Note: this is inconsistent to nL_to_mag()
    """
    x = 34.08*n.exp(20.7233 - 0.92104 * m)
    return x
    
def mag_to_nl_liwei(m):
    """
    Converting brightness from magnitude to nL according to nl_to_mag
    """
    x = 10**((26.3308-m)/2.5)
    return x

def nl_to_ucd_per_m2(nl):
    """
    Converting brightness from nL to ucd/m^2
    """
    ucd_m2 = (10/n.pi)*nl
    return ucd_m2

def get_panoramic_raster(dnight, set, band, raster, k=25):
    """    
    This function reads in a raster file and converts it into a Python array. 
    Only area above the horizon is preserved to enforce consistency. This 
    function does not work on full resolution mosaics due to limited memory space.

    Arguments:
    dnight -- data night; i.e. 'FCNA160803'
    set -- data set; i.e. 1 
    band -- filter; either 'V' or 'B'
    raster -- input raster; either 'gal', 'zod', or 'median' but not 'fullres'
    k -- downscale factor for making the image smaller

    Returns:
    A -- a 2D Python array of shape [1800,7200]/k   
    """
    filter = {'V':"",'B':"/B"}
    path = {'gal':"/gal/galtopmags",
            'zod':"/zod/zodtopmags",
            'median':filter[band]+"/median/skybrightmags"}
            
    # file = filepath.griddata+dnight+"/S_0"+str(set)+path[raster]
    file = filepath.griddata
    arcpy_raster = arcpy.sa.Raster(file)  
    A = arcpy.RasterToNumPyArray(arcpy_raster, "#", "#", "#", -9999)[:1800,:7200]
	# from skimage.transform import downscale_local_mean
	# A_small = downscale_local_mean(A,(k,k))
    return A


# Get numpy array with median mosaic sky brightness values in nL, then convert units
medianMosaicArr = get_panoramic_raster('FCNA160803', 1, 'V', 'median')
medianMosaicArr_ucd = nl_to_ucd_per_m2(medianMosaicArr)


# create 1-D arrays of alt and az coords
alt1 = n.arange(89.975,0,-0.05)
az1 = n.arange(-179.975,180,0.05)

# create 2-D arrays from 1-D arrays, with same shape as sky brightness array
interval = 90.0/7200
alt2 = n.arange(90-interval,-0.01,-interval)
__, alt = n.meshgrid(alt2, alt1, sparse=True)
interval = 360.0/1800
az2 = n.arange(-180+interval,180+interval,interval)
az, __ = n.meshgrid(az1, az2, sparse=True)

# convert altitude to zenith angle (theta)
theta = 90 - alt

# calculate solid angle in square radians for each pixel
solid_angle = (0.05**2) * n.sin(theta*n.pi/180)/(theta*n.pi/180) * (n.pi/180)**2

# calculate illuminance per pixel in mlx
E_i = medianMosaicArr_ucd * solid_angle / 1000


# Calculate horizontal illuminance
# cos(theta) factor accounts for angle of incidence, sin(theta) factor accounts for real
# sky area of pixels due to non-equal-area projection, exclude negative values from "no data" pixels and round
E_h_arr = E_i * n.cos(theta * n.pi/180) * n.sin(theta * n.pi/180)
E_h_arr = round(n.nansum(E_h_arr[E_h_arr > 0]), 9)


# Save results to a text file with three columns - azimuth in degrees, vert illum in mlx, horiz illum in mlx
output = open("illuminance_results.txt","w") 
output.write("Azimuth, Vertical Illuminance (mlx), Horizontal Illuminance (mlx)\n")
azimuth = n.arange(0,360,5)
for i in azimuth:
    output.write('{0}, {1}, {2}\n'.format(i, n.nan, E_h_arr))
output.close()

