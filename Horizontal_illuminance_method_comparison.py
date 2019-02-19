#-----------------------------------------------------------------------------#
#illuminance.py
#
#NPS Night Skies Program
#
#Last updated: 2019/02/19
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
#   (1) A txt file listing the azimuth angle, vertical illuminance, and 
#       horizontal illuminance
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
import matplotlib.pyplot as plt
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
    ucd = (10/n.pi)*nl
    return ucd

def get_panoramic_raster(dnight, set, band, raster):
    """    
    This function reads in a raster file and converts it into a Python array. 
    Only area above the horizon is preserved to enforce consistency. This 
    function does not work on full resolution mosaics due to limited memory space.

    Arguments:
    dnight -- data night; i.e. 'FCNA160803'
    set -- data set; i.e. 1 
    band -- filter; either 'V' or 'B'
    raster -- input raster; either 'gal', 'zod', or 'median' but not 'fullres'

    Returns:
    A -- a 2D Python array of shape [1800,7200]/k   
    """
    filter = {'V':"",'B':"/B"}
    path = {'gal':"/gal/galtopmags",
            'zod':"/zod/zodtopmags",
            'median':filter[band]+"/median/skybrightmags"}
            
    #file = filepath.griddata+dnight+"/S_0"+str(set)+path[raster]
    file = filepath.griddata
    arcpy_raster = arcpy.sa.Raster(file)  
    A = arcpy.RasterToNumPyArray(arcpy_raster, "#", "#", "#", -9999)[:1800,:7200]
    return A

# get numpy array with median mosaic sky brightness values in nL, then convert units
medianMosaicArr = get_panoramic_raster('FCNA160803', 1, 'V', 'median')
sky_ucd = nl_to_ucd_per_m2(medianMosaicArr)

# create arrays of theta (zenith angle) and azimuth coordinates
sky_coords = n.ogrid[0:90:1800j,-180:180:7200j]
theta = sky_coords[0]
az = sky_coords[1]

def get_horiz_illum_method_1(sky_ucd, theta):
    """
    This function calculates the horizontal illuminance for an array of sky brightness values over the entire sky
    hemisphere. This method of calculating the solid angle evaluates a double integral, over the surface S, of
    sin(theta)d(theta)d(phi), where S is one pixel. The integral evaluates to d(phi) * (-cos(theta2) - (-cos(theta1))).
    
    Arguments:
    sky_ucd -- array of sky brightness values from a mosaic image in ucd/m^2
    theta -- array of the same shape with corresponding zenith angles for each value in sky_ucd
    
    Returns:
    E_h -- total horizontal illuminance summed over all pixels
    """
    # calculate solid angle in square radians for each pixel
    solid_angle = (n.deg2rad(0.05)) * (-n.cos(n.deg2rad(theta+0.025)) - (-n.cos(n.deg2rad(theta-0.025))))
    # calculate illuminance per pixel in mlx
    E_i = sky_ucd * solid_angle / 1000
    # cos(theta) factor accounts for angle of incidence
    E_h_arr = E_i * n.cos(n.deg2rad(theta))
    # sum illuminance from each pixel and exclude negative values from NoData pixels
    E_h = n.sum(E_h_arr[E_h_arr > 0])
    
    return E_h

def get_horiz_illum_method_2(sky_ucd, theta):
    """
    This function calculates the horizontal illuminance for an array of sky brightness values over the entire sky
    hemisphere. This method multiplies the sky brightness array by a factor of sin(theta), which scales in proportion 
	to the area of each pixel.
    
    Arguments:
    sky_ucd -- array of sky brightness values from a mosaic image in ucd/m^2
    theta -- array of the same shape with corresponding zenith angles for each value in sky_ucd
    
    Returns:
    E_h -- total horizontal illuminance summed over all pixels
    """
    # calculate solid angle in square radians for each pixel
    solid_angle = (n.deg2rad(0.05))**2
    # calculate illuminance per pixel in mlx
    E_i = sky_ucd * solid_angle / 1000
    # cos(theta) factor accounts for angle of incidence, sin(theta) factor accounts for pixel area
    E_h_arr = E_i * n.cos(n.deg2rad(theta)) * n.sin(n.deg2rad(theta))
    # sum illuminance from each pixel and exclude negative values from NoData pixels
    E_h = n.sum(E_h_arr[E_h_arr > 0])
	
    return E_h

E_h_1 = get_horiz_illum_method_1(sky_ucd, theta)
E_h_2 = get_horiz_illum_method_2(sky_ucd, theta)

print("Method 1: " + str(E_h_1))
print("Method 2: " + str(E_h_2))

# Save results to a text file with three columns - azimuth in degrees, vert illum in mlx, horiz illum in mlx
output = open("illuminance_results.txt","w")
output.write("Azimuth, Vertical Illuminance (mlx), Horizontal Illuminance (mlx)\n")
azimuth = n.arange(0,360,5)
for i in azimuth:
    output.write('{0}, {1}, {2}\n'.format(i, n.nan, E_h_1))
output.close()

