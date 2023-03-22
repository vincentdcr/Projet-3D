from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from PIL import ImageFont, ImageDraw, Image
import numpy as np


def render_text(text, font_path, size, x, y, color):
    
    #load font
    font = ImageFont.truetype(font_path, size)
    
    #Create a PIL image with the text
    text_image = Image.new('RGBA', (512,512),(0,0,0,0))
    draw = ImageDraw.Draw(text_image)
    draw.text((10, 25), text, font=font)
    text_image.save("textrender/test.png", "PNG")
    
    # COnvert PIL image to numpy array
    np_image = np.array(text_image )
    
    #Create OpenGL texture
    texture_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 512, 512, 0, GL_RGBA, GL_UNSIGNED_BYTE, np_image)
    
    # Render texture as quad
    #glEnable(GL_TEXTURE_2D)
    #glColor3f(1.0, 1.0, 1.0)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glBegin(GL_QUADS)
    glTexCoord2f(0.0, 0.0)
    glVertex2f(x,y)
    glTexCoord2f(1.0, 0.0)
    glVertex2f(x +font.getsize(text)[0],y)
    glTexCoord2f(1.0, 1.0)
    glVertex2f(x +font.getsize(text)[0],y +font.getsize(text)[1])
    glTexCoord2f(0.0, 1.0)
    glVertex2f(x ,y+font.getsize(text)[1])
    
    #Clean up
    glDeleteTextures([texture_id])
    
    
    
    
    