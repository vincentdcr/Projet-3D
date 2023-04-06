
from lava import Lava                 
from core import Node, Shader,load, timer
from animation import KeyFrameControlNode
from transform import quaternion_from_euler, translate, vec, quaternion
import glfw

import random # 1/5 pas rocher mais lapins (chromatiques si possible)

class RockTime(Node):
    def __init__(self, shader, shader_chroma):
        super().__init__()
        random.seed()
        self.obj_array = []
        self.obj_shader = shader
        res = random.randint(0, 5)
        if res == 0:
            obj_filename = "texture/bunny/bunny.obj"
            self.obj_shader = shader_chroma
        else:
            obj_filename = "texture/rock/Rock1/Rock1.obj"
        obj = load(obj_filename, self.obj_shader)

        for i in range(4):
            obj = load(obj_filename, self.obj_shader)
            self.obj_array.append(obj[0])    

        lavaShader = Shader("glsl/Lava.vert", "glsl/Lava.frag")
        self.lava_node = Node(transform=translate(-12,0,-20))
        self.lava_node.add(Lava(lavaShader, 90, 80, "texture/terrain_texture/noisemap.png", "texture/water/dudv.png", "texture/water/waternormalmap.png"))     
        
        #flag to prevent erasing from Node if it's the first time we press Enter
        self.first_time = True

    def key_handler(self,key):
        if key == glfw.KEY_ENTER:
                if (not self.first_time):
                    self.remove(self.keynode1)
                    self.remove(self.keynode2)
                    self.remove(self.keynode3)
                    self.remove(self.keynode4)
                    self.remove(self.keynode_plan)
                self.first_time = False
            
                # make a small plane, put it at the origin and texture it with terrain_texture/lava-texture-free.jpg
                time = timer()
                
                #plane animation 
                translate_keys = {time : vec(0,0,0),
                                10 + time : vec(0,7,0)
                                }
                rotate_keys = {time: quaternion_from_euler(0, 0, 0),
                            10 + time: quaternion_from_euler(0, 0, 0)
                            }
                scale_keys = {time: 1.15,
                            10 + time: 1.15
                            }
                self.keynode_plan = KeyFrameControlNode(translate_keys, rotate_keys, scale_keys)
                self.keynode_plan.add(self.lava_node)
                self.add(self.keynode_plan)
                
                # First corner
                translate_keys1 = {
                    0+time: vec(-16, 0, -18),
                    10+time: vec(-68, 70, -52),
                    20+time: vec(-172, 30, -171),
                    30+time: vec(-201, -37, -211)
                }
                rotate_keys = {
                    0+time: quaternion(),
                    10+time: quaternion_from_euler(0, -200, -100),
                    20+time: quaternion_from_euler(0, -300, -150),
                    30+time: quaternion()
                }
                scale_keys = {
                    0+time: 5,
                    10+time: 5,
                    20+time: 5,
                    30+time: 5
                }

                self.keynode1 = KeyFrameControlNode(translate_keys1, rotate_keys, scale_keys)
                self.keynode1.add(self.obj_array[0])
                self.add(self.keynode1)
                # Second corner
                translate_keys2 = {
                    0+time: vec(-16, 0, -18),
                    15+time: vec(52, 80, -47),
                    26+time: vec(170, 30, -168),
                    33+time: vec(211, -37, -206)
                }

                self.keynode2 = KeyFrameControlNode(translate_keys2, rotate_keys, scale_keys)
                self.keynode2.add(self.obj_array[1])
                self.add(self.keynode2)

                # Third corner
                translate_keys3 = {
                    0+time: vec(-16, 0, -18),
                    5+time: vec(54, 150, 46),
                    8+time: vec(171, 27, 163),
                    10+time: vec(206, -37, 201)
                }

                self.keynode3 = KeyFrameControlNode(translate_keys3, rotate_keys, scale_keys)
                self.keynode3.add(self.obj_array[2])
                self.add(self.keynode3)

                # Fourth corner
                translate_keys4 = {
                    0+time: vec(-16, 0, -18),
                    11+time: vec(-50, 200, 55),
                    19+time: vec(-162, 30, 172),
                    24+time: vec(-203, -37, 210)
                }

                self.keynode4 = KeyFrameControlNode(translate_keys4, rotate_keys, scale_keys)
                self.keynode4.add(self.obj_array[3])
                self.add(self.keynode4)
                


