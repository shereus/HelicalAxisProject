# -----------------------------------------------------------------------------
# Copyright (c) 2021 Pepe Eulzer. All rights reserved.
# Distributed under the (new) BSD License.
# -----------------------------------------------------------------------------

import sys
from glob import glob
from time import perf_counter
from datetime import datetime


import OpenGL.GL as gl
from OpenGL.GL import shaders
from PyQt5.QtCore import Qt, QPoint, QRectF, QTimer
from PyQt5.QtGui import (QIcon, QOpenGLWindow, QSurfaceFormat, QPalette, QColor, QPainter, QFont)
from PyQt5.QtWidgets import (QApplication, QComboBox, QMainWindow, QWidget, QDockWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QCheckBox, QPushButton)
from numpy import exp
import pyqtgraph as pg

import helperQt    # wrapper around qt widgets etc
import helperGL    # convenience functions for OpenGL
import geometry    # scene objects (geometry, glyphs...)
import camera      # camera classes for view/projection matrices
import conversions # convert markers, compute FHAs
from defaults import *  # default const variables

class TimeTracker():
    def __init__(self):
        self.timetable = [["Timestamp", "Action Type"]]
        self.time_action = perf_counter()
        self.time_total = 0.0

        # action types
        self.TYPE_SPATIAL = "Spatial interaction"
        self.TYPE_TEMP_FILTER = "Temporal filtering"
        self.TYPE_TEMP_PREVIEW = "Temporal preview"
        self.TYPE_ANIMATION = "Animation control"
        self.TYPE_ATT_FILTER = "Attribute filtering"
        self.TYPE_GLYPH_SETTINGS = "Glyph settings"
        self.TYPE_ABS_TRANS = "|Translation| toggle"
        self.TYPE_ADD_AXIS_WORLD = "World axis added"
        self.TYPE_ADD_AXIS_BASE = "Base axis added"
        self.TYPE_RM_AXIS = "Axis set removed"
        self.TYPE_DATASET_CHANGE = "Changed dataset: "
        self.TYPE_FOLDER_CHANGE = "Changed folder: "

        self.active_action = None

    def logAction(self, action_type, comment=""):
        if self.active_action != action_type:
            self.active_action = action_type
            self.time_action = perf_counter() - self.time_action
            self.time_total += self.time_action
            self.timetable.append([self.time_total, action_type + comment])
            self.time_action = perf_counter()

    def resetTimer(self):
        self.time_action = perf_counter()
        self.time_total = 0.0

    def writeLog(self):
        if not WRITE_LOG:
            return
        now = datetime.now()
        filename = now.strftime("LOG_%Y-%m-%d_%H-%M-%S.csv")
        with open(filename, 'w') as f:
            for line in self.timetable:
                f.write(f"{line[0]},{line[1]}\n")


class GLWindow(QOpenGLWindow):
    """
    Window that holds an OpenGL context.
    Find documentation on the QOpenGLWindow class at https://doc.qt.io/qt-5/qopenglwindow.html
    """
    def __init__(self, tt, timeloop, scatter_phi_l, motion_path, add_checkbox_func, parent=None):
        super(GLWindow, self).__init__(updateBehavior=QOpenGLWindow.NoPartialUpdate, parent=parent)
        self.tt = tt
        self.timeloop = timeloop
        self.scatter_phi_l = scatter_phi_l
        self.motion_path = motion_path
        self.add_checkbox_func = add_checkbox_func
        self.HA_compute_method = "no method set"
        self.selection_tooltips = []
        self.HA_tooltip = "no tooltip set"
        self.active_colors = [False] * len(CORR_COLORS_NORM)
        self.tooltip_font = QFont("Helvetica", 18)
        self.tooltip_rectangle = QRectF(0, self.height() / 1.3, self.width(), 80)
        self.tooltip_color = QColor(200, 200, 200)

    def initializeGL(self):
        """
        Perform OpenGL resource initialization here.
        """
        # FPS counter
        #self.fps_time = perf_counter()
        #self.time_counter = 0

        # compile all shaders
        # ----------------------------------------
        vert_vertebra = shaders.compileShader(helperGL.read_shader(resource_path("shaders/vertebra.vert")), gl.GL_VERTEX_SHADER)
        frag_vertebra = shaders.compileShader(helperGL.read_shader(resource_path("shaders/vertebra.frag")), gl.GL_FRAGMENT_SHADER)
        self.shader_vertebra = shaders.compileProgram(vert_vertebra, frag_vertebra)

        vert_hinted = shaders.compileShader(helperGL.read_shader(resource_path("shaders/hinted.vert")), gl.GL_VERTEX_SHADER)
        frag_hinted = shaders.compileShader(helperGL.read_shader(resource_path("shaders/hinted.frag")), gl.GL_FRAGMENT_SHADER)
        self.shader_hinted = shaders.compileProgram(vert_hinted, frag_hinted)

        vert_glyph = shaders.compileShader(helperGL.read_shader(resource_path("shaders/glyph.vert")), gl.GL_VERTEX_SHADER)
        frag_glyph = shaders.compileShader(helperGL.read_shader(resource_path("shaders/glyph.frag")), gl.GL_FRAGMENT_SHADER)
        self.shader_glyph = shaders.compileProgram(vert_glyph, frag_glyph)
        
        vert_surface = shaders.compileShader(helperGL.read_shader(resource_path("shaders/surface.vert")), gl.GL_VERTEX_SHADER)
        frag_surface = shaders.compileShader(helperGL.read_shader(resource_path("shaders/surface.frag")), gl.GL_FRAGMENT_SHADER)
        self.shader_surface = shaders.compileProgram(vert_surface, frag_surface)

        # retrieve uniform locations
        # ----------------------------------------
        self.uniform_locations_vertebra = {
            'VP': gl.glGetUniformLocation(self.shader_vertebra, 'VP'),
            'M': gl.glGetUniformLocation(self.shader_vertebra, 'M'),
            'cameraPos' : gl.glGetUniformLocation(self.shader_vertebra, 'cameraPos'),
            'color' : gl.glGetUniformLocation(self.shader_vertebra, 'color'),
            'ambient' : gl.glGetUniformLocation(self.shader_vertebra, 'ambient'),
            'render_flat' : gl.glGetUniformLocation(self.shader_vertebra, 'render_flat'),
            'outline_color' : gl.glGetUniformLocation(self.shader_vertebra, 'outline_color')
        }

        self.uniform_locations_hinted = {
            'VP': gl.glGetUniformLocation(self.shader_hinted, 'VP'),
            'M': gl.glGetUniformLocation(self.shader_hinted, 'M'),
            'cameraPos' : gl.glGetUniformLocation(self.shader_hinted, 'cameraPos')
        }

        self.uniform_locations_glyph = {
            'VP':    gl.glGetUniformLocation(self.shader_glyph, 'VP'),
            'scale': gl.glGetUniformLocation(self.shader_glyph, 'scale'),
            'thickness': gl.glGetUniformLocation(self.shader_glyph, 'thickness'),
            'len':   gl.glGetUniformLocation(self.shader_glyph, 'len'),
            'offset':   gl.glGetUniformLocation(self.shader_glyph, 'offset'),
            'tipColor' : gl.glGetUniformLocation(self.shader_glyph, 'tipColor'),
            'type' : gl.glGetUniformLocation(self.shader_glyph, 'type'),
            'cameraPos' : gl.glGetUniformLocation(self.shader_glyph, 'cameraPos'),
            'phiLBounds' : gl.glGetUniformLocation(self.shader_glyph, 'phiLBounds'),
            'l_abs' : gl.glGetUniformLocation(self.shader_glyph, 'l_abs'),
            'r0_loc' : gl.glGetUniformLocation(self.shader_glyph, 'r0_loc')
        }

        self.uniform_locations_surface = {
            'VP': gl.glGetUniformLocation(self.shader_surface, 'VP'),
            'len':   gl.glGetUniformLocation(self.shader_surface, 'len'),
            'offset':   gl.glGetUniformLocation(self.shader_surface, 'offset'),
            'cameraPos' : gl.glGetUniformLocation(self.shader_surface, 'cameraPos'),
            'opacity' : gl.glGetUniformLocation(self.shader_surface, 'opacity'),
            'phiLBounds' : gl.glGetUniformLocation(self.shader_surface, 'phiLBounds'),
            'l_abs' : gl.glGetUniformLocation(self.shader_surface, 'l_abs'),
            'r0_loc' : gl.glGetUniformLocation(self.shader_surface, 'r0_loc')
        }

        # initialize the scene objects
        self.initScene()

    def initScene(self, scene_path=INITIAL_FOLDER):
        # initial uniforms
        gl.glUseProgram(self.shader_vertebra)
        gl.glUniform3fv(self.uniform_locations_vertebra['color'], 1, REFERENCE_COLOR)
        gl.glUseProgram(self.shader_glyph)
        gl.glUniform1f(self.uniform_locations_glyph['scale'], settings['glyphs_scale'])
        gl.glUniform1f(self.uniform_locations_glyph['thickness'], INITIAL_THICKNESS)
        gl.glUniform1f(self.uniform_locations_glyph['len'], INITIAL_LENGTH)
        gl.glUniform1f(self.uniform_locations_glyph['offset'], INITIAL_OFFSET)
        gl.glUseProgram(self.shader_surface)
        gl.glUniform1f(self.uniform_locations_surface['len'], INITIAL_LENGTH)
        gl.glUniform1f(self.uniform_locations_surface['offset'], INITIAL_OFFSET)

        # initialize reference models (vertebrae)
        # ----------------------------------------
        self.vertebrae = []              # all vertebrae (consistent)
        self.vertebrae_on = []           # rendered opaque
        self.vertebrae_off = []          # rendered hinted
        self.vertebra_highlighted = None # hover-selected geometry
        self.vertebra_selected = None    # click-selected geometry (reference)
        vertebrae_animation_steps = []

        # load filenames
        model_names = sorted(glob(scene_path + "/*.obj"))
        pos_names   = sorted(glob(self.motion_path + "/*pos.txt"))
        rot_names   = sorted(glob(self.motion_path + "/*rot.txt"))
        
        # check if R,v exist per object
        if not (len(model_names) == len(pos_names) == len(rot_names)):
            # see if marker files exist, convert them
            marker_names = sorted(glob(self.motion_path + "/*marker.txt"))
            for name in marker_names:
                conversions.markerToRv(name)
            # try laoding again
            pos_names = sorted(glob(self.motion_path + "/*pos.txt"))
            rot_names = sorted(glob(self.motion_path + "/*rot.txt"))

        assert(len(model_names) == len(pos_names) == len(rot_names))

        # create one model per file
        for i in range(len(model_names)):
            # load one vertebra model
            v = geometry.referenceGeometry(model_names[i], pos_names[i], rot_names[i], i, scale=settings['models_scale'])
            self.vertebrae.append(v)
            vertebrae_animation_steps.append(len(v.model_matrices))
#
#         # update the index range based on the number of instances found in animation data
        assert(len(set(vertebrae_animation_steps)) == 1)
        self.timeloop.updateIndexRange(0, vertebrae_animation_steps[0] - 1)

        # initialize glyph sequences
        # ----------------------------------------
        self.glyphs = []          # all glyph sequences
        self.glyphs_visible = []  # visible glyph sequences

        # initialize the camera and other state variables
        # ----------------------------------------
        self.updateRenderLists()
        self.camera = camera.TrackballCamera(self.width(), self.height())
        self.last_mouse_pos = QPoint()
        self.mouse_left_pressed = False
        self.mouse_mid_pressed  = False

        # 0: selection inactive
        # 1: selection active, nothing selected
        # 2: selection active, reference object selected
        # 3: selection active, reference and target object selected (computing)
        self.selection_mode = 0

    def resizeGL(self, w, h):
        """
        Set up transformation matrices and other window size dependent resources here.
        Avoid issuing OpenGL commands from this function as there may not be a context current when it is invoked.
        """
        self.camera.setProjection(w, h)
        self.tooltip_rectangle = QRectF(0, h / 1.3, w, 80)

    def paintGL(self):
        """
        Issue OpenGL draw commands or use QPainter here.
        """
        # FPS counter
        # frame_diff = perf_counter() - self.fps_time
        # self.time_counter += frame_diff
        # if self.time_counter >= 1.0:
        #     self.time_counter = 0.0
        #     print(str(1.0 / (frame_diff)) + " fps")
        # self.fps_time = perf_counter()

        # setup OpenGL state (modified by QPainter)
        gl.glClearColor(1.0, 1.0, 1.0, 1.0)
        gl.glClearStencil(255)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glStencilOp(gl.GL_KEEP, gl.GL_KEEP, gl.GL_REPLACE)

        # clear the scene
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT | gl.GL_STENCIL_BUFFER_BIT)

        # re-calculate global parameters
        VP = self.camera.getProjection() * self.camera.getView()
        t_index = self.timeloop.t_index
        t_index_lower = self.timeloop.t_index_lower
        t_index_preview = self.timeloop.t_index_preview
        t_index_preview_gap = max(0, t_index_preview-1)

        # vertebra shader
        # ----------------------------------------
        gl.glUseProgram(self.shader_vertebra)
        gl.glUniformMatrix4fv(self.uniform_locations_vertebra['VP'], 1, gl.GL_FALSE, VP.data())
        gl.glUniform3fv(self.uniform_locations_vertebra['cameraPos'], 1, self.camera.getPosition())

        if self.selection_mode != 0:
            # selection active
            # ----------------------------------------
            gl.glEnable(gl.GL_STENCIL_TEST)
                
            for vertebra in self.vertebrae:
                gl.glBindVertexArray(vertebra.VAO)
                M = vertebra.model_matrices[t_index_preview]
                gl.glUniformMatrix4fv(self.uniform_locations_vertebra['M'], 1, gl.GL_FALSE, M.data())

                # set color if this is a selected object
                if vertebra == self.vertebra_selected:
                    gl.glUniform3fv(self.uniform_locations_vertebra['color'], 1, SELECT_COLOR)
                    gl.glUniform1f(self.uniform_locations_vertebra['ambient'], 0.6)
                elif vertebra == self.vertebra_highlighted:
                    gl.glUniform3fv(self.uniform_locations_vertebra['color'], 1, SELECT_COLOR)

                # draw the object, write id to stencil
                gl.glStencilFunc(gl.GL_ALWAYS, vertebra.stencil_id, 0xFF)
                gl.glUniform1f(self.uniform_locations_vertebra['render_flat'], 0.0)
                gl.glDrawElements(gl.GL_TRIANGLES, vertebra.EBO_size, gl.GL_UNSIGNED_INT, None)
                
                # draw flat instances for the color outlines (inside to outside)
                gl.glStencilFunc(gl.GL_NOTEQUAL, vertebra.stencil_id, 0xFF)
                for i in range(len(vertebra.outline_colors)):
                    gl.glUniform1f(self.uniform_locations_vertebra['render_flat'], (i+1) * settings['outline_width'])
                    gl.glUniform3fv(self.uniform_locations_vertebra['outline_color'], 1, vertebra.outline_colors[i])
                    gl.glDrawElements(gl.GL_TRIANGLES, vertebra.EBO_size, gl.GL_UNSIGNED_INT, None)
                
                # reset color
                gl.glUniform3fv(self.uniform_locations_vertebra['color'], 1, REFERENCE_COLOR)
                gl.glUniform1f(self.uniform_locations_vertebra['ambient'], 0.1)
            
            gl.glDisable(gl.GL_STENCIL_TEST)

        else:
            # selection inactive
            # ----------------------------------------
            gl.glEnable(gl.GL_STENCIL_TEST)
            for vertebra in self.vertebrae_on:
                # activate the VAO of this object
                gl.glBindVertexArray(vertebra.VAO)

                # update per-object uniforms
                M = vertebra.model_matrices[t_index_preview]
                gl.glUniformMatrix4fv(self.uniform_locations_vertebra['M'], 1, gl.GL_FALSE, M.data())

                # draw the object, write id to stencil
                gl.glStencilFunc(gl.GL_ALWAYS, vertebra.stencil_id, 0xFF)
                gl.glUniform1f(self.uniform_locations_vertebra['render_flat'], 0.0)
                gl.glDrawElements(gl.GL_TRIANGLES, vertebra.EBO_size, gl.GL_UNSIGNED_INT, None)
                
                # draw a flat enlarged instance for the color outline
                gl.glStencilFunc(gl.GL_NOTEQUAL, vertebra.stencil_id, 0xFF)
                for i in range(len(vertebra.outline_colors)):
                    gl.glUniform1f(self.uniform_locations_vertebra['render_flat'], (i+1) * settings['outline_width'])
                    gl.glUniform3fv(self.uniform_locations_vertebra['outline_color'], 1, vertebra.outline_colors[i])
                    gl.glDrawElements(gl.GL_TRIANGLES, vertebra.EBO_size, gl.GL_UNSIGNED_INT, None)
            gl.glDisable(gl.GL_STENCIL_TEST)

            # vertebra hinted shader
            # ----------------------------------------
            gl.glUseProgram(self.shader_hinted)

            # update general uniforms
            gl.glUniformMatrix4fv(self.uniform_locations_hinted['VP'], 1, gl.GL_FALSE, VP.data())
            gl.glUniform3fv(self.uniform_locations_hinted['cameraPos'], 1, self.camera.getPosition())

            # draw vertebrae
            for vertebra in self.vertebrae_off:
                # update per-object uniforms
                M = vertebra.model_matrices[t_index_preview]
                gl.glUniformMatrix4fv(self.uniform_locations_hinted['M'], 1, gl.GL_FALSE, M.data())

                # draw
                gl.glStencilFunc(gl.GL_ALWAYS, vertebra.stencil_id, -1)
                gl.glBindVertexArray(vertebra.VAO)
                gl.glDrawElements(gl.GL_TRIANGLES, vertebra.EBO_size, gl.GL_UNSIGNED_INT, None)


        # glyph shader
        # ----------------------------------------
        gl.glUseProgram(self.shader_glyph)

        # update general uniforms
        gl.glUniformMatrix4fv(self.uniform_locations_glyph['VP'], 1, gl.GL_FALSE, VP.data())
        gl.glUniform3fv(self.uniform_locations_glyph['cameraPos'], 1, self.camera.getPosition())

        # draw glyphs
        nr = t_index - t_index_lower
        for glyph in self.glyphs_visible:
            # draw the shaft
            gl.glUniform1i(self.uniform_locations_glyph['type'], 0)
            gl.glBindVertexArray(glyph.VAO_shaft)
            gl.glDrawElementsInstancedBaseInstance(gl.GL_TRIANGLES, glyph.EBO_shaft_size, gl.GL_UNSIGNED_INT, None, nr, t_index_lower)

            # draw the tip
            gl.glUniform1i(self.uniform_locations_glyph['type'], 1)
            gl.glUniform3fv(self.uniform_locations_glyph['tipColor'], 1, glyph.corr_color)
            gl.glBindVertexArray(glyph.VAO_tip)
            gl.glDrawElementsInstancedBaseInstance(gl.GL_TRIANGLES, glyph.EBO_tip_size, gl.GL_UNSIGNED_INT, None, nr, t_index_lower)

            # draw the tip (preview)
            gl.glUniform1i(self.uniform_locations_glyph['type'], 3)
            gl.glDrawElementsInstancedBaseInstance(gl.GL_TRIANGLES, glyph.EBO_tip_size, gl.GL_UNSIGNED_INT, None, 1, t_index_preview_gap)

            # draw the shaft (preview)
            gl.glBindVertexArray(glyph.VAO_shaft)
            gl.glUniform1i(self.uniform_locations_glyph['type'], 2)
            gl.glDrawElementsInstancedBaseInstance(gl.GL_TRIANGLES, glyph.EBO_shaft_size, gl.GL_UNSIGNED_INT, None, 1, t_index_preview_gap)
            
            # update the connected scatterplot
            phi = glyph.instance_parameters['phi'][t_index_lower:t_index]
            l = glyph.instance_parameters_l[t_index_lower:t_index]
            glyph.scatterplot_l_phi_time.setData(phi, l)
            
            phi_p = [glyph.instance_parameters['phi'][t_index_preview_gap]]
            l_p = [glyph.instance_parameters_l[t_index_preview_gap]]
            glyph.scatterplot_l_phi_preview.setData(phi_p, l_p)

        # surface shader
        # ----------------------------------------
        gl.glUseProgram(self.shader_surface)

        # update general uniforms
        gl.glUniformMatrix4fv(self.uniform_locations_surface['VP'], 1, gl.GL_FALSE, VP.data())
        gl.glUniform3fv(self.uniform_locations_surface['cameraPos'], 1, self.camera.getPosition())

        # draw surfaces
        for glyph in self.glyphs_visible:
            gl.glBindVertexArray(glyph.VAO_surface)
            start = t_index_lower * 2
            nr = (t_index - t_index_lower) * 2
            gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, start, nr) # draw selected time interval
            #gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, glyph.nr_points) # draw all

        # calls to QPainter that overwrite the framebuffer
        # ----------------------------------------
        # draw the selection tooltip if selection is active
        if self.selection_mode != 0:
            qp = QPainter(self)
            qp.fillRect(self.tooltip_rectangle,  self.tooltip_color)
            qp.setFont(self.tooltip_font)
            qp.drawText(self.tooltip_rectangle, Qt.AlignCenter, self.HA_tooltip)

        # schedule update for continuous drawing
        self.update() 

    def wheelEvent(self, event):
        self.tt.logAction(self.tt.TYPE_SPATIAL)
        factor = event.angleDelta().y() * 0.001
        self.camera.zoom(factor)
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.last_mouse_pos = event.localPos()
            self.mouse_left_pressed = True

            # test if a reference object can be selected
            if self.selection_mode == 1:
                x = event.localPos().x()
                y = event.localPos().y()
                index = gl.glReadPixels(x, self.height() - y - 1, 1, 1, gl.GL_STENCIL_INDEX, gl.GL_UNSIGNED_INT)[0][0]
                if index != 255:
                    # if a FHAworld is computed only one object needs to be selected
                    if self.HA_compute_method == "FHAworld":
                        self.addHA(None, self.vertebrae[index], self.HA_compute_method)
                        self.__resetSelectionMode()
                    else:
                        self.HA_tooltip = self.selection_tooltips[1] # get second tooltip
                        self.vertebra_selected = self.vertebrae[index]
                        self.selection_mode = 2

            # test if a target object can be selected
            elif self.selection_mode == 2:
                x = event.localPos().x()
                y = event.localPos().y()
                index = gl.glReadPixels(x, self.height() - y - 1, 1, 1, gl.GL_STENCIL_INDEX, gl.GL_UNSIGNED_INT)[0][0]
                if index != 255:
                    vertebra_target = self.vertebrae[index]
                    self.addHA(self.vertebra_selected, vertebra_target, self.HA_compute_method)

                    self.__resetSelectionMode()
            
            else:
                self.tt.logAction(self.tt.TYPE_SPATIAL)

            event.accept()

        elif event.button() == Qt.RightButton:
            # cancel selection mode if active
            if self.selection_mode in [1, 2]:
                self.__resetSelectionMode()
                event.accept()

        elif event.button() == Qt.MiddleButton:
            self.tt.logAction(self.tt.TYPE_SPATIAL)
            self.last_mouse_pos = event.localPos()
            self.mouse_mid_pressed = True
            event.accept()
            
        else:
            event.ignore()

    def __resetSelectionMode(self):
        self.selection_mode = 0
        self.vertebra_highlighted = None
        self.vertebra_selected = None
        self.updateRenderLists()
        
    def mouseReleaseEvent(self, event):
        self.mouse_left_pressed = False
        self.mouse_mid_pressed  = False
        event.accept()

    def mouseMoveEvent(self, event):
        # highlight selectable objects
        if self.selection_mode != 0:
            x = event.localPos().x()
            y = event.localPos().y()
            index = gl.glReadPixels(x, self.height() - y - 1, 1, 1, gl.GL_STENCIL_INDEX, gl.GL_UNSIGNED_INT)[0][0]
            if index != 255:
                # found a selectable object
                self.vertebra_highlighted = self.vertebrae[index]
            else:
                self.vertebra_highlighted = None

        # rotate camera
        if self.mouse_left_pressed:
            travel = event.localPos() - self.last_mouse_pos
            self.last_mouse_pos = event.localPos()
            self.camera.rotate(travel.x()*0.5, travel.y()*0.5)
            event.accept()
        # translate camera
        elif self.mouse_mid_pressed:
            travel = event.localPos() - self.last_mouse_pos
            self.last_mouse_pos = event.localPos()
            self.camera.pan(travel.x()*0.001, travel.y()*0.001)
            event.accept()
        else:
            event.ignore()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_V:
            print("Active OpenGL version:", gl.glGetString(gl.GL_VERSION))
            event.accept()
        else:
            event.ignore()

    def addHA(self, ref, tar, method):
        color = [1.0, 0.0, 0.0]
        for i in range(len(self.active_colors)):
            if not self.active_colors[i]:
                self.active_colors[i] = True
                color = CORR_COLORS_NORM[i]
                break
        s = self.timeloop.t_span / self.timeloop.index_span
        g = geometry.glyphGeometry(GLYPH_PATH_SHAFT, GLYPH_PATH_TIP, ref, tar, color, s, method)
        self.add_checkbox_func(g)
        self.glyphs.append(g)

    def setGlyphThickness(self, thickness):
        gl.glUseProgram(self.shader_glyph)
        gl.glUniform1f(self.uniform_locations_glyph['thickness'], thickness)

    def setGlyphLength(self, length):
        gl.glUseProgram(self.shader_glyph)
        gl.glUniform1f(self.uniform_locations_glyph['len'], length)
        gl.glUseProgram(self.shader_surface)
        gl.glUniform1f(self.uniform_locations_surface['len'], length)

    def setGlyphOffset(self, offset):
        gl.glUseProgram(self.shader_glyph)
        gl.glUniform1f(self.uniform_locations_glyph['offset'], offset)
        gl.glUseProgram(self.shader_surface)
        gl.glUniform1f(self.uniform_locations_surface['offset'], offset)

    def setSurfaceOpacity(self, opacity):
        gl.glUseProgram(self.shader_surface)
        gl.glUniform1f(self.uniform_locations_surface['opacity'], opacity)

    def setPhiLThreshold(self, phi_min, phi_max, l_min, l_max):
        gl.glUseProgram(self.shader_glyph)
        gl.glUniform4f(self.uniform_locations_glyph['phiLBounds'], phi_min, phi_max, l_min, l_max)
        gl.glUseProgram(self.shader_surface)
        gl.glUniform4f(self.uniform_locations_glyph['phiLBounds'], phi_min, phi_max, l_min, l_max)

    def setLAbs(self, set_abs):
        if set_abs:
            gl.glUseProgram(self.shader_glyph)
            gl.glUniform1i(self.uniform_locations_glyph['l_abs'], 1)
            gl.glUseProgram(self.shader_surface)
            gl.glUniform1i(self.uniform_locations_surface['l_abs'], 1)
            for g in self.glyphs:
                g.instance_parameters_l = np.abs(g.instance_parameters['l'])
        else:
            gl.glUseProgram(self.shader_glyph)
            gl.glUniform1i(self.uniform_locations_glyph['l_abs'], 0)
            gl.glUseProgram(self.shader_surface)
            gl.glUniform1i(self.uniform_locations_surface['l_abs'], 0)
            for g in self.glyphs:
                g.instance_parameters_l = g.instance_parameters['l']
        
        # update plot data
        time_axis = np.linspace(self.timeloop.t_min, self.timeloop.t_max, self.timeloop.index_span)
        for g in self.glyphs:
            g.scatterplot_l_phi.setData(g.instance_parameters['phi'], g.instance_parameters_l)
            if not g.visible:
                g.scatterplot_l_phi.setPointsVisible(False)
            g.lineplot_l.setData(x=time_axis, y=g.instance_parameters_l)

    def setR0_loc(self, name):
        self.tt.logAction(self.tt.TYPE_GLYPH_SETTINGS)
        if name == "World Origin":
            gl.glUseProgram(self.shader_glyph)
            gl.glUniform1i(self.uniform_locations_glyph['r0_loc'], 0)
            gl.glUseProgram(self.shader_surface)
            gl.glUniform1i(self.uniform_locations_surface['r0_loc'], 0)
        if name == "Base Origin":
            gl.glUseProgram(self.shader_glyph)
            gl.glUniform1i(self.uniform_locations_glyph['r0_loc'], 1)
            gl.glUseProgram(self.shader_surface)
            gl.glUniform1i(self.uniform_locations_surface['r0_loc'], 1)
        if name == "Target Origin":
            gl.glUseProgram(self.shader_glyph)
            gl.glUniform1i(self.uniform_locations_glyph['r0_loc'], 2)
            gl.glUseProgram(self.shader_surface)
            gl.glUniform1i(self.uniform_locations_surface['r0_loc'], 2)

    def activateSelectionMode(self):
        # activate only if not already active
        if self.selection_mode == 0:
            self.selection_mode = 1

    def updateMotionData(self, motion_path, abs_l):
        """
        Used to load a new motion data set with the same geometry and number of time steps.
        Assumes data are already intialized (initializeGL was called).
        """
        self.motion_path = motion_path

        # update model matrices of each vertebra
        pos_names = sorted(glob(self.motion_path + "/*pos.txt"))
        rot_names = sorted(glob(self.motion_path + "/*rot.txt"))
        assert(len(pos_names) == len(rot_names))
        for i in range(len(pos_names)):
            self.vertebrae[i].loadModelMatrices(pos_names[i], rot_names[i], scale=settings['models_scale'])

        # update glyphs (glyphs know their associated models)
        time_axis = np.linspace(self.timeloop.t_min, self.timeloop.t_max, self.timeloop.index_span)
        for glyph in self.glyphs:
            glyph.bufferParameters()
            if abs_l:
                glyph.instance_parameters_l = np.abs(glyph.instance_parameters['l'])
            glyph.scatterplot_l_phi.setData(glyph.instance_parameters['phi'],
                                            glyph.instance_parameters_l)
            glyph.lineplot_phi.setData(x=time_axis, y=glyph.instance_parameters['phi'])
            glyph.lineplot_l.setData(x=time_axis, y=glyph.instance_parameters_l)
            

        # check that all models have the same number of timesteps
        nr_animation_steps = [v.rot_list.shape[0] for v in self.vertebrae]
        assert(len(set(nr_animation_steps)) == 1)

        # update the index range based on the number of time steps found
        self.timeloop.updateIndexRange(0, nr_animation_steps[0] - 1)

    def updateRenderLists(self):
        """
        Call this when object visibility / rendering type changed.
        """
        # clear outlines
        for v in self.vertebrae:
            v.outline_colors.clear()

        # update glyphs and surfaces
        self.glyphs_visible = [g for g in self.glyphs if g.visible]

        # update outline colors of visible glyphs
        for g in self.glyphs_visible:
            if g.ref != None:
                g.ref.outline_colors.append(g.corr_color)
            if g.tar != None:
                g.tar.outline_colors.append(g.corr_color)

        # update vertebrae
        self.vertebrae_on = []
        self.vertebrae_off = []
        for v in self.vertebrae:
            if len(v.outline_colors) != 0:
                self.vertebrae_on.append(v)
            else:
                self.vertebrae_off.append(v)
        


class MainWindow(QMainWindow):
    """
    This is the main window. Handles all controls, views, and communication.
    """
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.tt = TimeTracker()

        # load settings
        self.loadSettings(INITIAL_FOLDER + "/settings.txt")

        # folderpath to models / motion data
        self.folder_selector = helperQt.FolderSelector(self.loadFolder, INITIAL_FOLDER)
        self.selector = helperQt.DatasetSelector(self.loadDataset, INITIAL_FOLDER)
        self.active_folder = INITIAL_FOLDER

        # setup time control
        self.timeloop = helperQt.TimeLoop(settings['time_start'], settings['time_end'], 0, 100)
        time = settings['time_start'] + 0.1 * (settings['time_end'] - settings['time_start']) # start at 10% time
        self.timeloop.setTime(settings['time_start'], time) # set interval
        self.animation_timer = QTimer(self) # Qtimer for animation
        self.animation_timer.timeout.connect(self.animationStep)

        # export window
        self.export_dialog = helperQt.ExportDialog(self.timeloop)

        # plots widget
        # ----------------------------------------
        # scatterplot widget
        cb_roi = QCheckBox()
        cb_roi.setChecked(True)
        cb_roi.setText("Show ROI")
        cb_roi.stateChanged[int].connect(self.toggleROI)
        self.cb_abs = QCheckBox() # connected after main view is created
        self.cb_abs.setChecked(False)
        self.cb_abs.setText("|Translation Vel.|")
        self.cb_abs.stateChanged[int].connect(self.setLAbs)
        self.scatterplot_l_phi = helperQt.Scatter2D()
        self.scatterplot_l_phi.roi.sigRegionChanged.connect(self.ROIchanged)

        # lineplot widgets
        widget_lineplot = pg.GraphicsLayoutWidget()

        self.lineplot_phi = widget_lineplot.addPlot()
        self.lineplot_phi.setLabel('left', "Rotation Vel. (rad/s)", **LABEL_STYLE)
        self.lineplot_phi.setLabel('bottom', " ", **LABEL_STYLE)
        self.lineplot_phi.showGrid(x=False, y=True, alpha=0.2)
        
        widget_lineplot.nextRow()
        self.lineplot_l = widget_lineplot.addPlot()
        self.lineplot_l.setLabel('left', "Translation Vel. (m/s)", **LABEL_STYLE)
        self.lineplot_l.setLabel('bottom', "Time (s)", **LABEL_STYLE)
        self.lineplot_l.showGrid(x=False, y=True, alpha=0.2)
        self.lineplot_l.setXLink(self.lineplot_phi)

        # lineplot widgets time region
        pen = pg.mkPen(color=(0, 0, 0, 80), width=1.5)
        hoverPen = pg.mkPen(color=(0, 0, 0, 80), width=1.5)
        brush = pg.mkBrush(color=(0, 0, 0, 5))
        lineplot_time_ROI_phi = pg.LinearRegionItem((self.timeloop.t_min, self.timeloop.t_max*0.1),
                                                    brush=brush, hoverBrush=brush,
                                                    pen=pen, hoverPen=hoverPen)
                                                    #bounds=[self.timeloop.t_min, self.timeloop.t_max])
        lineplot_time_ROI_l   = pg.LinearRegionItem((self.timeloop.t_min, self.timeloop.t_max*0.1),
                                                    brush=brush, hoverBrush=brush,
                                                    pen=pen, hoverPen=hoverPen)
                                                    #bounds=[self.timeloop.t_min, self.timeloop.t_max])
        lineplot_time_ROI_phi.setMovable(False)
        lineplot_time_ROI_l.setMovable(False)
        
        pen = pg.mkPen(color=(0, 0, 0, 180), width=1.5)
        self.lineplot_time_phi = pg.InfiniteLine(angle=90, pen=pen, bounds=[settings['time_start'], settings['time_end']])
        self.lineplot_time_l   = pg.InfiniteLine(angle=90, pen=pen, bounds=[settings['time_start'], settings['time_end']])
        
        self.lineplot_phi.addItem(lineplot_time_ROI_phi)
        self.lineplot_l.addItem(lineplot_time_ROI_l)

        # add everything to a layout
        layout_scatter_settings = QHBoxLayout()
        layout_scatter_settings.setAlignment(Qt.AlignLeft)
        layout_scatter_settings.addWidget(cb_roi)
        layout_scatter_settings.addWidget(self.cb_abs)
        self.layout_plots = QVBoxLayout()
        self.layout_plots.addLayout(layout_scatter_settings)
        self.layout_plots.addWidget(self.scatterplot_l_phi)
        self.layout_plots.addWidget(widget_lineplot)

        # create a settings dock widget
        wrapper = QWidget()
        wrapper.setLayout(self.layout_plots)
        self.dock_widget_plots = QDockWidget("Plots")
        self.dock_widget_plots.setWidget(wrapper)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_widget_plots)

        # main view (OpenGL)
        # ----------------------------------------
        # set rendering parameters
        qformat = QSurfaceFormat()
        qformat.setRenderableType(QSurfaceFormat.OpenGL)
        qformat.setProfile(QSurfaceFormat.CoreProfile)
        qformat.setVersion(4, 0) # major, minor OpenGL versions
        qformat.setSwapBehavior(QSurfaceFormat.DoubleBuffer) # enables glSwapBuffers
        qformat.setSwapInterval(1) # continuous = 0, vsync = 1
        qformat.setSamples(16) # 4xMSAA

        # create the main view
        self.view_main = GLWindow(self.tt, self.timeloop, self.scatterplot_l_phi, list(self.selector.folderpaths.values())[0], self.addGlyphSet)
        self.view_main.setFormat(qformat)
        view_main_widget = QWidget.createWindowContainer(self.view_main)
        self.setCentralWidget(view_main_widget)

        # settings widget
        # ----------------------------------------
        # create all widgets
        slider_arrow_scale  = helperQt.SmartSlider(self.tt, self.view_main.setGlyphThickness, "Arrow Thickness", 0.01, 2, INITIAL_THICKNESS)
        slider_arrow_length = helperQt.SmartSlider(self.tt, self.view_main.setGlyphLength, "Arrow Length", 0.1, 20, INITIAL_LENGTH)
        slider_arrow_offset = helperQt.SmartSlider(self.tt, self.view_main.setGlyphOffset, "Arrow Offset", -15, 15, INITIAL_OFFSET)
        slider_surface_opac = helperQt.SmartSlider(self.tt, self.view_main.setSurfaceOpacity, "Surface Opacity", 0, 1, 0)
        button_FHAworld = QPushButton("Add FHA World")
        button_FHAworld.setCheckable(False)
        button_FHAworld.clicked.connect(self.addFHAworld)
        button_FHAworld.setToolTip("Compute the finite helical axes of an object's movements in the world.")
        button_FHAref = QPushButton("Add FHA Base")
        button_FHAref.setCheckable(False)
        button_FHAref.clicked.connect(self.addFHAref)
        button_FHAref.setToolTip("Compute the finite helical axes of an object's movements regarding a base object.")
        button_export = QPushButton("Export Axes")
        button_export.setCheckable = False
        button_export.clicked.connect(self.exportFHA)
        label_arrow_start = QLabel("Arrows start close to")
        combobox_arrow_start = QComboBox()
        combobox_arrow_start.addItem("World Origin")
        combobox_arrow_start.addItem("Base Origin")
        combobox_arrow_start.addItem("Target Origin")
        combobox_arrow_start.activated[str].connect(self.view_main.setR0_loc)
        combobox_arrow_start.setToolTip("Choose where the arrow glyphs begin.\nThis only translates the glyphs along their axis.")

        # add everything to a layout
        layout_settings = QVBoxLayout()
        layout_settings.setAlignment(Qt.AlignTop)
        layout_settings.addWidget(self.folder_selector)
        layout_settings.addWidget(self.selector)
        layout_settings.addWidget(helperQt.HorizontalLine())
        layout_settings.addWidget(QLabel("Display"))
        layout_settings.addWidget(slider_arrow_scale)
        layout_settings.addWidget(slider_arrow_length)
        layout_settings.addWidget(slider_arrow_offset)
        layout_settings.addWidget(slider_surface_opac)
        layout_arrow_start = QHBoxLayout()
        layout_arrow_start.addWidget(label_arrow_start)
        layout_arrow_start.addWidget(combobox_arrow_start)
        layout_settings.addLayout(layout_arrow_start)
        layout_settings.addWidget(helperQt.HorizontalLine())

        layout_settings.addWidget(QLabel("Helical Axis Sets"))
        self.layout_HA_sets = QVBoxLayout()
        layout_settings.addLayout(self.layout_HA_sets)

        layout_FHA_buttons = QHBoxLayout()
        layout_FHA_buttons.addWidget(button_FHAworld)
        layout_FHA_buttons.addWidget(button_FHAref)
        layout_settings.addLayout(layout_FHA_buttons)
        layout_settings.addStretch(1)
        layout_settings.addWidget(button_export)

        # create a settings dock widget
        wrapper = QWidget()
        wrapper.setLayout(layout_settings)
        dock_widget_settings = QDockWidget("Settings")
        dock_widget_settings.setWidget(wrapper)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock_widget_settings)
        

        # time slider widget
        # ----------------------------------------
        # play button
        button_play = QPushButton("Play")
        button_play.setCheckable(True)
        button_play.clicked.connect(self.playToggle)

        # preview button
        self.button_preview = QPushButton("Live View")
        self.button_preview.setCheckable(True)
        self.button_preview.clicked.connect(self.previewToggle)

        # actual time slider
        self.timeSlider = helperQt.TimeSlider(self.timeloop, TIME_COLORS, self.tt, settings['time_start'], settings['time_end'])
        self.timeSlider.registerMirroredROI(lineplot_time_ROI_phi)
        self.timeSlider.registerMirroredROI(lineplot_time_ROI_l)
        self.timeSlider.registerMirroredvLine(self.lineplot_time_phi)
        self.timeSlider.registerMirroredvLine(self.lineplot_time_l)

        # add everything to a layout
        layout_time_buttons = QVBoxLayout()
        layout_time_buttons.addWidget(button_play)
        layout_time_buttons.addWidget(self.button_preview)

        layout_time = QHBoxLayout()
        layout_time.addLayout(layout_time_buttons)
        layout_time.addWidget(self.timeSlider)

        # create a dock widget
        wrapper = QWidget()
        wrapper.setLayout(layout_time)
        wrapper.setFixedHeight(80)
        self.dock_widget_time = QDockWidget("Time (s)")
        self.dock_widget_time.setWidget(wrapper)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.dock_widget_time)

        self.tt.resetTimer()

    def loadDataset(self, target_dir):
        self.tt.logAction(self.tt.TYPE_DATASET_CHANGE, target_dir)
        self.view_main.updateMotionData(target_dir, self.cb_abs.isChecked())
        self.scatterplot_l_phi.resetROI()

    def playToggle(self, state):
        self.tt.logAction(self.tt.TYPE_ANIMATION)
        if(state):
            self.button_preview.setDisabled(True)
            if self.button_preview.isChecked():
                self.button_preview.setChecked(False)
                self.previewToggle(False)
            self.timeSlider.prepareAnimation()
            self.animation_timer.start(17)
        else:
            self.button_preview.setDisabled(False)
            self.animation_timer.stop()
            self.timeSlider.animationEnded()

    def previewToggle(self, state):
        self.tt.logAction(self.tt.TYPE_TEMP_PREVIEW)
        self.timeloop.setTimePreviewActive(state)
        if(state):
            self.timeSlider.setPreviewOn()
            self.lineplot_phi.addItem(self.lineplot_time_phi)
            self.lineplot_l.addItem(self.lineplot_time_l)
        else:
            self.timeSlider.setPreviewOff()
            self.lineplot_phi.removeItem(self.lineplot_time_phi)
            self.lineplot_l.removeItem(self.lineplot_time_l)

    def animationStep(self):
        self.timeloop.addTime(0.017)
        self.timeSlider.time_selector.setRegion((self.timeloop.t_lower, self.timeloop.t))

    def addFHAworld(self):
        self.view_main.HA_compute_method = "FHAworld"
        self.view_main.selection_tooltips = FHA_WORLD_TOOLTIPS
        self.view_main.HA_tooltip = FHA_WORLD_TOOLTIPS[0]
        self.view_main.activateSelectionMode()
    
    def addFHAref(self):
        self.view_main.HA_compute_method = "FHAref"
        self.view_main.selection_tooltips = FHA_BASE_TOOLTIPS
        self.view_main.HA_tooltip = FHA_BASE_TOOLTIPS[0]
        self.view_main.activateSelectionMode()
    
    def addFHAref2(self):
        self.view_main.HA_compute_method = "FHAref_projectFirst"
        self.view_main.selection_tooltips = FHA_BASE_TOOLTIPS
        self.view_main.HA_tooltip = FHA_BASE_TOOLTIPS[0]
        self.view_main.activateSelectionMode()

    def addRHA(self):
        self.view_main.HA_compute_method = "RHA"
        self.view_main.selection_tooltips = RHA_TOOLTIPS
        self.view_main.HA_tooltip = RHA_TOOLTIPS[0]
        self.view_main.activateSelectionMode()

    def loadHAfile(self):
        self.view_main.addHAfromFile()

    def addGlyphSet(self, glyph):
        if "world" in glyph.name:
            self.tt.logAction(self.tt.TYPE_ADD_AXIS_WORLD)
        else:
            self.tt.logAction(self.tt.TYPE_ADD_AXIS_BASE)

        # correlation color of this glyph in [0,255]
        color = (glyph.corr_color * 255.0).astype(np.int16)
        color = QColor(color[0], color[1], color[2], 255)
        
        # add scatterplot and lineplots of phi/l
        if self.cb_abs.isChecked():
            glyph.instance_parameters_l = np.abs(glyph.instance_parameters['l'])
        s, st, s_preview = self.scatterplot_l_phi.addPlotItem(glyph.instance_parameters['phi'],
                                               glyph.instance_parameters_l,
                                               color)
        time_axis = np.linspace(self.timeloop.t_min, self.timeloop.t_max, self.timeloop.index_span)
        lp_phi = self.lineplot_phi.plot(x=time_axis, y=glyph.instance_parameters['phi'], pen=color)
        lp_l = self.lineplot_l.plot(x=time_axis, y=glyph.instance_parameters_l, pen=color)

        glyph.registerPlotItems(s, st, s_preview, lp_phi, lp_l)

        # create a new checkbox for this glyph set
        c = QCheckBox()
        c.setChecked(True)
        c.setText(glyph.name)
        c.stateChanged[int].connect(glyph.setVisibility)
        c.stateChanged[int].connect(self.view_main.updateRenderLists)
        c.stateChanged[int].connect(s.setPointsVisible)
        c.stateChanged[int].connect(st.setPointsVisible)
        c.stateChanged[int].connect(s_preview.setPointsVisible)
        c.stateChanged[int].connect(lp_phi.setVisible)
        c.stateChanged[int].connect(lp_l.setVisible)

        # set the checkbox color
        p = QPalette()
        p.setColor(QPalette.Active, QPalette.Base, color)
        c.setPalette(p)

        # create a delete button
        b = QPushButton()
        b.setIcon(QIcon(resource_path("ico/trash.png")))
        b.setToolTip("Delete")
        b.clicked.connect(glyph.initiateDelete)
        b.clicked.connect(self.deleteGlyphs)

        l = QHBoxLayout()
        l.addWidget(c)
        l.addStretch(1)
        l.addWidget(b)
        glyph.registerCheckboxLayout(l)
        self.layout_HA_sets.addLayout(l)
        self.layout_HA_sets.removeItem

    def ROIchanged(self):
        self.tt.logAction(self.tt.TYPE_ATT_FILTER)
        p = self.scatterplot_l_phi.roi.pos()
        s = self.scatterplot_l_phi.roi.size()
        phi_min = p[0]
        phi_max = p[0] + s[0]
        if s[0] < 0:
            phi_min, phi_max = phi_max, phi_min
        l_min = p[1]
        l_max = p[1] + s[1]
        if s[1] < 0:
            l_min, l_max = l_max, l_min
        self.view_main.setPhiLThreshold(phi_min, phi_max, l_min, l_max)
        self.export_dialog.setROIrange(phi_min, phi_max, l_min, l_max)

    def toggleROI(self, state):
        self.tt.logAction(self.tt.TYPE_ATT_FILTER)
        if state == 0:
            self.scatterplot_l_phi.showROI(False)
            self.export_dialog.setROIFilterEnabled(False)
            self.view_main.setPhiLThreshold(-10000, 10000, -10000, 10000)
        else:
            self.scatterplot_l_phi.showROI(True)
            self.export_dialog.setROIFilterEnabled(True)
            self.ROIchanged()

    def setLAbs(self, set_abs):
        self.tt.logAction(self.tt.TYPE_ABS_TRANS)
        self.view_main.setLAbs(set_abs)
        if set_abs:
            self.lineplot_l.setLabel('left', "|Translation Vel.| (m/s)", **LABEL_STYLE)
            self.scatterplot_l_phi.setLabel('left', "|Translation Vel.| (m/s)", **LABEL_STYLE)
        else:
            self.lineplot_l.setLabel('left', "Translation Vel. (m/s)", **LABEL_STYLE)
            self.scatterplot_l_phi.setLabel('left', "Translation Vel. (m/s)", **LABEL_STYLE)

    def deleteGlyphs(self):
        # search for glyphs to be deleted
        self.tt.logAction(self.tt.TYPE_RM_AXIS)
        glyphs_del = [g for g in self.view_main.glyphs if g.to_be_deleted]
        for g in glyphs_del:
            # free color
            c = g.corr_color.tolist()
            idx = CORR_COLORS_NORM.tolist().index(c)
            self.view_main.active_colors[idx] = False

            # remove items from graphs and lists
            s = g.scatterplot_l_phi
            st = g.scatterplot_l_phi_time
            s_preview = g.scatterplot_l_phi_preview
            self.scatterplot_l_phi.removePlotItems(s, st, s_preview)
            self.lineplot_phi.removeItem(g.lineplot_phi)
            self.lineplot_l.removeItem(g.lineplot_l)

            # remove layout from view
            for i in reversed(range(g.checkboxLayout.count())):
                item = g.checkboxLayout.takeAt(i)
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
                else:
                    g.checkboxLayout.removeItem(item)
            self.layout_HA_sets.removeItem(g.checkboxLayout)

            # delete the glyph from the glyphs list
            self.view_main.glyphs.remove(g)

        # update the view
        self.view_main.updateRenderLists()

    def loadSettings(self, file):
        f = open(file)
        for l in f.readlines():
            name, value = l.split()
            settings[name] = float(value)

    def loadFolder(self):
        path = self.folder_selector.getText()
        if path == self.active_folder:
            return
        self.active_folder = path

        self.tt.logAction(self.tt.TYPE_FOLDER_CHANGE, path)
        self.selector.reload(path)
        self.loadSettings(path + "/settings.txt")

        # remove all axes
        for g in self.view_main.glyphs:
            g.initiateDelete()
        self.deleteGlyphs()

        # reset time
        self.timeloop.setupLoop(settings['time_start'], settings['time_end'], 0, 100)
        self.timeSlider.resetRegion(TIME_COLORS, settings['time_start'], settings['time_end'])

        for v in self.view_main.vertebrae:
            v.initiateDelete()
        self.view_main.motion_path = list(self.selector.folderpaths.values())[0]
        self.view_main.initScene(path)

    def exportFHA(self):
        self.export_dialog.active_glyphs = self.view_main.glyphs_visible
        self.export_dialog.exec()

    def closeEvent(self, event):
        self.tt.writeLog()
        return QMainWindow.closeEvent(self, event)


if __name__ == '__main__':
    # create an application context
    app = QApplication(sys.argv)
    app.setOrganizationName("VisGroup Uni Jena")
    app.setOrganizationDomain("vis.uni-jena.de")
    app.setApplicationName("HAExplorer")
    app.setStyle("Fusion")

    # create the main window
    window = MainWindow()
    window.resize(WINDOW_SIZE_X, WINDOW_SIZE_Y)
    window.show()

    sys.exit(app.exec_())