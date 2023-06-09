import OpenGL.GL as GL              # standard Python OpenGL wrapper
from PIL import Image               # load texture maps
import os
import core
import numpy as np
from transform import calc_normals

# -------------- OpenGL Texture Wrapper ---------------------------------------
class Texture:
    """ Helper class to create and automatically destroy textures """
    def __init__(self, tex_file, wrap_mode=GL.GL_REPEAT,
                 mag_filter=GL.GL_LINEAR, min_filter=GL.GL_LINEAR_MIPMAP_LINEAR,
                 tex_type=GL.GL_TEXTURE_2D, gamma_correction=True):
        self.glid = GL.glGenTextures(1)
        self.type = tex_type
        try:
            # imports image as a numpy array in exactly right format
            if(isinstance(tex_file,Image.Image)):
                tex = tex_file
            elif (isinstance(tex_file, np.ndarray)):
                tex = Image.fromarray(tex_file)
            else :
                tex = Image.open(tex_file).convert('RGBA')
            GL.glBindTexture(tex_type, self.glid)
            if(gamma_correction):
                GL.glTexImage2D(tex_type, 0, GL.GL_SRGB_ALPHA, tex.width, tex.height,
                            0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, tex.tobytes())
            else:
                GL.glTexImage2D(tex_type, 0, GL.GL_RGBA, tex.width, tex.height,
                            0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, tex.tobytes())
            GL.glTexParameteri(tex_type, GL.GL_TEXTURE_WRAP_S, wrap_mode)
            GL.glTexParameteri(tex_type, GL.GL_TEXTURE_WRAP_T, wrap_mode)
            GL.glTexParameteri(tex_type, GL.GL_TEXTURE_MIN_FILTER, min_filter)
            GL.glTexParameteri(tex_type, GL.GL_TEXTURE_MAG_FILTER, mag_filter)
            GL.glGenerateMipmap(tex_type)
            if (not isinstance(tex_file, np.ndarray)):
                print(f'Loaded texture {tex_file} ({tex.width}x{tex.height}'
                  f' wrap={str(wrap_mode).split()[0]}'
                  f' min={str(min_filter).split()[0]}'
                  f' mag={str(mag_filter).split()[0]})')
        except FileNotFoundError:
            print("ERROR: unable to load texture file %s" % tex_file)

    def __del__(self):  # delete GL texture from GPU when object dies
        GL.glDeleteTextures(self.glid)

class TextureArray:
    """ Helper class to create and automatically destroy textures """
    def __init__(self, tex_files, files_height, files_width, wrap_mode=GL.GL_REPEAT,
                 mag_filter=GL.GL_LINEAR, min_filter=GL.GL_LINEAR_MIPMAP_LINEAR, gamma_correction=True):
        self.type = GL.GL_TEXTURE_2D_ARRAY
        self.glid = GL.glGenTextures(1)
        try:
            GL.glBindTexture(GL.GL_TEXTURE_2D_ARRAY, self.glid)
            if gamma_correction : 
                color_coding1 = GL.GL_SRGB8_ALPHA8
                color_coding2 = GL.GL_RGBA
            else : 
                color_coding1 = GL.GL_RGBA8
                color_coding2 = GL.GL_RGBA
            GL.glTexStorage3D(GL.GL_TEXTURE_2D_ARRAY, 10, color_coding1, files_width, files_height, len(tex_files))
            for i in range(len(tex_files)):
                    tex = Image.open(tex_files[i]).convert('RGBA')
                    GL.glTexSubImage3D(GL.GL_TEXTURE_2D_ARRAY, 0, 0, 0, i, files_width, files_height, 1, color_coding2, GL.GL_UNSIGNED_BYTE, tex.tobytes())
            GL.glTexParameteri(GL.GL_TEXTURE_2D_ARRAY, GL.GL_TEXTURE_WRAP_S, wrap_mode)
            GL.glTexParameteri(GL.GL_TEXTURE_2D_ARRAY, GL.GL_TEXTURE_WRAP_T, wrap_mode)
            GL.glTexParameteri(GL.GL_TEXTURE_2D_ARRAY, GL.GL_TEXTURE_MIN_FILTER, min_filter)
            GL.glTexParameteri(GL.GL_TEXTURE_2D_ARRAY, GL.GL_TEXTURE_MAG_FILTER, mag_filter)
            GL.glGenerateMipmap(GL.GL_TEXTURE_2D_ARRAY)
            print(f'Loaded texture array containing {tex_files[0]} ({files_width}x{files_height}'
                  f' wrap={str(wrap_mode).split()[0]}'
                  f' min={str(min_filter).split()[0]}'
                  f' mag={str(mag_filter).split()[0]})')
        except FileNotFoundError:
            print("ERROR: unable to load texture array containing file %s" % tex_files[0])

    def __del__(self):  # delete GL texture from GPU when object dies
        GL.glDeleteTextures(self.glid)


class CubeMapTex:
    """ Helper class to create and automatically destroy textures """
    def __init__(self, tex_path):
        self.glid = GL.glGenTextures(1)
        self.type = GL.GL_TEXTURE_CUBE_MAP
        try:
            i=0
            for filename in sorted(os.listdir(tex_path)):
                tex_file = os.path.join(tex_path, filename)
                # checking if it is a file
                if os.path.isfile(tex_file):
                    # imports image as a numpy array in exactly right format
                    tex = Image.open(tex_file).convert('RGBA')
                    GL.glBindTexture(self.type, self.glid)
                    GL.glTexImage2D(GL.GL_TEXTURE_CUBE_MAP_POSITIVE_X + i, 0, GL.GL_SRGB_ALPHA, tex.width, tex.height,
                                    0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, tex.tobytes())
                    GL.glTexParameteri(GL.GL_TEXTURE_CUBE_MAP, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
                    GL.glTexParameteri(GL.GL_TEXTURE_CUBE_MAP, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
                    GL.glTexParameteri(GL.GL_TEXTURE_CUBE_MAP, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE)
                    GL.glTexParameteri(GL.GL_TEXTURE_CUBE_MAP, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE)
                    GL.glTexParameteri(GL.GL_TEXTURE_CUBE_MAP, GL.GL_TEXTURE_WRAP_R, GL.GL_CLAMP_TO_EDGE)
                    print(f'Loaded texture {tex_file} ({tex.width}x{tex.height}')

                    i+=1
        except FileNotFoundError:
            print("ERROR: unable to load texture file %s" % tex_file)

    def __del__(self):  # delete GL texture from GPU when object dies
        GL.glDeleteTextures(self.glid)


# -------------- Textured mesh decorator --------------------------------------
class Textured:
    """ Drawable mesh decorator that activates and binds OpenGL textures """
    def __init__(self, drawable, **textures):
        self.drawable = drawable
        self.textures = textures

    def draw(self, primitives=GL.GL_TRIANGLES, **uniforms):
        for index, (name, texture) in enumerate(self.textures.items()):
            GL.glActiveTexture(GL.GL_TEXTURE0 + index)
            if(isinstance(texture, np.uint32) ): #for self generated texture from FBOS
                GL.glBindTexture(GL.GL_TEXTURE_2D, texture)
            else:
                GL.glBindTexture(texture.type, texture.glid)
            uniforms[name] = index
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        self.drawable.draw(primitives=primitives, **uniforms)
        GL.glDisable(GL.GL_BLEND)

class TexturedCube:
    """ Drawable mesh decorator that activates and binds OpenGL textures """
    def __init__(self, drawable, **textures):
        self.drawable = drawable 
        self.textures = textures

    def draw(self, primitives=GL.GL_TRIANGLES, **uniforms):
        GL.glDepthFunc(GL.GL_LEQUAL);  # change depth function so depth test passes when values are equal to depth buffer's content
        for index, (name, texture) in enumerate(self.textures.items()):
            GL.glActiveTexture(GL.GL_TEXTURE0 + index)
            GL.glBindTexture(texture.type, texture.glid)
            uniforms[name] = index
        self.drawable.draw(primitives=primitives, **uniforms)
        GL.glDepthFunc(GL.GL_LESS); # set depth function back to default

class WaterTextured:
    """ Drawable mesh decorator that activates and binds OpenGL textures """
    def __init__(self, drawable, **textures):
        self.drawable = drawable
        self.textures = textures

    def draw(self, primitives=GL.GL_TRIANGLES, **uniforms):
        for index, (name, texture) in enumerate(self.textures.items()):
            GL.glActiveTexture(GL.GL_TEXTURE0 + index)
            if(isinstance(texture, np.uint32)): #for self generated texture from FBOS
                GL.glBindTexture(GL.GL_TEXTURE_2D, texture)
            else:
                GL.glBindTexture(texture.type, texture.glid)
            uniforms[name] = index
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        self.drawable.draw(primitives=primitives, **uniforms)
        GL.glDisable(GL.GL_BLEND)
        
