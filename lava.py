#!/usr/bin/env python3
import OpenGL.GL as GL              # standard Python OpenGL wrapper
import numpy as np                  # all matrix manipulations & OpenGL args
import core
from texture import Texture, WaterTextured


# -------------- Terrain ---------------------------------
class Lava(WaterTextured):
    """ Simple first textured object """
    def __init__(self, shader, map_width, map_height, noisemap_file, dudv_file, normal_file):

        LAVA_HEIGHT = 16
        # Add more vertices to make a pentagon
        num_vertices = 10
        radius = 1

        base_coords = []

        for i in range(num_vertices):
            angle = 2 * np.pi * i / num_vertices
            x = radius * np.cos(angle)
            y = 0
            z = radius * np.sin(angle)
            base_coords.append([x, y, z])

        base_coords = np.array(base_coords)
        scaled_coords = base_coords
        scaled_coords[:, 0] = base_coords[:, 0] * (map_width / 2)
        scaled_coords[:, 1] = base_coords[:, 1] + LAVA_HEIGHT
        scaled_coords[:, 2] = base_coords[:, 2] * (map_height / 2)

        indices = []
        for i in range(1, num_vertices - 1):
            indices.extend([0, i+1, i ])

        indices = np.array(indices, np.uint32)
       
        texcoords = []
        for i in range(num_vertices):
            angle = 2 * np.pi * i / num_vertices
            u = 0.5 * (1 + np.cos(angle))
            v = 0.5 * (1 + np.sin(angle))
            texcoords.append([u, v])
        # print("indices : ",indices)
        # print("textcoords : ",texcoords)
        # print("base_coords : ",base_coords)
        
        
        
        # setup plane mesh to be textured   
        mesh = core.Mesh(shader, attributes=dict(position=scaled_coords, tex_coord=texcoords), index=indices, k_a=(0.1,0.1,0.1), k_d=(0.4,0.4,0.4), k_s=(1.0,0.9,0.5), s=2)
        
        
        #charger la noisemap
        noisemap_tex = Texture(noisemap_file, GL.GL_MIRRORED_REPEAT, *(GL.GL_LINEAR, GL.GL_LINEAR_MIPMAP_LINEAR), gamma_correction=False)
        dudv_tex = Texture(dudv_file, GL.GL_MIRRORED_REPEAT, *(GL.GL_LINEAR, GL.GL_LINEAR_MIPMAP_LINEAR), gamma_correction=False)
        normal_tex = Texture(normal_file, GL.GL_MIRRORED_REPEAT, *(GL.GL_LINEAR, GL.GL_LINEAR_MIPMAP_LINEAR), gamma_correction=False)
        super().__init__(mesh, noise_map=noisemap_tex, dudv_map=dudv_tex, normal_map=normal_tex)

