#!/usr/bin/env python3
import OpenGL.GL as GL              # standard Python OpenGL wrapper
import numpy as np                  # all matrix manipulations & OpenGL args
import core
from texture import Texture, WaterTextured
from transform import normalized


# -------------- Terrain ---------------------------------
class Lava(WaterTextured):
    """ Simple first textured object """
    def __init__(self, shader, map_width, map_height, noisemap_file, dudv_file, normal_file):

        LAVA_HEIGHT = 16
        #rajouter des sommmets dans base coord si besoin d'1 truc + rond
        base_coords = np.array([[-1, 0, -1], [1, 0, -1], [1, 0, 1], [-1, 0, 1]])
        scaled_coords = base_coords
        scaled_coords[:,0] = base_coords[:,0] * (map_width/2)
        scaled_coords[:,1] = base_coords[:,1] + LAVA_HEIGHT
        scaled_coords[:,2] = base_coords[:,2] * (map_height/2)
        indices = np.array((1, 0, 3, 1 , 3 , 2), np.uint32)
        texcoords = ([0,0], [1, 0], [1, 1], [0, 1])
        # setup plane mesh to be textured
        mesh = core.Mesh(shader, attributes=dict(position=scaled_coords, tex_coord=texcoords), index=indices, k_a=(0.1,0.1,0.1), k_d=(0.4,0.4,0.4), k_s=(1.0,0.9,0.5), s=2)

        #charger la noisemap
        noisemap_tex = Texture(noisemap_file, GL.GL_MIRRORED_REPEAT, *(GL.GL_LINEAR, GL.GL_LINEAR_MIPMAP_LINEAR), gamma_correction=False)
        dudv_tex = Texture(dudv_file, GL.GL_MIRRORED_REPEAT, *(GL.GL_LINEAR, GL.GL_LINEAR_MIPMAP_LINEAR), gamma_correction=False)
        normal_tex = Texture(normal_file, GL.GL_MIRRORED_REPEAT, *(GL.GL_LINEAR, GL.GL_LINEAR_MIPMAP_LINEAR), gamma_correction=False)
        super().__init__(mesh, noise_map=noisemap_tex, dudv_map=dudv_tex, normal_map=normal_tex)

