import OpenGL.GL as GL              # standard Python OpenGL wrapper
import numpy as np                  # all matrix manipulations & OpenGL args
from core import Node
from texture import TexturedPyramid, TexturedSphere, TexturedCylinder, Texture, TexturedTiltedCylinder, Cone
from transform import normalized
from PIL import Image
import glfw        
import random
from math import radians


class TexturedTree(Node):
    def __init__(self, shader, position, leavesTextures, trunkTextures, light_dir=None):
        super().__init__()
        random.seed()
        
        
        (x, y, z) = position
        trunk_height = 2.5 + random.random()
        main_leaves_size = 2 + random.random()

        self.add(
            TexturedCylinder(shader, position=(x, y, z), height=trunk_height, texture=trunkTextures,
                             light_dir=light_dir))
        self.add(TexturedSphere(shader, position=(x, y + trunk_height, z), r=main_leaves_size, texture=leavesTextures,
                                light_dir=light_dir))

class TexturedPineTree(Node):
    def __init__(self, shader, position, leavesTextures, trunkTextures, light_dir=None):
        super().__init__()
        random.seed()
        
        (x, y, z) = position
        trunk_height = 3 + random.random()
        main_leaves_size = 1.5 + random.random()
        layers = random.randint(3, 5)
        layer_height = (layers) / random.uniform(1.5, 3)



        # drawing du tronc
        self.add(
            TexturedCylinder(shader, position=(x, y , z), height=trunk_height, r=0.25, texture=trunkTextures,
                             light_dir=light_dir))
        
        #drawing des feuilles
        for i in range(layers):
            layer_scale = -(1/layers)*i + main_leaves_size #ça ca marche
            bias_scale = layer_scale * random.uniform(0.2, 0.4)
            layer_y = trunk_height*(3/2) + layer_height * (i)       
            self.add(
                Cone(shader, position=(x, (layer_y/2)+y, z), height=layer_height, r=layer_scale, texture=leavesTextures,
                                light_dir=light_dir))
       
class Treemapping(Node): # plus tard, mapper la height de détéction ou non des arbres valides sur celle de l'eau +5 ( la plage en gros )
    def __init__(self, shader, position_Array, leavesTextures_path1, leavesTextures_path2, trunkTextures_path, nb_gen, light_dir=None):
        super().__init__()
        cpt =0        
        random.seed()
        len_vertices = len(position_Array)
        WATER_LEVEL = -40
        leavesTextures1 = Texture(leavesTextures_path1, GL.GL_REPEAT, *(GL.GL_LINEAR, GL.GL_LINEAR_MIPMAP_LINEAR))
        leavesTextures2 = Texture(leavesTextures_path2, GL.GL_REPEAT, *(GL.GL_LINEAR, GL.GL_LINEAR_MIPMAP_LINEAR))
        trunkTextures = Texture(trunkTextures_path, GL.GL_REPEAT, *(GL.GL_LINEAR, GL.GL_LINEAR_MIPMAP_LINEAR))

        
        while cpt < nb_gen: # generation basique aléatoire, très couteux, GPU instancing using bufferisation (explication prof) plus tard si possible en temps.
            plant = random.randint(0, len_vertices-1)
            plant_coordinates = position_Array [plant]
            
            if plant_coordinates[1]<= WATER_LEVEL : #en dessous du niveau de l'eau
                cpt-=1
            else :
                choix = random.randint(0,1)
                if choix == 0 :
                    # ajout d'un pin 
                   self.add(TexturedPineTree(shader, position_Array[plant],leavesTextures1,trunkTextures))
                   pass
                elif choix ==1 :
                    #ajout d'un arbre basique
                    self.add(TexturedTree(shader, position_Array[plant],leavesTextures2 ,trunkTextures))
                else : 
                    print ("on passera jamais ici")
            cpt+=1
            