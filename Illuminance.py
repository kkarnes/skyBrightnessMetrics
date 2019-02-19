#-----------------------------------------------------------------------------#
#illuminance.py
#
#NPS Night Skies Program
#
#Last updated: 2019/02/15
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
import matplotlib.pyplot as plt
import numpy as n
#import os
#import shutil
import sys

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
    A -- a 2D Python array of shape [1800,7200]
    """
    filter = {'V':"",'B':"/B"}
    path = {'gal':"/gal/galtopmags",
            'zod':"/zod/zodtopmags",
            'median':filter[band]+"/median/skybrightmags"}

    # file = filepath.griddata+dnight+"/S_0"+str(set)+path[raster]
    file = filepath.griddata
    arcpy_raster = arcpy.sa.Raster(file)  
    A = arcpy.RasterToNumPyArray(arcpy_raster, "#", "#", "#", -9999)[:1800,:7200]
    return A

def get_horiz_illum(theta, E_i):
    """
    This function calculates horizontal illuminance from an array of sky illuminance values. The cos(theta) factor accounts for
	angle of incidence on the horizontal surface and the sin(theta) factor is the solid angle correction for each pixel.
    
    Arguments:
    theta -- array of zenith angles in degrees
    E_i -- array of illuminance values in mlx
    
    Returns:
    E_h -- horizontal illuminance value in mlx
    """
    E_h_arr = E_i * n.cos(theta * n.pi/180) * n.sin(theta * n.pi/180)
    E_h = round(n.nansum(E_h_arr[E_h_arr > 0]), 9)
    return E_h

def vert_illuminance(phi_0, phi, az, theta, E_i):
    """    
    This function calculates the vertical illuminance value for a single phi_0 value on an array of sky brightness values.

    Arguments:
    phi_0 -- azimuth angle (in degrees) that the vertical surface faces
    phi -- array of possible angles of incidence on vertical surface (-90 to 90 degrees)
    az -- array of azimuth angles in degrees
    theta -- array of zenith angles in degrees
    E_i -- array of illuminance values in mlx

    Returns:
    E_v = vertical illuminance value in mlx for the given phi_0 value
    """
    # define start and end values around phi_0
    start = phi_0 - 90
    end = phi_0 + 90
    if start < -180:
        start = start + 360
    if end > 180:
        end = end - 360
    
    # use indices based on az to select correct columns of sky brightness in E_i
    if (phi_0 < -90) | (phi_0 > 90):
        indices = n.transpose(n.concatenate((n.where(az >= start), n.where(az <= end)),1))[:,1]
    else:
        indices = n.transpose(n.where((az >= start) & (az <= end)))[:,1]
    selected_arr = E_i[:,indices]
    
    # cos(phi) is for angle of incidence along azimuth, first sin(theta) is for angle of incidence along altitude,
    # second sin(theta) is the solid angle correction for each pixel
    E_v_arr = selected_arr * n.cos(n.deg2rad(phi)) * n.sin(n.deg2rad(theta)) * n.sin(n.deg2rad(theta))
    # sum all positive values in the array
    E_v = n.nansum(E_v_arr[E_v_arr > 0])
    
    return E_v

def get_vert_illum_values(az, theta, E_i, interval):
    """
    This function calls vertical_illuminance for all the phi_0 values in phi_0_range and returns an array
    of all the vertical illuminance values.
    
    Arguments:
    az -- array of azimuth angles in degrees
    theta -- array of zenith angles in degrees
    E_i -- array of illuminance values in mlx
    interval -- azimuth interval (in degrees) at which to calculate vertical illuminance
    
    Returns:
    E_v_arr -- array of vertical illuminance values for azimuth angles 0 to 360, using the specified interval
    """
    # create array of all phi_0 values to calculate vertical illuminance for
    phi_0_range = n.arange(-180, 180, interval)
    # create array of possible angle of incidence values
    phi = n.linspace(-90, 90, 3600)
    
    # calculate vertical illuminance for each phi_0 value in phi_0_range and store all results in an array
    E_v_arr = n.array([])
    for phi_0 in phi_0_range:
        E_v_arr = n.append(E_v_arr, vert_illuminance(phi_0, phi, az, theta, E_i))
        
    return E_v_arr

def calculate_illuminance(az, theta, E_i, interval):
    """
	This function calls the functions to calculate both horizontal and vertical illuminance for a single array
	and creates a text file with those values. The text file is comma-delimited with three columns:
	azimuth (in degrees), vertical illuminance (in mlx), and horizontal illuminance (in mlx).
	This function also currently displays a plot comparing vertical illuminance results from this script with results from Dan Duriscoe's code.
    
    Arguments:
    az -- array of azimuth angles in degrees
    theta -- array of zenith angles in degrees
    E_i -- array of illuminance values in mlx
    interval -- azimuth interval (in degrees) at which to calculate vertical illuminance
    
    Returns:
    None
    """
    E_h = get_horiz_illum(theta, E_i)
    E_v_arr = get_vert_illum_values(az, theta, E_i, interval)
    
    output = open("illuminance_results_vertical.txt","w")
    output.write("Azimuth, Vertical Illuminance (mlx), Horizontal Illuminance (mlx)\n")
    azimuth = n.arange(0,360,interval)
    index = n.arange(0, n.size(azimuth), 1)
    
    Katie_data = n.zeros_like(azimuth, dtype=float)
    
    # changes order from -180-180 to 0-360
    midpt = n.size(index)/2
    for i in index:
        if i < midpt:
            vert_illum = E_v_arr[i+midpt]
        else:
            vert_illum = E_v_arr[i-midpt]
        Katie_data[i] = vert_illum
        output.write('{0}, {1}, {2}\n'.format(azimuth[i], vert_illum, E_h))
    output.close()
	
    # plot results for comparison
    Dan_data = open("Dan_E_v_results.txt").read().splitlines()
    Dan_data[:] = [float(line) for line in Dan_data]
    D, = plt.plot(n.arange(0,360,5), Dan_data, 'b.')
    K, = plt.plot(azimuth, Katie_data, 'r.')
    plt.legend([K, D], ['Katie', 'Dan'])
    plt.xticks(range(0,361,45))
    plt.xlabel('Azimuth (degrees)')
    plt.ylabel('Vertical Illuminance (mlx)')
    plt.show()

# specify data to run
dnight = 'FCNA160803'
dset = 1
band = 'V'
raster = 'median'

# get array with median mosaic sky brightness values in nL from raster, then convert units
medianMosaicArr = get_panoramic_raster(dnight, dset, band, raster)
medianMosaicArr_ucd = nl_to_ucd_per_m2(medianMosaicArr)

# create arrays of theta (zenith angle) and azimuth coordinates
sky_coords = n.ogrid[0:90:1800j,-180:180:7200j]
theta = sky_coords[0]
az = sky_coords[1]

# calculate solid angle in square radians, then illuminance in mlx
solid_angle = (n.deg2rad(0.05))**2
E_i = medianMosaicArr_ucd * solid_angle / 1000

calculate_illuminance(az, theta, E_i, 5)

sys.exit()

