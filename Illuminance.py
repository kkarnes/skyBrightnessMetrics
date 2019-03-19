#-----------------------------------------------------------------------------#
#illuminance.py
#
#NPS Night Skies Program
#
#Last updated: 2019/03/18
#
#This script calculates horizontal and vertical illuminance metrics from a mosaic image.
#The script does this in the following steps:
#	(1) Reads the raster image into a numpy array, converts units from nL to mlx
#	(2) Horizontal illuminance - applies a horizon mask and then calculates the horizontal illuminance value
#	(3) Vertical illuminance - calculates vertical illuminance values for azimuth angles 0 to 360 using a specified interval (set to 5)
#
#Input: 
#   (1) filepath.py -- contains a variable 'griddata' with the location/name of the working directory.
#		The directory should contain the raster image on which to calculate metrics (named 'skybrightnl') and 'mask.tif' (see below).
#		This is also the location where illuminance_results.txt will be saved.
#		Note: You should have a separate working directory for each dataset to be processed, and illuminance.py and filepath.py
#		should be stored above all those directories.
#   (2) mask.tif -- horizon mask raster image
#
#Output:
#   (1) illuminance_results.txt -- a text file with azimuth angle, vertical illuminance, and horizontal illuminance values
#   (2) A plot comparing the results for vertical illuminance from this script to the results from Dan's secondbatchv4.py script.
#		The plot can optionally be saved manually at the conclusion of the script.
#
#History:
#	Katie Karnes -- Created
#
#-----------------------------------------------------------------------------#

import archook
archook.get_arcpy()
import arcpy

import matplotlib.pyplot as plt
import numpy as n
import sys

# Local Source
import filepath

#-----------------------------------------------------------------------------#

def nl_to_ucd_per_m2(nl):
    """
    Unit conversion: converts brightness from nL to ucd/m^2
    """
    ucd_m2 = (10/n.pi)*nl
    return ucd_m2

def get_panoramic_raster(file):
    """    
    This function reads in a raster file and converts it into a numpy array. This 
    function does not work on full resolution mosaics due to limited memory space.

    Arguments:
    file -- name of the raster file to be read (str)

    Returns:
    A -- a 2D numpy array of shape [1920,7200]
	A_mask -- a 2D numpy array of shape [1800,7200]
    """
	# For vertical illuminance, sky area down to zenith angle = 96 deg is preserved (corresponds to 1920 px)
    arcpy_raster = arcpy.sa.Raster(file)  
    A = arcpy.RasterToNumPyArray(arcpy_raster, "#", "#", "#", -9999)[:1920,:7200] # for vert illum, crop to za = 96
	
	# For horizontal illuminance (horizon mask has already been applied), only sky area down to zenith angle = 90 deg is preserved (1800 px)
    file_mask = file + "_m"
    arcpy_raster_mask = arcpy.sa.Raster(file_mask)
    A_mask= arcpy.RasterToNumPyArray(arcpy_raster_mask, "#", "#", "#", -9999)[:1800,:7200]
	
    return A, A_mask

def get_horiz_illum(theta, E_i):
    """
    This function calculates horizontal illuminance from an array of sky illuminance values. The cos(theta) factor accounts for
	angle of incidence on the horizontal surface and the sin(theta) factor is the solid angle correction for each pixel.
    
    Arguments:
    theta -- array of zenith angles in degrees
    E_i -- array of illuminance values in mlx
    
    Returns:
    E_h -- horizontal illuminance value in mlx (float)
    """
    correction_factor = n.cos(n.deg2rad(theta)) * n.sin(n.deg2rad(theta))
    E_h = E_i * correction_factor
	# break into two calculations to reduce memory usage
    E_h1 = E_h[:,0:3600]
    E_h2 = E_h[:,3600:7201]
	# sum all positive values
    E_h1 = n.sum(E_h1[E_h1>0])
    E_h2 = n.sum(E_h2[E_h2>0])
    E_f = round(E_h1+E_h2, 9)
    return E_f

def vert_illuminance(phi_0, phi, az, theta, E_i):
    """    
    This function calculates the vertical illuminance value for a single phi_0 value on an array of sky brightness values.

    Arguments:
    phi_0 -- azimuth angle (in degrees) that the vertical surface faces
    phi -- array of possible angles of incidence on vertical surface (-90 to 90 degrees)
    az -- array of azimuth angles (in degrees)
    theta -- array of zenith angles (in degrees)
    E_i -- array of illuminance values in mlx

    Returns:
    E_v = vertical illuminance value in mlx for the given phi_0 value (float)
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
    
	# for most datasets, shape of selected_arr will match theta, but in some cases height of theta may need to be cropped at horizon
    height = n.shape(selected_arr)[0]
    theta = theta[:height,:]
    # cos(phi) is for angle of incidence along azimuth, first sin(theta) is for angle of incidence along altitude,
    # second sin(theta) is the solid angle correction for each pixel
    E_v_arr = selected_arr * n.cos(n.deg2rad(phi)) * n.sin(n.deg2rad(theta)) * n.sin(n.deg2rad(theta))
    # sum all positive values in the array
    E_v = n.nansum(E_v_arr[E_v_arr > 0])
    
    return E_v

def get_vert_illum_values(az, theta, E_i, interval):
    """
    This function calls the function vert_illuminance() for each phi_0 value in phi_0_range and returns an array
    of all the values returned by vert_illuminance()
    
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

def calculate_illuminance(az, theta, theta_96, E_i, E_i_mask, interval):
    """
	This function calls the functions to calculate both horizontal and vertical illuminance for a single image stored in an array
	and creates a text file with those values. The text file is comma-delimited with three columns:
	azimuth (in degrees), vertical illuminance (in mlx), and horizontal illuminance (in mlx).
	This function also displays a plot (which can be saved manually but is not automatically saved) that compares
	the vertical illuminance results from this script with results from Dan's 'secondbatchv4.py' script.
    
    Arguments:
    az -- array of azimuth angles in degrees
    theta -- array of zenith angles in degrees from 0 to 90
	theta_96 -- array of zenith angles in degrees from 0 to 96
    E_i -- array of illuminance values in mlx
	E_i_mask -- array of illuminance values in mlx after applying horizon mask to image
    interval -- azimuth interval (in degrees) at which to calculate vertical illuminance
    
    Returns:
    None
    """
	# call functions to calculate horizontal and vertical illuminance
    E_h = get_horiz_illum(theta, E_i_mask)
    E_v_arr = get_vert_illum_values(az, theta_96, E_i, interval)
    
	# open text file and write headers
    output = open(filepath.griddata + "\\illuminance_results.txt","w")
    output.write("Azimuth, Vertical Illuminance (mlx), Horizontal Illuminance (mlx)\n")
	# create new array of azimuth values for writing to text file
    azimuth = n.arange(0,360,interval)
    index = n.arange(0, n.size(azimuth), 1)
    
    Katie_data = n.zeros_like(azimuth, dtype=float)
    
    # reorder results in E_v_arr to match azimuth order (instead of -180 to 180, go from 0 to 360)
	# then write results to text file
    midpt = n.size(index)/2
    for i in index:
        if i < midpt:
            vert_illum = E_v_arr[i+midpt]
        else:
            vert_illum = E_v_arr[i-midpt]
        Katie_data[i] = vert_illum
        output.write('{0}, {1}, {2}\n'.format(azimuth[i], vert_illum, E_h))
    output.close()
	
    # plot and compare results with Dan's results - this was used for testing, but could be modified to just plot current results
    Dan_data = open(filepath.griddata + "\\Dan_results.txt").read().splitlines()
    Dan_data[:] = [float(line) for line in Dan_data]
    D, = plt.plot(n.arange(0,360,5), Dan_data, 'b.')
    K, = plt.plot(azimuth, Katie_data, 'r.')
    plt.legend([K, D], ['illuminance.py', 'secondbatchv4.py'])
    plt.xticks(range(0,361,45))
    plt.xlabel('Azimuth (degrees)')
    plt.ylabel('Vertical Illuminance (mlx)')
    plt.show()

# get raster image location from filepath.py
raster_filepath = filepath.griddata + "\\skybrightnl"

# apply horizon mask using arcpy
arcpy.CheckOutExtension("spatial")
output = arcpy.sa.SetNull(filepath.griddata+"\\mask.tif", raster_filepath, "Value = 0")
arcpy.env.overwriteOutput = True
output.save(raster_filepath + "_m")

# get array with median mosaic sky brightness values in nL from raster, then convert units
medianMosaicArr, medianMosaicArr_mask = get_panoramic_raster(raster_filepath)
medianMosaicArr = nl_to_ucd_per_m2(medianMosaicArr)
medianMosaicArr_mask = nl_to_ucd_per_m2(medianMosaicArr_mask)

# create arrays of theta (zenith angle) and azimuth coordinates
sky_coords = n.ogrid[0:90:1800j,-180:180:7200j]
theta = sky_coords[0]
az = sky_coords[1]
sky_coords_za96 = n.ogrid[0:96:1920j,-180:180:7200j]
theta_96 = sky_coords_za96[0]

# calculate solid angle in square radians, then illuminance in mlx
solid_angle = (n.deg2rad(0.05))**2 # is multiplied by the sin(theta) factor later in get_horiz_illum() and vert_illuminance()
E_i = medianMosaicArr * solid_angle / 1000
E_i_mask = medianMosaicArr_mask * solid_angle / 1000

# set the interval for azimuth angles at which to calculate vertical illuminance
interval = 5

calculate_illuminance(az, theta, theta_96, E_i, E_i_mask, interval)

sys.exit()

