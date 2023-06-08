# -----------------------------------------------------------------------------
# Copyright (c) 2021 Pepe Eulzer. All rights reserved.
# Distributed under the (new) BSD License.
# -----------------------------------------------------------------------------

from ctypes import alignment
import os
import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QCheckBox, QDialog, QLineEdit, QPushButton, QVBoxLayout, QWidget, 
                             QHBoxLayout, QSlider, QComboBox, QLabel, QFrame)
from PyQt5.QtGui import QLinearGradient, QBrush, QColor
import pyqtgraph as pg

from defaults import *  # default const variables

# Override pyqtgraph defaults
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
pg.setConfigOption('antialias', True)


class HorizontalLine(QFrame):
    """
    A horizontal line for use in Qt Layouts.
    """
    def __init__(self):
        super(HorizontalLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)

class SmartSlider(QWidget):
    """
    A wrapper around the slider widget, providing labels for name and value.
    Scales automatically in 100 discrete steps between minval and maxval.
    The number of value label decimals to be shown can be declared.
    """
    def __init__(self, tt, call_function, name="Slider ", minval=0, maxval=100, val=50, decimals=2, unit=""):
        super(SmartSlider, self).__init__()
        self.tt = tt
        self.call_function = call_function

        self.minval = minval
        self.scale = float(maxval - minval) / 100.0
        self.unit = unit
        self.suffix = "{:." + str(decimals) + "f}"

        # slider needs a value in [0, 100]
        slider_value = int(100 * (val - minval) / (maxval - minval))
        
        self.label_name = QLabel(name)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.setValue(slider_value)
        self.label_value = QLabel(self.suffix.format(val) + self.unit)
        
        l = QHBoxLayout()
        l.addWidget(self.label_name)
        l.addWidget(self.slider)
        l.addWidget(self.label_value)
        self.setLayout(l)

        self.slider.valueChanged[int].connect(self.__valueChanged)

    def __valueChanged(self, v):
        # this gets a value in slider coordinates [0,100] and scales to original range
        self.tt.logAction(self.tt.TYPE_GLYPH_SETTINGS)
        real_value = v * self.scale + self.minval
        self.label_value.setText(self.suffix.format(real_value) + self.unit)
        self.call_function(real_value)

class FolderSelector(QWidget):
    """
    A wrapper around the line edit widget with a label.
    """
    def __init__(self, call_function, dir, label_text="Folder "):
        super(FolderSelector, self).__init__()
        
        label = QLabel(label_text)
        self.lineEdit = QLineEdit(dir)
        self.lineEdit.editingFinished.connect(call_function)

        l = QHBoxLayout()
        l.setAlignment(Qt.AlignLeft)
        l.addWidget(label)
        l.addWidget(self.lineEdit)
        self.setLayout(l)

    def getText(self):
        return self.lineEdit.text()

class DatasetSelector(QWidget):
    """
    A wrapper around the combobox widget with a label.
    All subfolders of the target directory become entries (e.g., for dataset selection).
    """
    def __init__(self, call_function, target_dir, label_text="Dataset "):
        super(DatasetSelector, self).__init__()
        self.call_function = call_function
        
        label = QLabel(label_text)
        self.combobox = QComboBox()
        self.combobox.activated[str].connect(self.__activated)
        self.folderpaths = {}
        for f in os.scandir(target_dir):
            if f.is_dir():
                self.combobox.addItem(f.name)
                self.folderpaths[f.name] = f.path
        
        l = QHBoxLayout()
        l.setAlignment(Qt.AlignLeft)
        l.addWidget(label)
        l.addWidget(self.combobox)
        self.setLayout(l)

    def __activated(self, name):
        self.call_function(self.folderpaths[name])

    def reload(self, target_dir):
        while self.combobox.count() > 0:
            self.combobox.removeItem(0)

        self.folderpaths = {}
        for f in os.scandir(target_dir):
            if f.is_dir():
                self.combobox.addItem(f.name)
                self.folderpaths[f.name] = f.path


class TimeLoop():
    """
    Convenience class to loop a time variable within a defined interval.
    t -> the current time in seconds (float)
    t_index -> the index in [min_index, max_index] for animation data
    """
    def __init__(self, t_min:float, t_max:float, min_index:int, max_index:int):
        self.setupLoop(t_min, t_max, min_index, max_index)

    def setupLoop(self, t_min:float, t_max:float, min_index:int, max_index:int):
        # animation time bounds
        self.t_min = t_min
        self.t_max = t_max
        self.t_span = t_max - t_min
        self.min_index = min_index
        self.max_index = max_index
        self.index_span = self.max_index - self.min_index
        self.preview_active = False

        # "upper" time variables for a time range
        self.t = t_min
        self.t_index = min_index

        # "lower" time variables for a time range
        self.t_lower = t_min
        self.t_index_lower = min_index 

        # "preview" time variables
        self.t_preview = t_min
        self.t_index_preview = min_index

    def addTime(self, increment):
        # assumes increment < (t_max - t_min)
        t_new = self.t + increment
        delta = self.t - self.t_lower
        if t_new <= self.t_max:
            self.t = t_new
        else:
            self.t = self.t_min + increment
        self.t_lower = self.t - delta
        self.__updateIndex()

    def setTime(self, lower, upper):
        if upper > self.t_max:
            self.t = self.t_max
        elif upper < self.t_min:
            self.t = self.t_min
        else:
            self.t = upper

        if lower > upper:
            self.t_lower = upper
        elif lower < self.t_min:
            self.t_lower = self.t_min
        elif lower > self.t_max:
            self.t_lower = self.t_max
        else:
            self.t_lower = lower
        
        self.__updateIndex()

    def setTimePreview(self, tp):
        if tp >= self.t_max:
            self.t_preview = self.t_max
        elif tp < self.t_min:
            self.t_preview = self.t_min
        else:
            self.t_preview = tp
        self.t_index_preview = self.min_index + int((self.t_preview / self.t_span) * (self.index_span))

    def setTimePreviewActive(self, state):
        if state:
            self.preview_active = True
        else:
            self.preview_active = False
            self.t_preview = self.t
            self.t_index_preview = self.t_index

    def updateIndexRange(self, min_index:int, max_index:int):
        self.min_index = min_index
        self.max_index = max_index
        self.index_span = self.max_index - self.min_index
        self.__updateIndex()

    def __updateIndex(self):
        self.t_index = self.min_index + int((self.t / self.t_span) * self.index_span)
        self.t_index_lower = max(self.min_index, self.min_index + int((self.t_lower / self.t_span) * self.index_span))

        if not self.preview_active:
            self.t_preview = self.t
            self.t_index_preview = self.t_index

class TimeSlider(pg.PlotWidget):
    """
    A wrapper around the pyqtgtraph plot widget.
    This is essentially a timeslider with graphing capabilities.
    Allows to select a region of time.
    """
    def __init__(self, timeloop, colors, tt, min_s=0.0, max_s=1.0):
        super().__init__()
        self.tt = tt
        self.timeloop = timeloop
        self.animating = False
        self.mirrored_rois = set()
        self.mirrored_vlines = set()

        # view settings
        self.hideAxis('left')
        self.showGrid(x=True, y=False, alpha=0.3)
        self.setMouseEnabled(x=False, y=False)
        self.setAutoPan(x=False, y=False)
        padding = float(max_s - min_s) * 0.01
        self.setLimits(xMin=min_s-padding, xMax=max_s+padding, yMin=0.0, yMax=0.2)

        # create gradient from colormap
        stops = np.linspace(0, 1, colors.shape[0])
        gradient = QLinearGradient(min_s, 0, max_s, 0)
        for i in range(colors.shape[0]):
            gradient.setColorAt(stops[i], QColor(colors[i,0], colors[i,1], colors[i,2]))

        # live "hover" selector
        pen = pg.mkPen(color=(100, 100, 100, 255), width=1.5)
        self.vLine = pg.InfiniteLine(angle=90, pen=pen, bounds=[min_s, max_s])

        # selector
        pen = pg.mkPen(color=(100, 100, 100, 255), width=1.5)
        hoverPen = pg.mkPen(color=(100, 100, 100, 255), width=2.5)
        brush = QBrush(gradient)
        self.time_selector = pg.LinearRegionItem((min_s, max_s*0.1), brush=brush, hoverBrush=brush,
                                                 pen=pen, hoverPen=hoverPen, bounds=[min_s, max_s])
        self.time_selector.sigRegionChanged.connect(self.__regionChanged)

        # current time text
        self.text_time0 = pg.TextItem("0.00 s",
                                      anchor=(1.1,-0.5),
                                      color=(160, 160, 160, 255),
                                      border=(160, 160, 160, 255),
                                      fill=(250, 250, 250, 255))
        self.text_time0.setPos(0.0, 0.206)

        self.text_time1 = pg.TextItem(('%0.2f s' %(max_s*0.1)),
                                      anchor=(-0.1,-0.5),
                                      color=(160, 160, 160, 255),
                                      border=(160, 160, 160, 255),
                                      fill=(240, 240, 240, 255))
        self.text_time1.setPos(max_s*0.1, 0.206)

        # dummy graph to set bounds
        self.plot([min_s,max_s], [0.0,0.2], pen=(0,0,0,0))

        # add items to plot
        self.addItem(self.time_selector)
        self.addItem(self.text_time1)
    
    def mouseMoved(self, evt):
        value = self.getPlotItem().vb.mapSceneToView(evt)
        self.vLine.setValue(value.x())
        self.text_time0.setPos(value.x(), 0.206)
        self.text_time0.setText('%0.2f s' %value.x())
        self.timeloop.setTimePreview(value.x())
        for l in self.mirrored_vlines:
            l.setPos(value.x())

    def setPreviewOn(self):
        self.tt.logAction(self.tt.TYPE_TEMP_PREVIEW)
        t = self.timeloop.t_preview
        self.vLine.setValue(t)
        self.text_time0.setPos(t, 0.206)
        self.text_time0.setText('%0.2f s' %t)
        self.addItem(self.vLine, ignoreBounds=True)
        self.removeItem(self.text_time1)
        self.addItem(self.text_time0)
        self.scene().sigMouseMoved.connect(self.mouseMoved)

    def setPreviewOff(self):
        self.removeItem(self.vLine)
        self.removeItem(self.text_time0)
        self.addItem(self.text_time1)
        self.scene().sigMouseMoved.disconnect(self.mouseMoved)

    def prepareAnimation(self):
        self.animating = True
        self.time_selector.setMovable(False)
        lower, upper = self.time_selector.getRegion()
        return lower, upper

    def animationEnded(self):
        self.animating = False
        self.time_selector.setMovable(True)

    def __regionChanged(self):
        self.tt.logAction(self.tt.TYPE_TEMP_FILTER)
        lower, upper = self.time_selector.getRegion()
        self.text_time1.setPos(upper, 0.206)
        self.text_time1.setText('%0.2f s' %upper)
        for roi in self.mirrored_rois:
            roi.setRegion((lower, upper))
        if not self.animating:
            self.timeloop.setTime(lower, upper)

    def registerMirroredROI(self, roi):
        self.mirrored_rois.add(roi)

    def registerMirroredvLine(self, line):
        self.mirrored_vlines.add(line)

    def resetRegion(self, colors, min_s, max_s):
        padding = float(max_s - min_s) * 0.01
        self.setLimits(xMin=min_s-padding, xMax=max_s+padding, yMin=0.0, yMax=0.2)
        stops = np.linspace(0, 1, colors.shape[0])
        gradient = QLinearGradient(min_s, 0, max_s, 0)
        for i in range(colors.shape[0]):
            gradient.setColorAt(stops[i], QColor(colors[i,0], colors[i,1], colors[i,2]))
        self.time_selector.setBrush(QBrush(gradient))
        self.time_selector.setBounds([min_s, max_s])
        self.plot([min_s,max_s], [0.0,0.2], pen=(0,0,0,0))


class Scatter2D(pg.PlotWidget):
    """
    A wrapper around the pyqtgtraph plot widget.
    Scatterplot of 2 values, e.g., length and angle.
    Can dynamically turn sets on/off.
    """
    def __init__(self):
        super().__init__()
        self.items = []
        self.items_t = []
        self.items_preview = []

        self.setLabel('left', "Translation Vel. (m/s)", **LABEL_STYLE)
        self.setLabel('bottom', "Rotation Vel. (rad/s)", **LABEL_STYLE)
        self.showGrid(x=True, y=True, alpha=0.2)

        self.roi = pg.RectROI([0,-6e-5],[0.015,12e-5],
                              invertible=True,
                              rotatable=False,
                              sideScalers=True,
                              pen=pg.mkPen(color=(0,0,0,120),width=1.5),
                              hoverPen=pg.mkPen(color=(0,0,0,150), width=2),
                              handlePen=pg.mkPen(color=(0,0,0,120), width=1),
                              handleHoverPen=pg.mkPen(color=(0,0,0,150), width=2))
        self.roi.addScaleHandle([0.5, 0], [0.5, 1])
        self.roi.addScaleHandle([0, 0.5], [1, 0.5])
        self.roi.addScaleHandle([0, 0], [1, 1])
        self.roi.addScaleHandle([0, 1], [1, 0])
        self.roi.addScaleHandle([1, 0], [0, 1])
        self.addItem(self.roi)


    def addPlotItem(self, x, y, color):
        s = pg.ScatterPlotItem(x=x, y=y, pen=None, size=SCATTER_POINT_SIZE, brush=color)
        st = pg.ScatterPlotItem(x=[0], y=[0], pen=None, size=SCATTER_POINT_SIZE*1.5, brush=color.darker(200))
        s_preview = pg.ScatterPlotItem(x=[0], y=[0], pen=color, size=SCATTER_POINT_SIZE*4, brush=color.lighter(200), symbol='+')
        self.items.append(s)
        self.items_t.append(st)
        self.items_preview.append(s_preview)
        self.addItem(s)

        # set time markers on top
        for time_marker in self.items_t:
            self.removeItem(time_marker)
            self.addItem(time_marker)

        # set preview markers on top
        for preview_marker in self.items_preview:
            self.removeItem(preview_marker)
            self.addItem(preview_marker)

        self.resetROI()

        return s, st, s_preview

    def resetROI(self):
        x = np.array([item.data['x'] for item in self.items])
        y = np.array([item.data['y'] for item in self.items])
        x = x.ravel()
        y = y.ravel()
        size_x = np.max(x)-np.min(x)
        size_y = np.max(y)-np.min(y)
        self.enableAutoRange('xy', True)
        self.roi.setPos(np.min(x) - 0.1 * size_x, np.min(y) - 0.1 * size_y)
        self.roi.setSize((size_x * 1.2, size_y * 1.2))
        self.enableAutoRange('xy', False)

    def removePlotItems(self, s, st, s_preview):
        self.removeItem(s)
        self.removeItem(st)
        self.removeItem(s_preview)
        self.items.remove(s)
        self.items_t.remove(st)
        self.items_preview.remove(s_preview)

    def showROI(self, show):
        if show:
            self.addItem(self.roi)
        else:
            self.removeItem(self.roi)


class ExportDialog(QDialog):
    """
    A dialog window for exporting FHA sets.
    """
    def __init__(self, timeloop):
        super().__init__()
        self.setWindowTitle("Export FHA sets")
        self.setMinimumWidth(500)
        
        self.timeloop = timeloop
        self.active_glyphs = []
        self.phi_min = -10000.0
        self.phi_max = 10000.0
        self.l_min = -10000.0
        self.l_max = 10000.0

        save_folder = os.path.join(os.path.dirname(sys.argv[0]), "FHA_export")
        self.line_edit_file = QLineEdit(save_folder)

        button_export = QPushButton("Export")
        button_export.clicked.connect(self.export_pressed)
        button_cancel = QPushButton("Cancel")
        button_cancel.clicked.connect(self.reject)
        self.cb_filter_time = QCheckBox()
        self.cb_filter_time.setText("Apply time window")
        self.cb_filter_time.setToolTip("If checked, will only export the selected time range.")
        self.cb_filter_ROI = QCheckBox()
        self.cb_filter_ROI.setText("Apply ROI")
        self.cb_filter_ROI.setToolTip("If checked, will only export the selected ROI range.")

        layout_top = QVBoxLayout()
        layout_top.addWidget(QLabel("Save location:"))
        layout_top.addWidget(self.line_edit_file)
        layout_top.addWidget(self.cb_filter_time)
        layout_top.addWidget(self.cb_filter_ROI)
        layout_buttons = QHBoxLayout()
        layout_buttons.addStretch(1)
        layout_buttons.addWidget(button_export)
        layout_buttons.addWidget(button_cancel)
        layout_top.addStretch(1)
        layout_top.addWidget(QLabel("All visible FHA sets will be exported."))
        layout_top.addLayout(layout_buttons)
        self.setLayout(layout_top)

    def setROIFilterEnabled(self, enabled):
        if enabled:
            self.cb_filter_ROI.setEnabled(True)
        else:
            self.cb_filter_ROI.setChecked(False)
            self.cb_filter_ROI.setEnabled(False)

    def setROIrange(self, phi_min, phi_max, l_min, l_max):
        self.phi_min = phi_min
        self.phi_max = phi_max
        self.l_min = l_min
        self.l_max = l_max

    def export_pressed(self):
        if len(self.active_glyphs) == 0:
            print("No glyphs visible.")
            self.reject()
        
        # create the folder if it does not exist
        save_path = self.line_edit_file.text()
        if not os.path.exists(save_path):
            os.makedirs(save_path)

        for g in self.active_glyphs:
            data_n = g.instance_parameters['n']
            data_r0 = g.instance_parameters['r0']
            data_l = g.instance_parameters['l']
            data_phi = g.instance_parameters['phi']

            if self.cb_filter_time.isChecked():
                min_i = self.timeloop.t_index_lower
                max_i = self.timeloop.t_index
                data_n = data_n[min_i:max_i]
                data_r0 = data_r0[min_i:max_i]
                data_l = data_l[min_i:max_i]
                data_phi = data_phi[min_i:max_i]
            
            if self.cb_filter_ROI.isChecked():
                mask = np.logical_and(data_phi >= self.phi_min,
                       np.logical_and(data_phi <= self.phi_max,
                       np.logical_and(data_l >= self.l_min,
                                      data_l <= self.l_max)))
                data_n = data_n[mask]
                data_r0 = data_r0[mask]
                data_l = data_l[mask]
                data_phi = data_phi[mask]

            name = g.name[4:].replace(" ", "_")
            np.savetxt(os.path.join(save_path, name + "_n.txt"), data_n)
            np.savetxt(os.path.join(save_path, name + "_r0.txt"), data_r0)
            np.savetxt(os.path.join(save_path, name + "_l.txt"), data_l)
            np.savetxt(os.path.join(save_path, name + "_phi.txt"), data_phi)

        self.done(1)

