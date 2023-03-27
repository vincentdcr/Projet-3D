import OpenGL.GL as GL              # standard Python OpenGL wrapper
from PIL import Image               # load texture maps
import os
import core
import numpy as np

def calcNormals(vertices, index):
    normals = np.zeros(vertices.shape, dtype=vertices.dtype)

    for i in range(0, len(index), 3):
        a = vertices[index[i]]
        b = vertices[index[i + 1]]
        c = vertices[index[i + 2]]

        normal = np.cross(b - a, c - a)
        normal = normal / np.linalg.norm(normal)

        normals[index[i]] += normal
        normals[index[i + 1]] += normal
        normals[index[i + 2]] += normal

    for i in range(len(normals)):
        normals[i] = normals[i] / np.linalg.norm(normals[i])

    return normals, vertices, index

# -------------- OpenGL Texture Wrapper ---------------------------------------
class Texture:
    """ Helper class to create and automatically destroy textures """
    def __init__(self, tex_file, wrap_mode=GL.GL_REPEAT,
                 mag_filter=GL.GL_LINEAR, min_filter=GL.GL_LINEAR_MIPMAP_LINEAR,
                 tex_type=GL.GL_TEXTURE_2D):
        self.glid = GL.glGenTextures(1)
        self.type = tex_type
        try:
            # imports image as a numpy array in exactly right format
            if(isinstance(tex_file,Image.Image)):
                tex = tex_file
            else:
                tex = Image.open(tex_file).convert('RGBA')
            GL.glBindTexture(tex_type, self.glid)
            GL.glTexImage2D(tex_type, 0, GL.GL_RGBA, tex.width, tex.height,
                            0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, tex.tobytes())
            GL.glTexParameteri(tex_type, GL.GL_TEXTURE_WRAP_S, wrap_mode)
            GL.glTexParameteri(tex_type, GL.GL_TEXTURE_WRAP_T, wrap_mode)
            GL.glTexParameteri(tex_type, GL.GL_TEXTURE_MIN_FILTER, min_filter)
            GL.glTexParameteri(tex_type, GL.GL_TEXTURE_MAG_FILTER, mag_filter)
            GL.glGenerateMipmap(tex_type)
            print(f'Loaded texture {tex_file} ({tex.width}x{tex.height}'
                  f' wrap={str(wrap_mode).split()[0]}'
                  f' min={str(min_filter).split()[0]}'
                  f' mag={str(mag_filter).split()[0]})')
        except FileNotFoundError:
            print("ERROR: unable to load texture file %s" % tex_file)

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
                    GL.glTexImage2D(GL.GL_TEXTURE_CUBE_MAP_POSITIVE_X + i, 0, GL.GL_RGBA, tex.width, tex.height,
                                    0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, tex.tobytes())
                    GL.glTexParameteri(GL.GL_TEXTURE_CUBE_MAP, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR);
                    GL.glTexParameteri(GL.GL_TEXTURE_CUBE_MAP, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR);
                    GL.glTexParameteri(GL.GL_TEXTURE_CUBE_MAP, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE);
                    GL.glTexParameteri(GL.GL_TEXTURE_CUBE_MAP, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE);
                    GL.glTexParameteri(GL.GL_TEXTURE_CUBE_MAP, GL.GL_TEXTURE_WRAP_R, GL.GL_CLAMP_TO_EDGE);
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
            if(isinstance(texture, np.uint32)): #for self generated texture from FBOS
                GL.glBindTexture(GL.GL_TEXTURE_2D, texture)
            else:
                GL.glBindTexture(texture.type, texture.glid)
            uniforms[name] = index
        self.drawable.draw(primitives=primitives, **uniforms)

    
    
    
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
        

        
class TexturedCylinder(Textured):
    """ Simple first textured object """

    def __init__(self, shader, texture, height=1, divisions=50, r=0.5, position=(0, 0, 0), light_dir=None, shinyness=2):
        self.height = height
        self.divisions = divisions
        self.ray = r

        # setup plane mesh to be textured
        vertices = ()
        tex_coord = ()
        vertices = vertices + ((0, self.height, 0),)
        tex_coord += ((0, 0),)
        tex_i = 0
        # top
        for angle in np.arange(0, 2 * np.pi, 2 * np.pi / self.divisions):
            vertices = vertices + ((self.ray * np.cos(angle) , self.height, self.ray * np.sin(angle)),)
            tex_coord += ((tex_i / divisions, 0),)
            tex_i += 1
        vertices = vertices + ((0, 0, 0),)
        tex_coord += ((1, 1),)
        tex_i = 0
        #bottom
        for angle in np.arange(0, 2 * np.pi, 2 * np.pi / self.divisions):
            vertices = vertices + ((self.ray * np.cos(angle), 0, self.ray * np.sin(angle)),)
            tex_coord += ((tex_i / divisions, 1),)
            tex_i += 1
        vertices = np.array(vertices, np.float32) + np.array(position, np.float32)
        index = ()
        # top face
        for i in range(1, self.divisions, 1):
            index = index + (0, i + 1, i)
        index = index + (0, 1, self.divisions)
        # bottom face
        for i in range(1, self.divisions, 1):
            index = index + (self.divisions + 1, self.divisions + i + 1, self.divisions + i + 2)
        index = index + (self.divisions + 1, self.divisions * 2 + 1, self.divisions + 2)
        # side
        for i in range(1, self.divisions, 1):
            index = index + (i, i + 1, self.divisions + i + 1, i + 1, self.divisions + i + 2, self.divisions + i + 1)
        index = index + (self.divisions, 1, self.divisions * 2 + 1, 1, self.divisions + 2, self.divisions * 2 + 1)

        (normals, vertices, index) = calcNormals(vertices, index)
        mesh = core.Mesh(shader, attributes=dict(position=vertices, tex_coord=np.array(tex_coord), normal=normals),
                    index=index, s=shinyness, light_dir=light_dir)

        # setup & upload texture to GPU, bind it to shader name 'diffuse_map'
        super().__init__(mesh, diffuse_map=texture)

        
class TexturedTiltedCylinder(Textured):
    """ Simple first textured object """

    def __init__(self, shader, texture, height=1, divisions=50, r=0.5, position=(0, 0, 0), light_dir=None, shinyness=2, bias=0.5):
        self.height = height
        self.divisions = divisions
        self.ray = r

        # setup plane mesh to be textured
        vertices = ()
        tex_coord = ()
        vertices = vertices + ((0, self.height, 0),)
        tex_coord += ((0, 0),)
        tex_i = 0
        # top
        for angle in np.arange(0, 2 * np.pi, 2 * np.pi / self.divisions):
            vertices = vertices + (((self.ray-bias) * np.cos(angle) , self.height, (self.ray-bias) * np.sin(angle)),)
            tex_coord += ((tex_i / divisions, 0),)
            tex_i += 1
        vertices = vertices + ((0, 0, 0),)
        tex_coord += ((1, 1),)
        tex_i = 0
        #bottom
        for angle in np.arange(0, 2 * np.pi, 2 * np.pi / self.divisions):
            vertices = vertices + ((self.ray * np.cos(angle), 0, self.ray * np.sin(angle)),)
            tex_coord += ((tex_i / divisions, 1),)
            tex_i += 1
        vertices = np.array(vertices, np.float32) + np.array(position, np.float32)
        index = ()
        # top face
        for i in range(1, self.divisions, 1):
            index = index + (0, i + 1, i)
        index = index + (0, 1, self.divisions)
        # bottom face
        for i in range(1, self.divisions, 1):
            index = index + (self.divisions + 1, self.divisions + i + 1, self.divisions + i + 2)
        index = index + (self.divisions + 1, self.divisions * 2 + 1, self.divisions + 2)
        # side
        for i in range(1, self.divisions, 1):
            index = index + (i, i + 1, self.divisions + i + 1, i + 1, self.divisions + i + 2, self.divisions + i + 1)
        index = index + (self.divisions, 1, self.divisions * 2 + 1, 1, self.divisions + 2, self.divisions * 2 + 1)

        (normals, vertices, index) = calcNormals(vertices, index)
        mesh = core.Mesh(shader, attributes=dict(position=vertices, tex_coord=np.array(tex_coord), normal=normals),
                    index=index, s=shinyness, light_dir=light_dir)

        # setup & upload texture to GPU, bind it to shader name 'diffuse_map'
        super().__init__(mesh, diffuse_map=texture)

        
class Cone(Textured):
    """ Simple first textured object """

    def __init__(self, shader, texture, height=1, divisions=50, r=0.5, position=(0, 0, 0), light_dir=None, shinyness=2):
        self.height = height
        self.divisions = divisions
        self.ray = r

        # setup plane mesh to be textured
        vertices = ()
        tex_coord = ()
        vertices = vertices + ((0, self.height, 0),)
        tex_coord += ((0, 0),)
        tex_i = 0
        vertices = vertices + ((0, 0, 0),)
        tex_coord += ((1, 1),)
        tex_i = 0
        #bottom
        for angle in np.arange(0, 2 * np.pi, 2 * np.pi / self.divisions):
            vertices = vertices + ((self.ray * np.cos(angle), 0, self.ray * np.sin(angle)),)
            tex_coord += ((tex_i / divisions, 1),)
            tex_i += 1
        vertices = np.array(vertices, np.float32) + np.array(position, np.float32)
        index = ()
        # sides face
        for i in range(2, self.divisions, 1):
            index = index + (0, i + 1, i)
        index = index + (0, 2, self.divisions)
        for i in range(2, self.divisions, 1):
            index = index + (1, i , i + 1)
        index = index + (1, self.divisions, 2)
        (normals, vertices, index) = calcNormals(vertices, index)
        mesh = core.Mesh(shader, attributes=dict(position=vertices, tex_coord=np.array(tex_coord), normal=normals),
                    index=index, s=shinyness, light_dir=light_dir)

        # setup & upload texture to GPU, bind it to shader name 'diffuse_map'
        super().__init__(mesh, diffuse_map=texture)
        
class TexturedPyramid(Textured):
    def __init__(self, shader, texture, position=(0, 0, 0), size=1.0, light_dir=None, shinyness=2):
        # Define the vertices and texture coordinates for the pyramid
        vertices = np.array([
            # base
            (-0.5, 0.0, 0.5),
            (0.5, 0.0, 0.5),
            (0.5, 0.0, -0.5),
            (-0.5, 0.0, -0.5),
            # top
            (0.0, 1.0, 0.0)
        ], dtype=np.float32) * size + position

        texture_coords = np.array([
            # base
            (0, 0),
            (1, 0),
            (1, 1),
            (0, 1),
            # top
            (0.5, 1)
        ], dtype=np.float32)

        indices = np.array([
            # base
            0, 1, 2,
            0, 2, 3,
            # sides
            0, 1, 4,
            1, 2, 4,
            2, 3, 4,
            3, 0, 4
        ], dtype=np.uint32)

        (normals, vertices, index) = calcNormals(vertices, indices)
        mesh = core.Mesh(shader, attributes=dict(position=vertices, tex_coord=np.array(texture_coords), normal=normals),
                    index=index, s=shinyness, light_dir=light_dir)
        # setup & upload texture to GPU, bind it to shader name 'diffuse_map'
        super().__init__(mesh, diffuse_map=texture)

    
    
class TexturedSphere(Textured):
    """ Procedural textured sphere """

    # avec l'aide de : http://www.songho.ca/opengl/gl_sphere.html
    def __init__(self, shader, texture, position=(0, 0, 0), r=1, stacks=10, sectors=10, light_dir=None, shinyness=2):
        # setup plane mesh to be textured
        vertices = ()
        tex_coord = ()

        lengthInv = 1.0 / r
        sectorStep = 2 * np.pi / sectors
        stackStep = np.pi / stacks

        for i in range(stacks + 1):
            stackAngle = np.pi / 2 - i * stackStep
            xy = r * np.cos(stackAngle)
            z = r * np.sin(stackAngle) + r

            for j in range(sectors + 1):
                sectorAngle = j * sectorStep
                # vertex position (x, y, z)
                x = xy * np.cos(sectorAngle)
                y = xy * np.sin(sectorAngle)
                vertices = vertices + ((x, z, y),)
                tex_coord += ((i / stacks, j / sectors),)
        vertices = np.array(vertices, np.float32)+np.array(position, np.float32)

        index = ()
        for i in range(stacks):
            k1 = i * (sectors + 1)
            k2 = k1 + sectors + 1
            for j in range(sectors):

                # 2 triangles per sector excluding first and last stacks
                if (i != 0):
                    index = index + (k1, k1 + 1, k2)

                if (i != (stacks - 1)):
                    index = index + (k1 + 1, k2 + 1, k2)

                k1 = k1 + 1
                k2 = k2 + 1
        
        (normals, vertices, index) = calcNormals(vertices, index)
        self.vertices = vertices
        mesh = core.Mesh(shader, attributes=dict(position=vertices, tex_coord=np.array(tex_coord), normal=normals),
                    index=index, s=shinyness, light_dir=light_dir)

        # setup & upload texture to GPU, bind it to shader name 'diffuse_map'
        super().__init__(mesh, diffuse_map=texture)
        
