#!/usr/bin/env python3
import OpenGL.GL as GL              # standard Python OpenGL wrapper
import numpy as np                  # all matrix manipulations & OpenGL args
from core import  Mesh
from texture import Texture, Textured, TextureArray
from transform import normalized, calc_normals
from PIL import Image


 
# -------------- Terrain ---------------------------------
class Terrain(Textured):
    """ Simple first textured object """
    def __init__(self, shader, terrain_textures, terrain_normal_textures, noise_file, lava_map_file, dudv_file, lava_normal_file, map_width, map_height, heightmap_file, shadowFrameBuffer):
        height_map = generate_height_map(map_width, map_height, heightmap_file)
        self.vertices = generate_vertices(map_width, map_height, height_map)
        indices = generate_indices(map_width, map_height)
        texcoords = generate_texcoords(map_width, map_height)
        normals = calc_normals(self.vertices, indices) 
        # setup plane mesh to be textured
        mesh = Mesh(shader, attributes=dict(position=self.vertices, tex_coord=texcoords, normal=normals), index=indices, k_a=(0.4,0.4,0.4), k_d=(0.8,0.7,0.7), k_s=(1.0,0.85,0.85), s=8)

        # setup & upload texture to GPU, bind it to shader name 'diffuse_map'

        terrain_tex = TextureArray(terrain_textures, 2048, 2048, GL.GL_REPEAT, GL.GL_LINEAR, GL.GL_LINEAR_MIPMAP_LINEAR)
        terrain_normal_tex = TextureArray(terrain_normal_textures, 2048, 2048, GL.GL_REPEAT, GL.GL_LINEAR, GL.GL_LINEAR_MIPMAP_LINEAR, gamma_correction=False)
        noise_tex = Texture(noise_file, GL.GL_REPEAT, *(GL.GL_LINEAR, GL.GL_LINEAR_MIPMAP_LINEAR), gamma_correction=False)
        lava_map_tex = Texture(lava_map_file, GL.GL_REPEAT, *(GL.GL_LINEAR, GL.GL_LINEAR_MIPMAP_LINEAR), gamma_correction=False)
        lava_normal_tex = Texture(lava_normal_file, GL.GL_MIRRORED_REPEAT, *(GL.GL_LINEAR, GL.GL_LINEAR_MIPMAP_LINEAR), gamma_correction=False)
        dudv_tex = Texture(dudv_file, GL.GL_MIRRORED_REPEAT, *(GL.GL_LINEAR, GL.GL_LINEAR_MIPMAP_LINEAR), gamma_correction=False)
        super().__init__(mesh, terrain=terrain_tex, terrain_normal=terrain_normal_tex, noise_map=noise_tex, lava_map=lava_map_tex, 
                         lava_normal_map=lava_normal_tex, dudv_map=dudv_tex, shadow_map=shadowFrameBuffer.getDepthTexture())

    def getVertices (self):
        return self.vertices 
 

def generate_height_map(width, height, heightmap_file):
    MIN_HEIGHT = -64
    MAX_HEIGHT = 64

    im = Image.open(heightmap_file) 
    
    heightmap = im.convert("L")  # convert to grayscale
    
    noise_map = np.zeros((height, width))
    
    for z in range(min(heightmap.height, height)):
        for x in range(min(heightmap.width, width)):
            noise_map[z,x] = np.interp(heightmap.getpixel((z,x)), [0,255], [MIN_HEIGHT,MAX_HEIGHT]) #map height map value    
    return noise_map


def generate_vertices(width, height, noise_map): #à récup pour les coord de chaque point de la grille
    v = []
    for z in range(0,height): 
        for x in range(0,width):
            v.append((-height/2 + x, noise_map[x,z], -width/2 + z))   
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
                # Bottom left triangle of square
                indices.append(pos)
                indices.append(pos + width)
                indices.append(pos + width + 1)
                # Top right triangle of square
                indices.append(pos + 1 + width)
                indices.append(pos + 1)
                indices.append(pos)
    
    return np.asarray(indices)

# make sure that the wrap mode is set to repeat !
def generate_texcoords(width, height):
    texcoords = []
    for z in range(0,height): 
        for x in range(0,width):
            texcoords.append((x,z))
    return np.asarray(texcoords)

def generate_normals(width, height, position):

    normals = np.full((width*height, 3), fill_value=np.array([0.0,1.0,0.0]))
    for z in range(1,height-1): 
        for x in range(1,width-1):
            Yu       = position[x + (z+1)*width][1]
            Yul = position[x+1 + (z+1)*width][1]
            Yl = position[x+1 + z*width][1]
            Yd = position[x + (z-1)*width][1]
            Ydr = position[x-1 + (z-1)*width][1]
            Yr = position[x-1 + z*width][1]
            
            normal = np.array([  (2*(Yr - Yl) - Yul + Ydr + Yu - Yd), 6, (2*(Yd - Yu) + Yul + Ydr - Yu - Yr)  ])
            normals[x+z*width] = normalized(normal)
    return normals 

def generate_tangents(vertices, indices, texcoords):
    tangents = np.zeros((len(vertices), 3))

    # reshape the input arrays to be (num_triangles, 3, 3) and (num_triangles, 3, 2)
    tri_verts = vertices[indices].reshape(-1, 3, 3)
    tri_uvs = texcoords[indices].reshape(-1, 3, 2)
    edge_1 = tri_verts[:,1] - tri_verts[:,0]
    edge_2 = tri_verts[:,2] - tri_verts[:,0]
    delta_uv1 = tri_uvs[:,1] - tri_uvs[:,0]
    delta_uv2 = tri_uvs[:,2] - tri_uvs[:,0]
    f = 1.0 / (delta_uv1[:,0] * delta_uv2[:,1] - delta_uv2[:,0] * delta_uv1[:,1])
    j=0
    for i in range(0, len(indices), 3):
        i1, i2, i3 = indices[i], indices[i+1], indices[i+2]
        tangents[i1] = f[j] * (delta_uv2[j,1] * edge_1[j] - delta_uv1[j,1] * edge_2[j])
        tangents[i2] = tangents[i1]
        tangents[i3] = tangents[i1]
        j = j + 1
    return tangents