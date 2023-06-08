# -----------------------------------------------------------------------------
# Copyright (c) 2021 Pepe Eulzer. All rights reserved.
# Distributed under the (new) BSD License.
# -----------------------------------------------------------------------------

import ctypes
import os

import numpy as np
import OpenGL.GL as gl
from PyQt5.QtGui import QMatrix4x4

import helperGL
import conversions
from defaults import *

class referenceGeometry():
    """
    Handles buffers, modelmatrix, etc. of one reference object,
    for example a vertebra.
    """
    def __init__(self, model_path, pos_path, rot_path, stencil_id, scale=1.0):
        # set stencil id
        self.stencil_id = stencil_id

        # set name
        __, tail = os.path.split(model_path)
        self.name = tail.split("_")[0]      # L1_something.obj -> L1
        self.name = self.name.split(".")[0] # L1.obj -> L1

        # colors for outlines
        self.outline_colors = []

        # load and buffer the geometry
        self.VAO, self.EBO_size = helperGL.obj_to_VAO(model_path)
        self.loadModelMatrices(pos_path, rot_path, scale)

    def loadModelMatrices(self, pos_path, rot_path, scale=1.0):
        # setup a modelmatrix for each timestep
        translations = np.loadtxt(pos_path, skiprows=1, dtype=np.float32)#[::100]
        rotations    = np.loadtxt(rot_path, skiprows=1, dtype=np.float32)#[::100]
        assert(translations.shape[0] == rotations.shape[0])

        self.model_matrices = [QMatrix4x4() for i in range(len(translations))]
        for i in range(len(translations)):
            R = QMatrix4x4(rotations[i,0], rotations[i,1], rotations[i,2], 0.0,
                           rotations[i,3], rotations[i,4], rotations[i,5], 0.0,
                           rotations[i,6], rotations[i,7], rotations[i,8], 0.0,
                           0.0,            0.0,            0.0,            1.0)
            # bottom-up transforms
            self.model_matrices[i].translate(translations[i,0], translations[i,1], translations[i,2])
            self.model_matrices[i] = self.model_matrices[i] * R
            self.model_matrices[i].scale(scale)

        # save rotation matrices and translations separately for helical axis computation
        self.rot_list = rotations.reshape(-1,3,3)
        self.trans_list = translations.reshape(-1,3)

    def initiateDelete(self):
        gl.glBindVertexArray(0)
        gl.glDeleteVertexArrays(1, [self.VAO])


class glyphGeometry():
    """
    Handles buffers, modelmatrices, etc. of a glyph set.
    Contains geometry for one set of arrows and one surface.
    Can be linked to a scatterplot and lineplots of phi/l.
    Input:
      - model_path: path to the glyph geometry file
      - ref: the reference object in the scene (selected first)
      - tar: the target object in the scene (selected second)
      - timestep_size: the time increment in s
      - method: HA computation method used, one of
        * 'FHAworld' finite helical axis of tar w.r.t. world system
        * 'FHAref' finite helical axis of tar w.r.t. ref system, r0 closest to world origin
    """
    def __init__(self, shaft_path, tip_path, ref, tar, corr_color, timestep_size, method, r0_path=None, n_path=None):
        self.ref = ref
        self.tar = tar
        self.scatterplot_l_phi = None
        self.scatterplot_l_phi_time = None
        self.scatterplot_l_phi_preview = None
        self.lineplot_phi = None
        self.lineplot_l = None
        self.checkboxLayout = None
        self.corr_color = corr_color
        self.name = "Initializing..."
        self.method = method
        self.r0_path = r0_path
        self.n_path = n_path
        self.timestep_size = timestep_size
        self.to_be_deleted = False

        # create and load VAOs
        self.VAO_shaft, self.EBO_shaft_size = helperGL.obj_to_VAO(shaft_path)
        self.VAO_tip, self.EBO_tip_size = helperGL.obj_to_VAO(tip_path)
        self.VAO_surface = gl.glGenVertexArrays(1)
        self.VBO_parameters, self.VBO_surface = gl.glGenBuffers(2)

        # compute axes, buffer vertex and instance parameters
        # this is also externally called when data is updated
        self.bufferParameters()

        # set visibility for self and corresponding reference geometries
        self.visible = True
        if self.ref != None:
            self.ref.outline_colors.append(self.corr_color)
        if self.tar != None:
            self.tar.outline_colors.append(self.corr_color)

    def bufferParameters(self):
        # compute axes
        # ----------------------------------------
        if self.method == 'FHAworld':
            self.name = "FHA " + self.tar.name + " world"
            # compute the finite helical axis of tar w.r.t. the world system
            n, r0, r0_displ_base, r0_displ_tar, phi, l = conversions.computeFHAworld(self.tar.rot_list, self.tar.trans_list)
            self.nr_instances = n.shape[0]

        elif self.method == 'FHAref':
            self.name = "FHA " + self.tar.name + " base " + self.ref.name
            # compute the finite helical axis of tar w.r.t. ref
            n, r0, r0_displ_base, r0_displ_tar, phi, l = conversions.computeFHAref(
                self.ref.rot_list, self.ref.trans_list,
                self.tar.rot_list, self.tar.trans_list)
            self.nr_instances = n.shape[0]

        # scale phi/l by timestep size -> velocities
        phi /= self.timestep_size
        l /= self.timestep_size

        # create surface
        # ----------------------------------------
        self.__createSurfaceGeometry(r0, r0_displ_base, r0_displ_tar, n, phi, l, scale=settings['glyphs_scale'])

        # create arrow glyph instances
        # ----------------------------------------
        self.instance_parameters = np.zeros(self.nr_instances, [("color", np.float32, 3),
                                                                ("n", np.float32, 3),
                                                                ("r0", np.float32, 3),
                                                                ("r0_displ_base", np.float32),
                                                                ("r0_displ_tar", np.float32),
                                                                ("phi", np.float32),
                                                                ("l", np.float32)])
        
        self.instance_parameters["color"]         = helperGL.colormapRGB(TIME_COLORS, self.nr_instances)
        self.instance_parameters["n"]             = n
        self.instance_parameters["r0"]            = r0
        self.instance_parameters["r0_displ_base"] = r0_displ_base
        self.instance_parameters["r0_displ_tar"]  = r0_displ_tar
        self.instance_parameters["phi"]           = phi
        self.instance_parameters["l"]             = l
        self.instance_parameters_l = self.instance_parameters["l"] # can be switched to |L|

        # buffer data
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.VBO_parameters)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, self.instance_parameters.nbytes, self.instance_parameters, gl.GL_STATIC_DRAW)

        # define layout
        # assign the parameter VBO to both VAOs
        for VAO in [self.VAO_shaft, self.VAO_tip]:
            gl.glBindVertexArray(VAO)
            stride = self.instance_parameters.strides[0]
            # "colors"
            offset = ctypes.c_void_p(0)
            gl.glEnableVertexAttribArray(2)
            gl.glVertexAttribPointer(2, 3, gl.GL_FLOAT, gl.GL_FALSE, stride, offset)
            gl.glVertexAttribDivisor(2, 1)
            # "n"
            offset = ctypes.c_void_p(self.instance_parameters.dtype["color"].itemsize)
            gl.glEnableVertexAttribArray(3)
            gl.glVertexAttribPointer(3, 3, gl.GL_FLOAT, gl.GL_FALSE, stride, offset)
            gl.glVertexAttribDivisor(3, 1)
            # "r0"
            offset = ctypes.c_void_p(self.instance_parameters.dtype["color"].itemsize
                                   + self.instance_parameters.dtype["n"].itemsize)
            gl.glEnableVertexAttribArray(4)
            gl.glVertexAttribPointer(4, 3, gl.GL_FLOAT, gl.GL_FALSE, stride, offset)
            gl.glVertexAttribDivisor(4, 1)
            # "r0_displ_base"
            offset = ctypes.c_void_p(self.instance_parameters.dtype["color"].itemsize
                                   + self.instance_parameters.dtype["n"].itemsize
                                   + self.instance_parameters.dtype["r0"].itemsize)
            gl.glEnableVertexAttribArray(5)
            gl.glVertexAttribPointer(5, 1, gl.GL_FLOAT, gl.GL_FALSE, stride, offset)
            gl.glVertexAttribDivisor(5, 1)
            # "r0_displ_tar"
            offset = ctypes.c_void_p(self.instance_parameters.dtype["color"].itemsize
                                   + self.instance_parameters.dtype["n"].itemsize
                                   + self.instance_parameters.dtype["r0"].itemsize
                                   + self.instance_parameters.dtype["r0_displ_base"].itemsize)
            gl.glEnableVertexAttribArray(6)
            gl.glVertexAttribPointer(6, 1, gl.GL_FLOAT, gl.GL_FALSE, stride, offset)
            gl.glVertexAttribDivisor(6, 1)

            # "phi"
            offset = ctypes.c_void_p(self.instance_parameters.dtype["color"].itemsize
                                   + self.instance_parameters.dtype["n"].itemsize
                                   + self.instance_parameters.dtype["r0"].itemsize
                                   + self.instance_parameters.dtype["r0_displ_base"].itemsize
                                   + self.instance_parameters.dtype["r0_displ_tar"].itemsize)
            gl.glEnableVertexAttribArray(7)
            gl.glVertexAttribPointer(7, 1, gl.GL_FLOAT, gl.GL_FALSE, stride, offset)
            gl.glVertexAttribDivisor(7, 1)
            # "l"
            offset = ctypes.c_void_p(self.instance_parameters.dtype["color"].itemsize
                                   + self.instance_parameters.dtype["n"].itemsize
                                   + self.instance_parameters.dtype["r0"].itemsize
                                   + self.instance_parameters.dtype["r0_displ_base"].itemsize
                                   + self.instance_parameters.dtype["r0_displ_tar"].itemsize
                                   + self.instance_parameters.dtype["phi"].itemsize)
            gl.glEnableVertexAttribArray(8)
            gl.glVertexAttribPointer(8, 1, gl.GL_FLOAT, gl.GL_FALSE, stride, offset)
            gl.glVertexAttribDivisor(8, 1)
        gl.glBindVertexArray(0)

    def __createSurfaceGeometry(self, r0_list, r0_displ_base_list, r0_displ_tar_list, n_list, phi_list, L_list, scale=1.0):
        # set positions
        # ----------------------------------------
        self.nr_points = len(r0_list) * 2
        positions = np.zeros((self.nr_points, 3))
        displ_base = np.zeros(self.nr_points)
        displ_tar = np.zeros(self.nr_points)
        phi = np.zeros(self.nr_points)
        L = np.zeros(self.nr_points)

        for i in range(len(r0_list)):
            positions[i*2] = r0_list[i]
            positions[i*2+1] = r0_list[i] + n_list[i] * scale
            phi[i*2] = phi_list[i]
            phi[i*2+1] = phi_list[i]
            L[i*2] = L_list[i]
            L[i*2+1] = L_list[i]
            displ_base[i*2] = r0_displ_base_list[i]
            displ_base[i*2+1] = r0_displ_base_list[i]
            displ_tar[i*2] = r0_displ_tar_list[i]
            displ_tar[i*2+1] = r0_displ_tar_list[i]

        # calculate surface normals / glyph direction / colors
        # ----------------------------------------
        normals = np.zeros((self.nr_points, 3))
        directions = np.zeros((self.nr_points, 3))
        colors = helperGL.colormapRGB(TIME_COLORS, self.nr_points)

        # the first point pair
        connection = positions[1] - positions[0]
        connection = connection / np.linalg.norm(connection) * scale
        directions[0] = connection
        directions[1] = connection
        post = positions[2] - positions[0]
        normal = np.cross(post, connection)
        normal /= np.linalg.norm(normal)
        normals[0] = normal
        normals[1] = normal

        # the last point pair
        connection = positions[-1] - positions[-2]
        connection = connection / np.linalg.norm(connection) * scale
        directions[-2] = connection
        directions[-1] = connection
        pre = positions[-4] - positions[-2]
        normal = np.cross(connection, pre)
        normal /= np.linalg.norm(normal)
        normals[-2] = normal
        normals[-1] = normal

        # all point pairs in between
        for i in range(2, self.nr_points - 2, 2):
            connection = positions[i+1] - positions[i]
            connection = connection / np.linalg.norm(connection) * scale
            directions[i] = connection
            directions[i+1] = connection
            pre = positions[i-2] - positions[i]
            post = positions[i+2] - positions[i]
            pre_normal = np.cross(connection, pre)
            post_normal = np.cross(post, connection)
            avg_normal = np.mean(np.array([pre_normal, post_normal]), axis=0)
            avg_normal /= np.linalg.norm(avg_normal)
            normals[i] = avg_normal
            normals[i+1] = avg_normal

        # generate buffers
        # ----------------------------------------
        # interweave vertex data
        vertices = np.zeros(self.nr_points, [("position",   np.float32, 3),
                                             ("normal",     np.float32, 3),
                                             ("direction",  np.float32, 3),
                                             ("color",      np.float32, 3),
                                             ("phi",        np.float32),
                                             ("L",          np.float32),
                                             ("displ_base", np.float32),
                                             ("displ_tar",  np.float32)
                                             ])
        vertices["position"] = positions
        vertices["normal"] = normals
        vertices["direction"] = directions
        vertices["color"] = colors
        vertices["phi"] = phi
        vertices["L"] = L
        vertices["displ_base"] = displ_base
        vertices["displ_tar"] = displ_tar

        gl.glBindVertexArray(self.VAO_surface)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.VBO_surface)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices.nbytes, vertices, gl.GL_STATIC_DRAW)

        # "position"
        stride = vertices.strides[0]
        offset = ctypes.c_void_p(0)
        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, stride, offset)
        # "normal"
        offset = ctypes.c_void_p(vertices.dtype["position"].itemsize)
        gl.glEnableVertexAttribArray(1)
        gl.glVertexAttribPointer(1, 3, gl.GL_FLOAT, gl.GL_FALSE, stride, offset)
        # "direction"
        offset = ctypes.c_void_p(vertices.dtype["position"].itemsize 
                               + vertices.dtype["normal"].itemsize)
        gl.glEnableVertexAttribArray(2)
        gl.glVertexAttribPointer(2, 3, gl.GL_FLOAT, gl.GL_FALSE, stride, offset)
        # "color"
        offset = ctypes.c_void_p(vertices.dtype["position"].itemsize 
                               + vertices.dtype["normal"].itemsize
                               + vertices.dtype["direction"].itemsize)
        gl.glEnableVertexAttribArray(3)
        gl.glVertexAttribPointer(3, 3, gl.GL_FLOAT, gl.GL_FALSE, stride, offset)
        # "phi"
        offset = ctypes.c_void_p(vertices.dtype["position"].itemsize 
                               + vertices.dtype["normal"].itemsize
                               + vertices.dtype["direction"].itemsize
                               + vertices.dtype["color"].itemsize)
        gl.glEnableVertexAttribArray(4)
        gl.glVertexAttribPointer(4, 1, gl.GL_FLOAT, gl.GL_FALSE, stride, offset)
        # "L"
        offset = ctypes.c_void_p(vertices.dtype["position"].itemsize 
                               + vertices.dtype["normal"].itemsize
                               + vertices.dtype["direction"].itemsize
                               + vertices.dtype["color"].itemsize
                               + vertices.dtype["phi"].itemsize)
        gl.glEnableVertexAttribArray(5)
        gl.glVertexAttribPointer(5, 1, gl.GL_FLOAT, gl.GL_FALSE, stride, offset)
        # "displ_base"
        offset = ctypes.c_void_p(vertices.dtype["position"].itemsize 
                               + vertices.dtype["normal"].itemsize
                               + vertices.dtype["direction"].itemsize
                               + vertices.dtype["color"].itemsize
                               + vertices.dtype["phi"].itemsize
                               + vertices.dtype["L"].itemsize)
        gl.glEnableVertexAttribArray(6)
        gl.glVertexAttribPointer(6, 1, gl.GL_FLOAT, gl.GL_FALSE, stride, offset)
        # "displ_tar"
        offset = ctypes.c_void_p(vertices.dtype["position"].itemsize 
                               + vertices.dtype["normal"].itemsize
                               + vertices.dtype["direction"].itemsize
                               + vertices.dtype["color"].itemsize
                               + vertices.dtype["phi"].itemsize
                               + vertices.dtype["L"].itemsize
                               + vertices.dtype["displ_base"].itemsize)
        gl.glEnableVertexAttribArray(7)
        gl.glVertexAttribPointer(7, 1, gl.GL_FLOAT, gl.GL_FALSE, stride, offset)

        gl.glBindVertexArray(0)

    def registerPlotItems(self, scatter, scatter_t, scatter_preview, line_phi, line_l):
        # necessary for dataset updates
        self.scatterplot_l_phi = scatter
        self.scatterplot_l_phi_time = scatter_t
        self.scatterplot_l_phi_preview = scatter_preview
        self.lineplot_phi = line_phi
        self.lineplot_l = line_l

    def registerCheckboxLayout(self, layout):
        self.checkboxLayout = layout

    def setVisibility(self, status):
        if status:
            self.visible = True
        else:
            self.visible = False

    def initiateDelete(self):
        self.to_be_deleted = True
        gl.glBindVertexArray(0)
        gl.glDeleteBuffers(2, [self.VBO_parameters, self.VBO_surface])
        gl.glDeleteVertexArrays(3, [self.VAO_shaft, self.VAO_tip, self.VAO_surface])
