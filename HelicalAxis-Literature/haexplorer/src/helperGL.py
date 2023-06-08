# -----------------------------------------------------------------------------
# Copyright (c) 2021 Pepe Eulzer. All rights reserved.
# Distributed under the (new) BSD License.
# -----------------------------------------------------------------------------

import ctypes

import numpy as np
import igl
import OpenGL.GL as gl

def read_shader(path):
    """
    Reads a textfile into a single string.
    """
    text = None
    with open(path, 'r') as file:
        text = file.read()
    return text

def obj_to_VAO(model_path):
    """
    Converts a .obj to a VAO with EBO for use with OpenGL.
    The VAO contains position and normal attributes. Uses igl for loading.
    """
    # load geometry
    # ----------------------------------------
    # read obj
    positions, _, normals, faces, _, _ = igl.read_obj(model_path)
    EBO_size = faces.size
    if len(normals) != len(positions):
        normals = igl.per_vertex_normals(positions, faces, igl.PER_VERTEX_NORMALS_WEIGHTING_TYPE_ANGLE)

    # interweave vertex data
    size = int(positions.size/3)
    vertices = np.zeros(size, [("position", np.float32, 3),
                                ("normal",   np.float32, 3)])
    vertices["position"] = positions
    vertices["normal"] = normals

    # generate buffers
    # ----------------------------------------
    VAO = gl.glGenVertexArrays(1)
    VBO = gl.glGenBuffers(1)
    EBO = gl.glGenBuffers(1)

    gl.glBindVertexArray(VAO)
    
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, VBO)
    gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices.nbytes, vertices, gl.GL_STATIC_DRAW)
    gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, EBO)
    gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, faces.nbytes, faces, gl.GL_STATIC_DRAW)
    # "position"
    stride = vertices.strides[0]
    offset = ctypes.c_void_p(0)
    gl.glEnableVertexAttribArray(0)
    gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, stride, offset)
    # "normal"
    offset = ctypes.c_void_p(vertices.dtype["position"].itemsize)
    gl.glEnableVertexAttribArray(1)
    gl.glVertexAttribPointer(1, 3, gl.GL_FLOAT, gl.GL_FALSE, stride, offset)

    gl.glBindVertexArray(0)

    return VAO, EBO_size

def colormapRGB(colors, sample_count):
    """
    Returns a colormap with sample_count RGB values,
    linearly interpolating equidistantly spaced RGB points.
    The colormap can, for example, be used as a VBO.
    Parameters:
     * colors: numpy array of the form [[R1,G1,B1], [R2,G2,B2], ...]
       The RGB values are expected in [0.0, 255.0]
     * sample_count: length of the colormap to return
    """
    r = colors[:,0] / 255.0
    g = colors[:,1] / 255.0
    b = colors[:,2] / 255.0
    x_axis = np.arange(len(r))
    x_samples = np.linspace(0, len(r)-1, sample_count)

    colormap = np.zeros((sample_count,3), dtype=np.float32)
    colormap[:,0] = np.interp(x_samples, x_axis, r)
    colormap[:,1] = np.interp(x_samples, x_axis, g)
    colormap[:,2] = np.interp(x_samples, x_axis, b)

    return colormap