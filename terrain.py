#!/usr/bin/env python3
import OpenGL.GL as GL              # standard Python OpenGL wrapper
import numpy as np                  # all matrix manipulations & OpenGL args
from core import  Mesh
from texture import Texture, Textured


# -------------- Terrain ---------------------------------
class Terrain(Textured):
    """ Simple first textured object """
    def __init__(self, shader, tex_file, map_width, map_height):
        self.file = tex_file

        noise_map = generate_noise_map(map_width, map_height)
        vertices = generate_vertices(map_width, map_height, noise_map)
        indices = generate_indices(map_width, map_height)
        texcoords = generate_texcoords(map_width, map_height)
        normals = generate_normals(map_width, map_height, vertices) 
        # setup plane mesh to be textured
        mesh = Mesh(shader, attributes=dict(position=vertices, tex_coord=texcoords, normal=normals), index=indices )

        # setup & upload texture to GPU, bind it to shader name 'diffuse_map'
        texture = Texture(tex_file, GL.GL_MIRRORED_REPEAT, *(GL.GL_LINEAR, GL.GL_LINEAR_MIPMAP_LINEAR))
        super().__init__(mesh, diffuse_map=texture)


def generate_noise_map(width, height):
    noise_map = []
    
    for z in range(0,height): 
        for x in range(0,width):
            noise_map.append(0)
    return noise_map


def generate_vertices(width, height, noise_map): 
    v = []
    for z in range(0,height): 
        for x in range(0,width):
            v.append((x, noise_map[x + z*width], z))   
    return np.asarray(v)

def generate_indices(width, height):
    indices = []
    
    for z in range(0,height): 
        for x in range(0,width):
            pos = x + z*width
            
            if (x == width - 1 or z == height - 1):
                # Don't create indices for right or top edge
                continue
            else:
                # Top left triangle of square
                indices.append(pos)
                indices.append(pos + width)
                indices.append(pos + width + 1)
                # Bottom right triangle of square
                indices.append(pos + 1 + width)
                indices.append(pos + 1)
                indices.append(pos)
    return np.asarray(indices)

def generate_texcoords(width, height):
    texcoords = []
    i = 0
    j = 0
    for z in range(0,height): 
        for x in range(0,width):
            texcoords.append((i,j))
            j = (j + 1) % 2 
        i = (i + 1) % 2
    return np.asarray(texcoords)

def generate_normals(width, height, position):

    normals = np.full((width*height, 3), fill_value=np.array([0,6,0]))
    for z in range(1,height-1): 
        for x in range(1,width-1):
            Yu       = position[x + (z+1)*width][1]
            Yur = position[x+1 + (z+1)*width][1]
            Yr = position[x+1 + z*width][1]
            Yd = position[x + (z-1)*width][1]
            Ydl = position[x-1 + (z-1)*width][1]
            Yl = position[x-1 + z][1]
            normal = np.array([  (2*(Yl - Yr) - Yur + Ydl + Yu - Yd), 6, (2*(Yd - Yu) + Yur + Ydl - Yu - Yl)  ])
            normals[x+z*width] = normal
    return normals # Normalization ??

