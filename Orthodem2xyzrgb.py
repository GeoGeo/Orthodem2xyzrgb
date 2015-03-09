# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Orthodem2xyzrgb
                                 A QGIS plugin
 This plugin creates xyzrgb point clouds
                              -------------------
        begin                : 2015-03-03
        git sha              : $Format:%H$
        copyright            : (C) 2015 by Steven Kay GeoGeo
        email                : steven@geogeoglobal.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.gui import QgsMessageBar

# Initialize Qt resources from file resources.py
import resources_rc
# Import the code for the dialog
from Orthodem2xyzrgb_dialog import Orthodem2xyzrgbDialog
import os.path
from qgis.core import *
import traceback
import time
from rastertools import *
import random
import re

class Worker(QtCore.QObject):
    
    '''
    Worker thread. Based on example from 
    '''
    
    def __init__(self, widjet):
        
        QtCore.QObject.__init__(self)
        
        self.killed = False
        self.wid = widjet
        mynodata = []
        self.style = self.wid.dlg.cbFormat.currentIndex()
        self.headers = self.wid.dlg.cbHeaders.isChecked()
        if self.wid.dlg.cbNoData.isChecked():
            nodatavals = self.wid.dlg.leNoData.text()
            nodatavals = re.sub("\s+","",nodatavals)
            nodatavals = re.sub("[,]","|",nodatavals)
            mynodatatext = nodatavals.split("|")
            for x in mynodatatext:
                try:
                    mynodata.append(int(x))
                except:
                    pass
            print "Using nodata = %s" % str(mynodata)
        self.rdr = RastersToXYZRGB(self.wid.dlg.leOrthomosaic.text(),
                      self.wid.dlg.leDem.text(),
                      self.wid.dlg.mQgsSpinBox.value(),
                      nodata = mynodata)
    
    def getstartinfo(self):
        '''
        pre-run information from rasters
        '''
        inform = ["Raster size is (%d x %d)" % (self.rdr.red.cols, self.rdr.red.rows) ]
        inform.append("Size in samples (%d x %d)" % (self.rdr.red.xtiles, self.rdr.red.ytiles))
        resstep = float( self.rdr.red.xpixelsize * self.rdr.red.tilesize )
        inform.append("Sample resolution %2.3fm" % resstep)
        return "\n".join([str(x) for x in inform])
    
    def getendinfo(self, took, ct):
        '''
        post-run information
        '''
        inform = ["Raster size is (%d x %d)" % (self.rdr.red.cols, self.rdr.red.rows) ]
        inform.append("Size in samples (%d x %d)" % (self.rdr.red.xtiles, self.rdr.red.ytiles))
        resstep = float( self.rdr.red.xpixelsize * self.rdr.red.tilesize )
        inform.append("Sample resolution %2.3fm" % resstep)
        inform.append("Took %2.2f seconds" % took)
        inform.append("Wrote %d points" % ct)
        inform.append("Dropped %d nodata points" % self.rdr.dropped)
        return "\n".join([str(x) for x in inform])
    
    def formatline (self, style, x, y, z, r, g, b):
        if style == 0:
            return "%2.4f,%2.4f,%2.4f,%d,%d,%d\n" % (x, y, z, r, g, b)
        if style == 1:
            return "%2.4f,%2.4f,%2.4f\n" % (x, y, z)
        if style==2:
            return "%2.4f %2.4f %2.4f\n" % (x, y, z)
        if style==3:
            return "%2.4f %2.4f %2.4f %d %d %d\n" % (x, y, z, r, g, b)
        return ""
    
    def formatheaders (self, style):
        if style == 0:
            return "X,Y,Z,R,G,B\n" 
        if style == 1:
            return "X,Y,Z\n" 
        if style == 2:
            return "X Y Z\n"
        if style == 3:
            return "X Y Z R G B\n"
        return ""
      
    def run(self):
        ret = None
        self.progresstext.emit("Started...")
        fo = open(self.wid.dlg.leOutputFilename.text(),"w")
        16
        self.infotext.emit(self.getstartinfo())
        ct = 0
        tick = time.time()
        if self.headers:
            fo.write(self.formatheaders(self.style))
        jitter = self.rdr.red.xpixelsize *.333
        try:
            lastprogress = 0
            
            for prog, point in self.rdr.getPointsAndProgress():
                if len(point) > 0:
                    x,y,z,r,g,b = point
                    x = x - jitter + (2.0*random.random()*jitter)
                    y = y - jitter + (2.0*random.random()*jitter)
                    line = self.formatline (self.style, x, y, z, r, g, b)
                    fo.write(line)
                    ct += 1
                    
                if self.killed is True:
                    # kill request received, exit loop early
                    self.progresstext.emit("Job cancelled.")
                    break
                
                if (int(prog) > lastprogress):
                    # emit signal every 1%
                    lastprogress = int(prog)
                    self.progress.emit(lastprogress)
                    coverage = (float(ct) / (float(ct)+float(self.rdr.dropped))) * 100.0
                    progmess = "Progress - %d%% done. %d points, %d nodata points (coverage is %2.1f%%)" % (lastprogress, ct, self.rdr.dropped, coverage)
                    self.progresstext.emit(progmess)
                    # update info box
                    took = time.time()- tick
                    self.infotext.emit(self.getendinfo(took, ct)) 
                
            if self.killed is False:
                self.progress.emit(100)
                ret = (None,None)
                
        except Exception, e:
            # send error to GUI
            self.error.emit(e, traceback.format_exc())
        
        fo.flush()
        fo.close()
        took = time.time()- tick
        self.progresstext.emit("Finished in %2.4f secs" % took)
        self.finished.emit(ret)
        
    def kill(self):
        self.killed = True
        
    finished = QtCore.pyqtSignal(object)
    error = QtCore.pyqtSignal(Exception, basestring)
    progress = QtCore.pyqtSignal(float)
    progresstext = QtCore.pyqtSignal(basestring)
    infotext = QtCore.pyqtSignal(basestring)

class Orthodem2xyzrgb(object):
    """
    QGIS Plugin Implementation.
    """

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'Orthodem2xyzrgb_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and
        self.dlg = Orthodem2xyzrgbDialog()

        # Declare instance attributese
        self.actions = []
        self.menu = self.tr(u'&Create xyzrgb from Mosaic/DSM')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'Orthodem2xyzrgb')
        self.toolbar.setObjectName(u'Orthodem2xyzrgb')

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('Orthodem2xyzrgb', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to Tr
        self.layer = layerue.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """
        Create GUI
        """

        icon_path = ':/plugins/Orthodem2xyzrgb/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Point Cloud from Rasters'),
            callback=self.run,
            parent=self.iface.mainWindow())

    def unload(self):
        """
        Removes the plugin menu item and icon from QGIS GUI.
        """
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Create xyzrgb from Mosaic/DSM'),
                action)
            self.iface.removeToolBarIcon(action)

    def workerExceptionThrown(self, exc, tb):
        """
        clean up the worker and thread
        """
        self.worker.deleteLater()
        self.thread.quit()
        self.thread.wait()
        self.thread.deleteLater()
        print str(tb)
        self.iface.messageBar().pushMessage('Error:' + str(tb), level=QgsMessageBar.CRITICAL, duration=3)
        
        
    def workerFinished(self, ret):
        """
        clean up the worker and thread
        """
        self.worker.deleteLater()
        self.thread.quit()
        self.thread.wait()
        self.thread.deleteLater()
        # remove widget from message bar
        self.iface.messageBar().popWidget(self.messageBar)
        if ret is not None:
            # report the result
            #layer, total_area = ret
            self.iface.messageBar().pushMessage('Finished!')
        else:
            # notify the user that something went wrong
            self.iface.messageBar().pushMessage('Job cancelled.', level=QgsMessageBar.WARNING, duration=3)
            
    def startWorker(self):
        """
        Start task in a separate worker thread
        """
        worker = Worker(self)
    
        # configure the QgsMessageBar
        messageBar = self.iface.messageBar().createMessage('Started to create file', )
        progressBar = self.dlg.progressBar
        cancelButton = self.dlg.pbCancel
        cancelButton.clicked.connect(worker.kill)
        self.iface.messageBar().pushWidget(messageBar, self.iface.messageBar().INFO)
        self.messageBar = messageBar
    
        # start the worker in a new thread
        thread = QtCore.QThread()
        worker.moveToThread(thread)
        worker.finished.connect(self.workerFinished)
        worker.error.connect(self.workerExceptionThrown)
        worker.progress.connect(self.dlg.progressBar.setValue)
        worker.progresstext.connect(self.dlg.lbProgress.setText)
        worker.infotext.connect(self.dlg.txInfo.setText)
        thread.started.connect(worker.run)
        thread.start()
        self.thread = thread
        self.worker = worker

    def choosefilenameortho(self, e):
        """
        file chooser for orthomosaic
        """
        filename = QFileDialog.getOpenFileName(self.dlg,"Select TIFF file",
            "/home", "TIF files (*.tif);;All files (*.*)")
        if filename:
            self.dlg.leOrthomosaic.setText(filename)
    
    def choosefilenamedsm(self, e):
        """
        file chooser for DSM file
        """
        filename = QFileDialog.getOpenFileName(self.dlg,"Select TIFF file",
            "/home", "TIF files (*.tif);;All files (*.*)")
        if filename:
            self.dlg.leDem.setText(filename)

    def run(self):
        """
        Wire in the event bindings
        """
        # show the dialog
        self.dlg.pbOrtho.clicked.connect(self.choosefilenameortho)
        self.dlg.pbDem.clicked.connect(self.choosefilenamedsm)
        
        self.dlg.pbStart.clicked.connect(self.startWorker)
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass
