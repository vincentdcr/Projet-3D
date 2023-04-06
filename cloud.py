#!/usr/bin/env python3            # standard Python OpenGL wrapper
import numpy as np                  # all matrix manipulations & OpenGL args
import core
from texture import Texture, Textured
from transform import normalized
from PIL import Image
from waterFrameBuffer import WaterFrameBuffers
import random
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import noise

# -------------- Terrain ---------------------------------

# créer shader .frag .vert -> reprendre water.vert
# classe noise avec un get qui renvoie l'image faire un champ avec l'image 
# dans core 3eme draw ajouter speed = sin

class Cloud(Textured):
    """ Simple first textured object """
    
    
    def __init__(self, shader, map_width, map_height, noise_map):
        CLOUD_HEIGHT = 50

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
        

        
    
    
    
# def DrawGLScene():
#     global map256

#     glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
#     glLoadIdentity()

#     LoopForever() #Our cloud function

#     texture = np.zeros((256, 256, 3), dtype=np.uint8) #Temporary array to hold texture RGB values

#     for i in range(256):
#         for j in range(256):
#             color = map256[i*256+j]
#             texture[j, 0] = color
#             texture[j, 1] = color
#             texture[j, 2] = color

#     ID = glGenTextures(1) #Generate an ID for texture binding
#     glBindTexture(GL_TEXTURE_2D, ID) #Texture binding

#     glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
#     glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
#     glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
#     glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    
#     gluBuild2DMipmaps(GL_TEXTURE_2D, GL_RGB, 256, 256, GL_RGB, GL_UNSIGNED_BYTE, texture)

#     glMatrixMode(GL_TEXTURE) #Let's move the clouds from left to right
#     x = 0.0
#     x += 0.01
#     glTranslatef(x, 0, 0)

#     glEnable(GL_TEXTURE_2D) #Render the cloud texture
#     glBegin(GL_QUADS)
#     glTexCoord2d(1,1); glVertex3f(0.5, 0.5, 0.)
#     glTexCoord2d(0,1); glVertex3f(-0.5, 0.5, 0.)
#     glTexCoord2d(0,0); glVertex3f(-0.5, -0.5, 0.)
#     glTexCoord2d(1,0); glVertex3f(0.5, -0.5, 0.)
#     glEnd()

#     glutSwapBuffers()