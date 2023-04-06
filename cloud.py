#!/usr/bin/env python3            # standard Python OpenGL wrapper
import numpy as np                  # all matrix manipulations & OpenGL args
import core
from texture import Textured
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

# -------------- Terrain ---------------------------------

# créer shader .frag .vert -> reprendre water.vert
# classe noise avec un get qui renvoie l'image faire un champ avec l'image 
# dans core 3eme draw ajouter speed = sin

class Cloud(Textured):
    """ Simple first textured object """
    
    
    def __init__(self, shader, map_width, map_height, noise_map):
        CLOUD_HEIGHT = 60

        base_coords = np.array([[-1, 0, -1], [1, 0, -1], [1, 0, 1], [-1, 0, 1]])
        scaled_coords = base_coords
        scaled_coords[:,0] = base_coords[:,0] * (map_width/2)
        scaled_coords[:,1] = base_coords[:,1] + CLOUD_HEIGHT
        scaled_coords[:,2] = base_coords[:,2] * (map_height/2)
        indices = np.array((1, 0, 3, 1 , 3 , 2), np.uint32)
        texcoords = ([0,0], [1, 0], [1, 1], [0, 1])
        # setup plane mesh to be textured
        mesh = core.Mesh(shader, attributes=dict(position=scaled_coords, tex_coord=texcoords), index=indices, k_a=(0.6,0.6,0.6), k_d=(0.2,0.2,0.2), k_s=(0.9,0.9,1.0), s=20)
        super().__init__(mesh, cloud_map=noise_map)