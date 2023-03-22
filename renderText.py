from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from PIL import ImageFont, ImageDraw, Image
import numpy as np
from texture import Texture, Textured
import core 
from quad import Quad



class RenderText(Quad):
    """ Simple first textured object """
    def __init__(self, text, font_path, size, shader):
    
        #load font
        font = ImageFont.truetype(font_path, size)
        
        #Create a PIL image with the text
        text_image = Image.new('RGBA', (512,512),(0,0,0,0))
        draw = ImageDraw.Draw(text_image)
        draw.text((10, 25), text, font=font)
        
        base_coords = ((-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0))
        indices = np.array((1, 3, 0, 1 , 2 , 3), np.uint32)
        texcoords = ([0,0], [1, 0], [1, 1], [0, 1])
        mesh = core.Mesh(shader, attributes=dict(position=base_coords, tex_coord=texcoords), index=indices)

        #Create OpenGL texture
        texture = Texture(text_image, GL_MIRRORED_REPEAT, *(GL_LINEAR, GL_LINEAR_MIPMAP_LINEAR))
        super().__init__(texture, mesh)


    
    
    
    
    