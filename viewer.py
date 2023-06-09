#!/usr/bin/env python3
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
from water import Water
from tree import Treemapping
from GrassManager import Grass_blade
from animation_rocks import RockTime
from cloud import Cloud
from noise import Noise
from particles import ParticlesEmitter

# -------------- Example textured plane class ---------------------------------
class TexturedPlane(Textured):
    """ Simple first textured object """
    def __init__(self, shader, tex_file):
        # prepare texture modes cycling variables for interactive toggling
        self.wraps = cycle([GL.GL_REPEAT, GL.GL_MIRRORED_REPEAT,
                            GL.GL_CLAMP_TO_BORDER, GL.GL_CLAMP_TO_EDGE])
        self.filters = cycle([(GL.GL_NEAREST, GL.GL_NEAREST),
                              (GL.GL_LINEAR, GL.GL_LINEAR),
                              (GL.GL_LINEAR, GL.GL_LINEAR_MIPMAP_LINEAR)])
        self.wrap, self.filter = next(self.wraps), next(self.filters)
        self.file = tex_file

        # setup plane mesh to be textured
        base_coords = ((-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0))
        scaled = 100 * np.array(base_coords, np.float32) 
        indices = np.array((0, 1, 2, 0, 2, 3), np.uint32)
        mesh = Mesh(shader, attributes=dict(position=scaled), index=indices)

        # setup & upload texture to GPU, bind it to shader name 'diffuse_map'
        texture = Texture(tex_file, self.wrap, *self.filter)
        super().__init__(mesh, cube_map=texture) # change to cube map along with the shader used for chrome effect

    def key_handler(self, key):
        # cycle through texture modes on keypress of F6 (wrap) or F7 (filtering)
        self.wrap = next(self.wraps) if key == glfw.KEY_F6 else self.wrap
        self.filter = next(self.filters) if key == glfw.KEY_F7 else self.filter
        if key in (glfw.KEY_F6, glfw.KEY_F7):
            texture = Texture(self.file, self.wrap, *self.filter)
            self.textures.update(diffuse_map=texture)

class CubeMapTexture(TexturedCube):
    """ Simple first textured object """
    def __init__(self, shader, tex_path, tex_path2):
        self.file = tex_path

        # setup cube mesh to be textured
        base_coords_face1 = ((-1, 1, -1), (-1, -1, -1), (1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1))
        base_coords_face2 = ((-1, -1, 1), (-1, -1, -1), (-1, 1, -1), (-1, 1, -1), (-1, 1, 1), (-1, -1, 1))
        base_coords_face3 = ((1, -1, -1), (1, -1, 1), (1, 1, 1), (1, 1, 1), (1, 1, -1), (1, -1, -1))
        base_coords_face4 = ((-1, -1, 1), (-1, 1, 1), (1, 1, 1), (1, 1, 1), (1, -1, 1), (-1, -1, 1))
        base_coords_face5 = ((-1, 1, -1), (1, 1, -1), (1, 1, 1), (1, 1, 1), (-1, 1, 1), (-1, 1, -1))
        base_coords_face6 = ((-1, -1, -1), (-1, -1, 1), (1, -1, -1), (1, -1, -1), (-1, -1, 1), (1, -1, 1))
        base_coords = base_coords_face1 + base_coords_face2 + base_coords_face3 + base_coords_face4 + base_coords_face5 + base_coords_face6
        mesh = Mesh(shader, attributes=dict(position=base_coords))

        # setup & upload texture to GPU, bind it to shader name 'cube_map'
        texture = CubeMapTex(tex_path)
        texture2 = CubeMapTex(tex_path2)
        super().__init__(mesh, cube_map=texture, cube_map2=texture2)
        

# -------------- main program and scene setup --------------------------------
def main():
    """ create a window, add scene objects, then run rendering loop """
    viewer = Viewer()
    shader = Shader("glsl/texture.vert", "glsl/texture.frag")
    shaderTerrain = Shader("glsl/texture_terrain.vert", "glsl/texture_terrain.frag")
    normalvizShader = Shader("glsl/normalviz.vert", "glsl/normalviz.frag", "glsl/normalviz.geom") 
    lightCubeShader = Shader("glsl/lightcube.vert", "glsl/lightcube.frag")
    skyboxShader = Shader("glsl/skybox.vert", "glsl/skybox.frag")
    waterShader = Shader("glsl/water.vert", "glsl/water.frag")
    reflectionShader = Shader("glsl/texture.vert", "glsl/texture_reflection.frag") # reflection par rapport a la skybox
    cloudShader = Shader("glsl/cloud.vert", "glsl/cloud.frag")
    particleShader = Shader("glsl/particle.vert", "glsl/particle.frag")
    noiseMap = Noise()
    
    
    terrain_textures = ("texture/terrain_texture/blackrock.png", "texture/terrain_texture/meadow.png", 
                       "texture/terrain_texture/ocean.png", "texture/terrain_texture/sand.png", "texture/terrain_texture/rock_snow.png" )
    terrain_normal_textures = ("texture/terrain_texture/blackrock_normal.png", "texture/terrain_texture/meadow_normal.png", 
                       "texture/terrain_texture/ocean_normal.png", "texture/terrain_texture/sand_normal.png",
                       "texture/terrain_texture/rock_snow_normal.png" )

    
    viewer.add(*[mesh for file in sys.argv[1:] for mesh in load(file, shader)])
    terrain = Terrain(shaderTerrain, terrain_textures, terrain_normal_textures, "texture/terrain_texture/noise_map.png", "texture/terrain_texture/lava_map.png",
                       "texture/water/dudv.png", "texture/water/waternormalmap.png", 513, 513, "texture/heightmapstests/Heightmap.png",  viewer.getShadowFrameBuffer())

    viewer.add(terrain)
    vertices = terrain.getVertices()    
    
    viewer.add(Treemapping(shader, vertices , "texture/textures_wood/pineleaf2.png", "texture/textures_wood/leaves.png", "texture/textures_wood/bark.jpg", 500, viewer.getShadowFrameBuffer().getDepthTexture()))
    viewer.add(RockTime(shader, reflectionShader))
    viewer.add(Water(waterShader, 513, 513, viewer.getWaterFrameBuffers(), "texture/water/dudv.png", "texture/water/waternormalmap.png"))
    viewer.add(CubeMapTexture(skyboxShader, "texture/skybox/skyboxday", "texture/skybox/skyboxnight/"))
    viewer.add(Cloud(cloudShader, 513,513,noiseMap.getNoiseMapTexture()))

    #Particles
    emitter = ParticlesEmitter(particleShader)
    viewer.add(emitter)
    viewer.setParticlesEmitter(emitter)
    # start rendering loop
    viewer.run()   


if __name__ == '__main__':
    main()                     # main function keeps variables locally scoped
