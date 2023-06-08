# -----------------------------------------------------------------------------
# Copyright (c) 2021 Pepe Eulzer. All rights reserved.
# Distributed under the (new) BSD License.
# -----------------------------------------------------------------------------

import sys
import os
import numpy as np

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

# initial window size
WINDOW_SIZE_X = 1920 #1280
WINDOW_SIZE_Y = 1080 #720

# write out usage log?
WRITE_LOG = False

# default settings if not provided in settings.txt
settings = {'time_start':0.0,
            'time_end':5.0,
            'models_scale':1.0,
            'glyphs_scale':1.0,
            'outline_width':3.0}

# initial data folder
INITIAL_FOLDER = "Example1"

# initial glyph properties
INITIAL_THICKNESS = 0.5
INITIAL_LENGTH = 4.0
INITIAL_OFFSET = 0.0

# scatter plot properties
SCATTER_POINT_SIZE = 3.5

# colormap for time values (will be interpolated)
TIME_COLORS = np.array([[255,255,204],
                        [161,218,180],
                        [ 65,182,196],
                        [ 44,127,184],
                        [ 37, 52,148]])

# color of bones
REFERENCE_COLOR = [0.89, 0.85, 0.79] 

# color when picking objects
SELECT_COLOR = [1.0, 1.0, 0.5]

# colors to identify correspondences
CORR_COLORS = np.array([[27,158,119],
                        [217,95,2],
                        [117,112,179],
                        [231,41,138],
                        [102,166,30],
                        [230,171,2],
                        [166,118,29],
                        [102,102,102]])
# normalized version
CORR_COLORS_NORM = CORR_COLORS / 255.0

# where the glyph geometry is stored
GLYPH_PATH_SHAFT = resource_path("models_glyphs/arrow_shaft.obj")
GLYPH_PATH_TIP = resource_path("models_glyphs/arrow_tip.obj")

# tooltips for selecting objects
FHA_WORLD_TOOLTIPS = ["Select the target object.\nFHA will be relative to the world system."]
FHA_BASE_TOOLTIPS =  ["Select the base object\nFHA will be relative to this system.",
                      "Select the target object."]
RHA_TOOLTIPS =       ["Select the first object.\nRHA will use this as the start.",
                      "Select the second object.\nRHA will use this as the end."]

# style for graph labels
LABEL_STYLE = {}# {'font-size':'10pt'}