# Night Skies Illuminance Metric Calculations

<!-- Table of Contents -->

- [Purpose](#purpose)
- [Required Software](#required-software)
- [Documentation](#documentation)
  - [Workflow Summary](#1-workflow-summary)
  - [Required Files](#2-required-files)
  - [Projecting a 3D sky onto a 2D image](#3-projecting-a-3d-sky-onto-a-2d-image)
    - [Solid Angle Derivation](#solid-angle-derivation)
  - [Calculating Illuminance](#4-calculating-illuminance)
    - [Horizontal illuminance](#horizontal-illuminance)
    - [Vertical Illuminance](#vertical-illuminance)
  - [Output](#5-output)
- [Public Domain](#public-domain)

## Purpose
Photometric indicators can be used to quantify night sky quality by measuring the amount of natural and artifical light in the sky. *Observed* and *estimated artificial* values can be calculated for each indicator. *Observed* values are calculated from calibrated images that represent what an observer on the ground would see. *Estimated artificial* values are calculated from images after a model of the natural sky background has been subtracted.

Natural reference conditions for each indicator have also been determined. Using the estimated artificial value and the natural reference condition for a given indicator, a unitless *Light Pollution Ratio* can be calculated. The Light Pollution Ratio allows for direct comparison of indicators from one site to another.

Photometric indicators include measures of both luminance and illuminance. This script (`illuminance.py`) calculates two illuminance indicators: horizontal illuminance and vertical illuminance. The script is designed to be run on mosaic images created using the [NPS NSNSD Night Skies Data Reduction Pipeline.](https://github.com/liweihung/nightskies) The Data Reduction Pipeline output includes four mosaic images -- galactic mosaic, zodiacal mosaic, full-resolution mosaic, and a median-filtered mosaic. To determine the *observed* indicators described above, this script should be run on the median mosaic image.

## Required Software
This script was developed using Anaconda version 5.3. The NightSkies environment (`NightSkies.yml`) is available in this repository. Python 2.7, archook, arcpy, numpy, and matplotlib are required.

## Documentation
The metrics and methods implemented in this script and described below were adopted from and are described more thoroughly in [Duriscoe, 2016](https://doi.org/10.1016/j.jqsrt.2016.02.022)<sup>1</sup>.

### 1. Workflow Summary

![Flowchart of functions, scripts, and files](https://github.com/kkarnes/skyBrightnessMetrics/blob/master/static/Illuminance_script_flowchart.png)

### 2. Required Files
`filepath.py` stores the location of the mosaic raster image that you want to calculate metrics on in the variable `griddata`.

`mask.tif` is a raster image that contains a horizon mask (this is also an output product of the NSNSD Data Reduction Pipeline). The mask is applied to the mosaic image before calculating horizontal illuminance.

### 3. Projecting a 3D sky onto a 2D image
The mosaic images are rectangular in shape. Of course, the sky itself is not. In order to properly account for the projection of pieces of the sky onto pixels in our image, it is necessary to consider how much sky area each pixel represents. Each pixel does not represent a constant solid angle in the sky, rather, the solid angle subtended by each pixel varies with zenith angle.

#### Solid Angle Derivation

<img src="https://github.com/kkarnes/skyBrightnessMetrics/blob/master/static/solid_angle_derivation_1.PNG" alt="Derivation of solid angle formula">

<img src="https://github.com/kkarnes/skyBrightnessMetrics/blob/master/static/solid_angle_derivation_2.PNG" alt="Derivation of solid angle formula">

**Note:**
These two factors of the solid angle above appear in the calculations in this script at different times. The solid angle is first defined as (0.05&deg;)<sup>2</sup> and is later multipled by sin&theta; during the horizontal and vertical illuminance calculations. This is done in two separate steps simply due to the fact that the shape of the theta array is not the same for the horizontal and vertical illuminance calculations (theta values range to 90&deg; and 96&deg; respectively).

### 4. Calculating Illuminance
One input to this script is a mosaic image raster that contains sky brightness values in nanolamberts (nL). Once the values have been read into a 2D numpy array, these sky brightness values are converted from nanolamberts to sky brightness luminance values (b<sub>i</sub>), which has units of &mu;cd m<sup>-2</sup>. Illuminance can be calculated from b<sub>i</sub> using the equation below.

<img src="https://github.com/kkarnes/skyBrightnessMetrics/blob/master/static/E_i.PNG" alt="Illuminance equation" height="90">

#### Natural Reference Conditions
As was mentioned above, natural reference conditions (given a moonless night) are derived for each indicator to allow for the calculation of light pollution ratios. The natural reference conditions for horizontal and vertical maximum illuminance are 0.8 millilux and 0.4 millilux respectively.

#### Horizontal Illuminance
Horizontal illuminance (E<sub>h</sub>) is calculated using the equation below. It is reported in millilux (mlx) and measures the amount of light striking a flat, horizontal surface such as the ground. Before beginning these calculations, a horizon mask is applied (see [Required Files](#2-required-files)) to remove non-sky areas from the image.

<img src="https://github.com/kkarnes/skyBrightnessMetrics/blob/master/static/E_h.PNG" alt="Horizontal illuminance equation" height="90">

The zenith angle, &theta;, ranges from 0&deg; at the zenith to 90&deg; at the horizon. Cos&theta;, therefore, ranges from one at the zenith to zero at the horizon. The cos&theta; factor accounts for the angle of incidence of the light striking the horizontal surface. Light coming from the zenith hits the horizontal surface perpendicularly, while only a small percentage of the light coming from near the horizon will directly strike the surface, and light coming from the horizon itself travels parallel to the surface and will not illuminate the surface at all.

#### Vertical Illuminance
Vertical illuminance measures the amount of light striking a flat, vertical surface. This vertical plane can face any direction (azimuth) around the horizon, so vertical illuminance values are calculated for all azimuth values (0&deg; to 360&deg;) in a specified increment (typically 5&deg;). The interval can be changed in `illuminance.py`.

<img src="https://github.com/kkarnes/skyBrightnessMetrics/blob/master/static/E_v.PNG" alt="Vertical illuminance equation" height="90">

For a vertical surface, the angle of incidence of light on the surface varies with both zenith angle (&theta;) and the angle along the azimuth axis between the light and the direction the surface faces (&Phi;). Note that in the equation above, the azimuth of the vertical surface is &Phi;<sub>i</sub>, while the angle of incidence of the light on the vertical surface is &Phi;.

### 5. Output
This script creates a comma-delimited text file with three columns: azimuth (in degrees), vertical illuminance (in mlx), and horizontal illuminance (in mlx). The azimuth values vary depending on the interval set in `illuminance.py`. The second and third columns, respectively, contain the corresponding vertical illuminance value and the image's horizontal illuminance value (which does not vary with azimuth).

A simple plot is useful for visualizing how vertical illuminance varies with azimuth for a certain image. Plots were also used during development for comparison purposes to ensure that the illuminance values produced by this script are consistent with the results from Dan Duriscoe's illuminance calculations in his script `secondbatchv4.py`. The sample plot below, created by running this script on data collected at Badlands National Park in 2018, demonstrates that `illuminance.py` successfully reproduces the results from `secondbatchv4.py`.

![Plot comparing vertical illuminance methods from two scripts](https://github.com/kkarnes/skyBrightnessMetrics/blob/master/static/BADL_plot.png)

<sup><sup>1</sup></sup> <sup>Duriscoe, Dan M. "Photometric indicators of visual night sky quality derived from all-sky brightness maps." Journal of Quantitative Spectroscopy and Radiative Transfer (2016): 181, 33-45.</sup>

## Public Domain
This project is in the public domain within the United States, and copyright and related rights in the work worldwide are waived through the [CC0 1.0 Universal public domain dedication](https://creativecommons.org/publicdomain/zero/1.0/).

All contributions to this project will be released under the CC0 dedication. By submitting a pull request, you are agreeing to comply with this waiver of copyright interest.
