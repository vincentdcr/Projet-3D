import OpenGL.GL as GL              # standard Python OpenGL wrapper
from texture import Texture, Textured
import numpy as np 

class Quad(Textured):
    """ Simple first textured object """
    def __init__(self, tex, mesh):
        super().__init__(mesh, diffuse_map=tex) 