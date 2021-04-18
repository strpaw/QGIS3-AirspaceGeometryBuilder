# -*- coding: utf-8 -*-
"""
/***************************************************************************
 AirspaceGeometryBuilder
                                 A QGIS plugin
 Create polygon based on common used description in aviation.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2021-04-09
        git sha              : $Format:%H$
        copyright            : (C) 2021 by Paweł Strzelewicz
        email                : @
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
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, QVariant
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QWidget, QMessageBox
from qgis.core import *

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .airspace_geometry_builder_dialog import AirspaceGeometryBuilderDialog
import os.path
from datetime import datetime
from .airspace_geometry import *


class AirspaceGeometryBuilder:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        self.output_layer = None
        self.output_layer_name = ''
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'AirspaceGeometryBuilder_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&AirspaceGeometryBuilder')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

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
        return QCoreApplication.translate('AirspaceGeometryBuilder', message)


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
            be added to the toolbar. Defaults to True.
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
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/airspace_geometry_builder/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'AirspaceGeometryBuilder'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&AirspaceGeometryBuilder'),
                action)
            self.iface.removeToolBarIcon(action)

    @staticmethod
    def generate_output_layer_name():
        """ Generate layer name based on timestamp. """
        timestamp = datetime.now()
        return "AspGeometryBuilder_{}".format(timestamp.strftime("%Y_%m_%d_%H%M%f"))

    @staticmethod
    def create_output_layer(layer_name):
        """ Create memory layer for storing features created by plugin.
        param layer_name: str
        return: QgsVectorLayer
        """
        layer = QgsVectorLayer('Polygon?crs=epsg:4326', layer_name, 'memory')
        provider = layer.dataProvider()
        layer.startEditing()
        provider.addAttributes([QgsField("FEAT_NAME", QVariant.String, len=100)])
        layer.commitChanges()
        QgsProject.instance().addMapLayer(layer)
        return layer

    def output_layer_removed(self):
        """ Check if output layer has been removed from layers. """
        return not bool(QgsProject.instance().mapLayersByName(self.output_layer_name))

    def set_output_layer(self):
        if self.output_layer is None or self.output_layer_removed():
            layer_name = AirspaceGeometryBuilder.generate_output_layer_name()
            self.output_layer = AirspaceGeometryBuilder.create_output_layer(layer_name)
            self.output_layer_name = self.output_layer.name()  # Keep name in case output layer is removed from Layers
        self.iface.setActiveLayer(self.output_layer)

    def reset_circle_input_data(self):
        self.dlg.lineEditRefLongitude.clear()
        self.dlg.lineEditRefLatitude.clear()
        self.dlg.lineEditCircleRadius.clear()
        self.dlg.comboBoxCircleRadiusUOM.setCurrentIndex(0)

    def reset_circle_sector_input_data(self):
        self.dlg.lineEditCircleSectorBrngFrom.clear()
        self.dlg.lineEditCircleSectorBrngTo.clear()
        self.dlg.lineEditCircleSectorRadius.clear()
        self.dlg.lineEditCircleSectorRadiusUOM.setCurrentIndex(0)

    def reset_circle_ring_input_data(self):
        self.dlg.lineEditCircleRingInnerRadius.clear()
        self.dlg.lineEditCircleRingOuterRadius.clear()
        self.dlg.lineEditCircleRingRadiiUOM.setCurrentIndex(0)

    def reset_plugin_input_data(self):
        """ Remove user entries when plugin is opened and set drop down list to initial state. """
        self.dlg.lineEditAirspaceName.clear()
        self.dlg.comboBoxAspShapeMethod.setCurrentIndex(0)
        self.dlg.stackedWidgetShapeData.setCurrentIndex(0)
        self.dlg.stackedWidgetReferencePointBased.setCurrentIndex(0)
        self.reset_circle_input_data()
        self.dlg.checkBoxCircleCircleCenterOffset.setChecked(False)
        self.disable_circle_center_offset()
        self.reset_circle_sector_input_data()
        self.reset_circle_ring_input_data()

    def add_airspace(self, name, wkt):
        """
        :param name: str, airspace name
        :param wkt: str, airspace geometry WKT string
        """
        feat = QgsFeature()
        prov = self.output_layer.dataProvider()
        feat_geom = QgsGeometry.fromWkt(wkt)
        feat.setGeometry(feat_geom)
        feat.setAttributes([name])
        prov.addFeatures([feat])
        self.output_layer.commitChanges()
        self.output_layer.updateExtents()
        self.iface.mapCanvas().setExtent(self.output_layer.extent())
        self.iface.mapCanvas().refresh()

    # Circle - center, radius

    def get_circle_input_data(self):
        err_msg = ""
        asp_name = self.dlg.lineEditAirspaceName.text().strip()
        center_lon = Coordinate(self.dlg.lineEditRefLongitude.text().strip(), AT_LONGITUDE, "Circle center longitude")
        center_lat = Coordinate(self.dlg.lineEditRefLatitude.text().strip(), AT_LATITUDE, "Circle center latitude")
        radius = Distance(self.dlg.lineEditCircleRadius.text().strip(), self.dlg.comboBoxCircleRadiusUOM.currentText())

        if not asp_name:
            err_msg += "Airspace name is required!\n"
        if center_lon.err_msg:
            err_msg += center_lon.err_msg + '\n'
        if center_lat.err_msg:
            err_msg += center_lat.err_msg + '\n'
        if radius.err_msg:
            err_msg += radius.err_msg + '\n'

        if err_msg:
            QMessageBox.critical(QWidget(), "Message", "{}".format(err_msg))
        else:
            return asp_name, center_lon, center_lat, radius

    def create_circle(self):
        circle_input_data = self.get_circle_input_data()
        if circle_input_data:
            asp_name, center_lon, center_lat, radius = circle_input_data
            circle_wkt = AirspaceGeometry.circle_as_wkt(center_lon, center_lat, radius)
            self.add_airspace(asp_name, circle_wkt)

    # Circle - center offset

    def disable_circle_center_definition(self):
        self.dlg.lineEditRefLongitude.clear()
        self.dlg.lineEditRefLongitude.setEnabled(False)
        self.dlg.lineEditRefLatitude.clear()
        self.dlg.lineEditRefLatitude.setEnabled(False)

    def enable_circle_center_definition(self):
        self.dlg.lineEditRefLongitude.setEnabled(True)
        self.dlg.lineEditRefLatitude.setEnabled(True)

    def disable_circle_center_offset(self):
        """ Disable input controls to define circle center offset """
        self.dlg.labelCircleCenterOffsetLongitude.setEnabled(False)
        self.dlg.lineEditCircleCenterOffsetLongitude.clear()
        self.dlg.lineEditCircleCenterOffsetLongitude.setEnabled(False)
        self.dlg.labelCircleCenterOffsetLatitude.setEnabled(False)
        self.dlg.lineEditCircleCenterOffsetLatitude.clear()
        self.dlg.lineEditCircleCenterOffsetLatitude.setEnabled(False)
        self.dlg.labelCircleCenterOffsetTrueBearing.setEnabled(False)
        self.dlg.lineEditCircleCenterOffsetTrueBearing.clear()
        self.dlg.lineEditCircleCenterOffsetTrueBearing.setEnabled(False)
        self.dlg.labelCircleCenterOffsetDistance.setEnabled(False)
        self.dlg.lineEditCircleCenterOffsetDistance.clear()
        self.dlg.lineEditCircleCenterOffsetDistance.setEnabled(False)
        self.dlg.comboBoxCircleCenterOffsetDistanceUOM.setCurrentIndex(0)
        self.dlg.comboBoxCircleCenterOffsetDistanceUOM.setEnabled(False)

    def enable_circle_center_offset(self):
        """ Enable input controls to define circle center offset """
        self.dlg.labelCircleCenterOffsetLongitude.setEnabled(True)
        self.dlg.lineEditCircleCenterOffsetLongitude.setEnabled(True)
        self.dlg.labelCircleCenterOffsetLatitude.setEnabled(True)
        self.dlg.lineEditCircleCenterOffsetLatitude.setEnabled(True)
        self.dlg.labelCircleCenterOffsetTrueBearing.setEnabled(True)
        self.dlg.lineEditCircleCenterOffsetTrueBearing.setEnabled(True)
        self.dlg.labelCircleCenterOffsetDistance.setEnabled(True)
        self.dlg.lineEditCircleCenterOffsetDistance.setEnabled(True)
        self.dlg.comboBoxCircleCenterOffsetDistanceUOM.setEnabled(True)

    def get_circe_center_offset_data(self):
        err_msg = ""
        asp_name = self.dlg.lineEditAirspaceName.text().strip()
        radius = Distance(self.dlg.lineEditCircleRadius.text().strip(), self.dlg.comboBoxCircleRadiusUOM.currentText())
        ref_lon = Coordinate(self.dlg.lineEditCircleCenterOffsetLongitude.text().strip(), AT_LONGITUDE,
                             "Circle center reference longitude")
        ref_lat = Coordinate(self.dlg.lineEditCircleCenterOffsetLatitude.text().strip(), AT_LATITUDE,
                             "Circle center reference latitude")
        tbrng = self.dlg.lineEditCircleCenterOffsetTrueBearing.text().strip()
        offset_dist = Distance(self.dlg.lineEditCircleCenterOffsetDistance.text().strip(),
                               self.dlg.comboBoxCircleCenterOffsetDistanceUOM.currentText())

        if not asp_name:
            err_msg += "Airspace name is required!\n"
        if radius.err_msg:
            err_msg += radius.err_msg + '\n'
        if ref_lon.err_msg:
            err_msg += ref_lon.err_msg + '\n'
        if ref_lat.err_msg:
            err_msg += ref_lat.err_msg + '\n'

        if not tbrng:
            err_msg += "True bearing to circle center required!\n"
        else:
            try:
                tbrng = float(tbrng)
            except ValueError:
                err_msg += "True bearing value error!\n"
        if offset_dist.err_msg:
            err_msg += "Circle center offset distance error!"

        if err_msg:
            QMessageBox.critical(QWidget(), "Message", "{}".format(err_msg))
        else:
            return asp_name, radius, ref_lon, ref_lat, tbrng, offset_dist

    def create_circle_center_offset(self):
        circle_input_data = self.get_circe_center_offset_data()
        if circle_input_data:
            asp_name, radius, ref_lon, ref_lat, tbrng, offset_dist = circle_input_data

            offset_dist_m = offset_dist.convert_distance_to_uom(UOM_M)
            radius_m = radius.convert_distance_to_uom(UOM_M)

            center_lon, center_lat = vincenty_direct_solution(ref_lon.ang_dd,
                                                              ref_lat.ang_dd,
                                                              tbrng, offset_dist_m)

            center_lon_dms = Angle.convert_dd_to_dms(center_lon, AT_LONGITUDE)
            center_lat_dms = Angle.convert_dd_to_dms(center_lat, AT_LATITUDE)
            self.dlg.lineEditRefLongitude.setText(center_lon_dms)
            self.dlg.lineEditRefLatitude.setText(center_lat_dms)

            circle_vertices = AirspaceGeometry.get_circle_vertices(center_lon, center_lat, radius_m)
            circle_wkt = AirspaceGeometry.get_geometry_as_wkt(circle_vertices)
            self.add_airspace(asp_name, circle_wkt)

    def switch_circle_center_definition(self):
        if self.dlg.checkBoxCircleCircleCenterOffset.isChecked():
            self.disable_circle_center_definition()
            self.enable_circle_center_offset()
        else:
            self.enable_circle_center_definition()
            self.disable_circle_center_offset()

    # Circle sector
    def get_circle_sector_data(self):
        err_msg = ""
        asp_name = self.dlg.lineEditAirspaceName.text().strip()
        center_lon = Coordinate(self.dlg.lineEditRefLongitude.text().strip(), AT_LONGITUDE, "Circle center longitude")
        center_lat = Coordinate(self.dlg.lineEditRefLatitude.text().strip(), AT_LATITUDE, "Circle center latitude")
        tbrng_from = self.dlg.lineEditCircleSectorBrngFrom.text().strip()
        tbrng_to = self.dlg.lineEditCircleSectorBrngTo.text().strip()
        radius = Distance(self.dlg.lineEditCircleSectorRadius.text().strip(),
                          self.dlg.lineEditCircleSectorRadiusUOM.currentText())

        if not asp_name:
            err_msg += "Airspace name is required!\n"
        if center_lon.err_msg:
            err_msg += center_lon.err_msg + '\n'
        if center_lat.err_msg:
            err_msg += center_lat.err_msg + '\n'
        if not tbrng_from:
            err_msg += "True bearing from is required!\n"
        else:
            try:
                tbrng_from = float(tbrng_from)
            except ValueError:
                err_msg += "True bearing from value error!\n"

        if not tbrng_to:
            err_msg += "True bearing to is required!\n"
        else:
            try:
                tbrng_to = float(tbrng_to)
            except ValueError:
                err_msg += "True bearing to value error!\n"

        if radius.err_msg:
            err_msg += radius.err_msg + '\n'

        if err_msg:
            QMessageBox.critical(QWidget(), "Message", "{}".format(err_msg))
        else:
            return asp_name, center_lon, center_lat, tbrng_from, tbrng_to, radius

    def create_circle_sector(self):
        circle_sector_data = self.get_circle_sector_data()
        if circle_sector_data:
            asp_name, center_lon, center_lat, tbrng_from, tbrng_to, radius = circle_sector_data
            circle_sector_wkt = AirspaceGeometry.circle_sector_as_wkt(center_lon, center_lat, radius, tbrng_from, tbrng_to)
            self.add_airspace(asp_name, circle_sector_wkt)

    # Circle ring
    def get_circle_ring_data(self):
        err_msg = ""
        asp_name = self.dlg.lineEditAirspaceName.text().strip()
        center_lon = Coordinate(self.dlg.lineEditRefLongitude.text().strip(), AT_LONGITUDE, "Circle ring center longitude")
        center_lat = Coordinate(self.dlg.lineEditRefLatitude.text().strip(), AT_LATITUDE, "Circle ring center latitude")
        inner_radius = Distance(self.dlg.lineEditCircleRingInnerRadius.text().strip(),
                                self.dlg.lineEditCircleRingRadiiUOM.currentText())
        outer_radius = Distance(self.dlg.lineEditCircleRingOuterRadius.text().strip(),
                                self.dlg.lineEditCircleRingRadiiUOM.currentText())

        if not asp_name:
            err_msg += "Airspace name is required!\n"
        if center_lon.err_msg:
            err_msg += center_lon.err_msg + '\n'
        if center_lat.err_msg:
            err_msg += center_lat.err_msg + '\n'
        if inner_radius.err_msg:
            err_msg += inner_radius.err_msg + '\n'
        if outer_radius.err_msg:
            err_msg += outer_radius.err_msg + '\n'

        if err_msg:
            QMessageBox.critical(QWidget(), "Message", "{}".format(err_msg))
        else:
            return asp_name, center_lon, center_lat, inner_radius, outer_radius

    def create_circle_ring(self):
        circle_ring_data = self.get_circle_ring_data()
        if circle_ring_data:
            asp_name, center_lon, center_lat, inner_radius, outer_radius = circle_ring_data
            circle_ring_wkt = AirspaceGeometry.circle_ring_as_wkt(center_lon, center_lat, inner_radius, outer_radius)
            self.add_airspace(asp_name, circle_ring_wkt)

    def set_asp_shape_type(self):
        if self.dlg.comboBoxAspShapeMethod.currentIndex() == 0:  # Circle
            self.dlg.stackedWidgetShapeData.setCurrentIndex(0)
            self.dlg.stackedWidgetReferencePointBased.setCurrentIndex(0)
        elif self.dlg.comboBoxAspShapeMethod.currentIndex() == 1:  # Circle sector
            self.dlg.stackedWidgetShapeData.setCurrentIndex(0)
            self.dlg.stackedWidgetReferencePointBased.setCurrentIndex(1)
        elif self.dlg.comboBoxAspShapeMethod.currentIndex() == 2:  # Circle ring
            self.dlg.stackedWidgetShapeData.setCurrentIndex(0)
            self.dlg.stackedWidgetReferencePointBased.setCurrentIndex(2)

    def create_feature(self):
        self.set_output_layer()
        if self.dlg.comboBoxAspShapeMethod.currentIndex() == 0:  # Circle: center, radius
            if self.dlg.checkBoxCircleCircleCenterOffset.isChecked():
                self.create_circle_center_offset()
            else:
                self.create_circle()
        if self.dlg.comboBoxAspShapeMethod.currentIndex() == 1:  # Circle sector
            self.create_circle_sector()
        if self.dlg.comboBoxAspShapeMethod.currentIndex() == 2:  # Circle ring
            self.create_circle_ring()

    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = AirspaceGeometryBuilderDialog()
            self.dlg.comboBoxAspShapeMethod.currentIndexChanged.connect(self.set_asp_shape_type)
            self.dlg.checkBoxCircleCircleCenterOffset.stateChanged.connect(self.switch_circle_center_definition)
            self.dlg.pushButtonCreatePolygon.clicked.connect(self.create_feature)
            self.dlg.pushButtonCancel.clicked.connect(self.dlg.close)

        # show the dialog
        self.dlg.show()
        self.reset_plugin_input_data()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass
