# Orthodem2xyzrgb

QGIS Plugin to create XYZRGB point clouds from an Orthomosaic/DSM pair 

You'll need
+ an orthorectified orthomosaic (normal or transparent)
+ a corresponding DSM

You can choose
+ the sample interval N. The points are sampled in the X and Y directions every N pixels
+ optionally, NoData values used in the mosaic (done as a comma separated list of integers) to ignore
+ one of several output formats (XYZ/XYZRGB, comma or space seperator)
+ whether or not to include field headers

It's assumed that
+ the orthomosaic is a 3 band RGB
+ both orthomosaic and dsm are same extents, pixelsize and CRS
+ neither image is rotated (i.e. one edge is the N-S axis)
