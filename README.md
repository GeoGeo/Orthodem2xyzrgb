# Orthodem2xyzrgb

QGIS Plugin to create XYZRGB point cloud files from an Orthomosaic / DSM image pair 

You'll need
+ an orthorectified orthomosaic (normal or transparent)
+ a corresponding DSM

It's assumed that
+ the orthomosaic is a 3 band RGB
+ both orthomosaic and dsm are same extents, pixelsize and CRS
+ neither image is rotated (i.e. one edge is the N-S axis)

You can choose
+ the sample interval N. The points are sampled in the X and Y directions every N pixels
+ optionally, NoData values used in the mosaic (done as a comma separated list of integers) to ignore
+ one of several output formats (XYZ/XYZRGB, comma or space seperator)
+ whether or not to include field headers
+ whether or not to output nodata values
+ if you choose to output nopixel values, the z value to use
+ whether or not to jitter the output points. This involves nudging the x,y values by up to +/- 1/3 of the sample interval. This option can improve point cloud rendering by avoiding banding and moire artifacts.

You can view the pointcloud in a number of ways...
- using SAGA, import point cloud from text file (use X,Y,Z format)
- the point cloud viewer from Mapbox ( https://github.com/mapbox/pointcloud ). Use the "X Y Z R G B" option
- QGIS, by using the "x,y,z,r,g,b" format with headers enabled, and loading in as a POINT layer from a CSV file

To get you started there are a sample DSM and Orthomosaic in the plugin folder.
