import sys
from itertools import cycle
import OpenGL.GL as GL              # standard Python OpenGL wrapper
import glfw                         # lean window system wrapper for OpenGL
import numpy as np                  # all matrix manipulations & OpenGL args
from core import Shader, Viewer, Mesh, load, Node
from texture import Texture, Textured, CubeMapTex, TexturedCube
from terrain import Terrain
from transform import translate, vec, quaternion
from animation import KeyFrameControlNode

class Grass_blade(Textured):
    # create a thin triangle with a texture grass.png
    def __init__(self, shader, tex_path):
        self.file = tex_path
        #setup triangle mesh to be textured
        base_coords = ((-0.025, 0, 0), (0.025, 0, 0), (0, 0.1, 0))
        tex_coords = ((0,0),(1,0),(0.5,1))
        
        mesh = Mesh(shader, attributes=dict(position=base_coords), texcoord =tex_coords)        
        texture = Texture(tex_path, GL.GL_REPEAT, *(GL.GL_NEAREST, GL.GL_NEAREST_MIPMAP_LINEAR))
        super().__init__(mesh, diffuse_map=texture)
        GL.glEnable(GL.GL_CULL_FACE)

class Grass_field():
    #use GPU instancing to create a field on grass, each grass is made by Grass_blade
    def __init__(self, shader, tex_path, nb_grass):
        self.nb_grass = nb_grass
        self.grass = Grass_blade(shader, tex_path)
        self.grass.mesh.add_instance()
        
    