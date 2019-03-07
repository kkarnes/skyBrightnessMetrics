# Night Skies Metric Calculations

## Purpose
Photometric indicators are used to quantify night sky quality -- the relative amounts of natural and artifical light in the sky. 'Observed' values are calculated using calibrated images that represent what an observer on the ground would see. 'Estimated artifical' values are calculated on images after a model of the natural sky background has been subtracted. Natural reference conditions for each indicator have also been determined. Using the estimated artificial value and the natural reference condition for a given indicator, a unitless 'light pollution ratio' can be calculated. Light pollution ratios allow for direct comparison of indicators from one site to another.

Photometric indicators include measures of both luminance and illuminance. This `illuminance.py` script calculates two illuminance indicators: horizontal illuminance and vertical illuminance.

This script is designed to be run on mosaic images created using the [NPS NSNSD Night Skies Data Reduction Pipeline.](https://github.com/liweihung/nightskies) The Data Reduction Pipeline output includes four mosaic images -- galactic mosaic, zodiacal mosaic, full-resolution mosaic, and a median-filtered mosaic. This script is intended for use on the median-filtered mosaic image (to determine 'observed' values as describe above) and for use on images after the natural sky background has been subtracted (to determine 'estimated artificial' values).

<!--- insert image
![median-filtered mosaic image](https://github.com/kkarnes/skyBrightnessMetrics/blob/master/static/.png)
--->

## Required Software
This script was developed using Anaconda version 5.3. The NightSkies environment (`NightSkies.yml`) is available in this repository. Python 2.7, archook, arcpy, numpy, and matplotlib are required.

## Documentation
The metrics and methods implemented in this script and described below were adopted from and are described more thoroughly in [Duriscoe, 2016](https://doi.org/10.1016/j.jqsrt.2016.02.022).

### Workflow Summary

![Flowchart of functions, scripts, and files](https://github.com/kkarnes/skyBrightnessMetrics/blob/master/static/Illuminance_script_flowchart.png)

### 1. Other Required Files
`filepath.py` stores the location of the mosaic raster image that you want to calculate metrics on in the variable `griddata`.

`mask.tif` is a raster image that contains a horizon mask. The mask is applied to the mosaic image before calculating horizontal illuminance.

### 2. Projecting a 3D sky onto a 2D image
The mosaic images are rectangular in shape. Of course, the sky itself is not. In order to properly account for the projection of pieces of the sky onto pixels in our image, it is necessary to consider how much sky area each pixel represents. Each pixel does not represent a constant solid angle in the sky, rather, the solid angle subtended by each pixel varies with zenith angle.

#### Solid Angle Derivation

The solid angle of any surface can be calculated using the following equation:

<!--- insert eq ![solid angle double integral equation]() --->

For our purposes, we evaluate the double integral for a single pixel in the sky:

<!--- insert evaluation of integral ![]() --->

This equation can be simplified by using the small-angle approximation as follows:

<!--- insert derivation ![]() --->

We use this simplified expression to calculate the solid angle in the illuminance calculations.

<!---
Show where/how it's implemented in the code:
The first two lines of `get_horiz_illum()` multiply the sky illuminance (E<sub>i</sub>)by a correction factor that includes both a cos(theta) and sin(theta) factor.
```
correction_factor = n.cos(n.deg2rad(theta)) * n.sin(n.deg2rad(theta))
E_h = E_i * correction_factor
```
solid angle factor:
The sin(theta) portion of the correction factor 
angle of incidence:
Theta (the zenith angle) ranges from 0&deg; at the zenith to 90&deg; at the horizon. The cosine of the zenith angle, therefore, ranges from 1 at the zenith to 0 at the horizon. This portion of the correction factor accounts for the angle of incidence of the light. This correction factor comes from `get_horiz_illum`; we are considering how much light strikes a flat horizontal surface. Light coming from the zenith hits perpendicular to the horizontal surface and all of the light illuminates the surface at that point. On the other hand, only a small percentage of the light coming from just above the horizon will illuminate the surface, and light coming from the horizon itself, parallel to the surface, will not illuminate the surface at all. The cos(theta) factor accounts for this.
This is done in two separate steps simply due to the fact that the shape of the theta array is not the same for the horizontal and vertical illuminance calculations (theta values range to 90 and 96 degrees respectively).
--->

### 3. Horizontal Illuminance 
Horizontal illuminance is reported in milli-lux (mlx) and measures the amount of light striking a flat, horizontal surface such as the ground.

### 4. Vertical Illuminance
Vertical illuminance is also reported in mlx and measures the amount of light striking a flat, vertical surface. This vertical plane can face any direction around the horizon, so vertical illuminance is calculated for all azimuth values using a given increment (typically five degrees). The maximum vertical illuminance value is the value when the surface is facing the sky in the brightest direction.

#### References
<sup>Duriscoe, Dan M. "Photometric indicators of visual night sky quality derived from all-sky brightness maps." Journal of Quantitative Spectroscopy and Radiative Transfer (2016): 181, 33-45.</sup>

## Public Domain
This project is in the public domain within the United States, and copyright and related rights in the work worldwide are waived through the [CC0 1.0 Universal public domain dedication](https://creativecommons.org/publicdomain/zero/1.0/).

All contributions to this project will be released under the CC0 dedication. By submitting a pull request, you are agreeing to comply with this waiver of copyright interest.
