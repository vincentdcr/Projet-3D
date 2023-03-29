import OpenGL.GL as GL           # standard Python OpenGL wrapper
import numpy as np                  # all matrix manipulations & OpenGL args
from core import Node,load, timer
from texture import TexturedPyramid, TexturedSphere, TexturedCylinder, Texture, TexturedTiltedCylinder, Cone
from animation import KeyFrameControlNode
from transform import quaternion_from_euler, translate, vec, quaternion
import glfw

import random # 1/5 pas rocher mais lapins (chromatiques si possible)

class RockTime(Node):
    def __init__(self, shader, shader_chroma):
        #ajout des rochers et de leurs animations.
        # les rochers sont animés pour la map choisie, changer de map peut entraîner des erreurs et ce serait bien fait, toc.
        super().__init__()
        random.seed()
        res = random.randint(0,5) # si plusieurs probas d'anims plus tard 
        if res == 0 :
            self.obj1_list =load("bunny.obj", shader_chroma)            
        else :
            self.obj1_list =load("rock/Rock1/Rock1.obj", shader)
        #boucle 
        for i in range(0,len(self.obj1_list)-1):
            self.add(self.obj1_list[i])      
            

    def key_handler(self,key):
        if key == glfw.KEY_ENTER:
            
            time = timer()
            translate_keys = {0+time : vec(0,0,0),#{0+time : vec(-16,0,-18),
                             # 1+time : vec(-68,61,-52),
                             # 2+time : vec(-172,30,-171),
                             # 3+time : vec(-201,-37,-211)}
                            
                              1+time : vec(0,0,0),
                              2+time : vec(0,0,0),
                              3+time : vec(0,0,0)}
            rotate_keys = {0+time: quaternion(),
                           1+time: quaternion_from_euler(0, -200, -100),
                           2+time: quaternion_from_euler(0,-300,-150),
                           3+time:  quaternion()}
            scale_keys = {0+time: 5,
                          1+time: 5,
                          2+time: 5,
                          3+time: 5}

            keynode = KeyFrameControlNode(translate_keys, rotate_keys, scale_keys)
            keynode.add(self.obj1_list[0])
            self.add(keynode)
            #.children =
        
   
        