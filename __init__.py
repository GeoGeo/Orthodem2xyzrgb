# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Orthodem2xyzrgb
                                 A QGIS plugin
 This plugin creates xyzrgb point clouds
                             -------------------
        begin                : 2015-03-03
        copyright            : (C) 2015 by Steven Kay GeoGeo
        email                : steven@geogeoglobal.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load Orthodem2xyzrgb class from file Orthodem2xyzrgb.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .Orthodem2xyzrgb import Orthodem2xyzrgb
    return Orthodem2xyzrgb(iface)
