import OpenGL.GL as GL              # standard Python OpenGL wrapper
import numpy as np                  # all matrix manipulations & OpenGL args
from core import Node, Mesh
from texture import Textured, TexturedPyramid, TexturedSphere, TexturedCylinder, Texture, TexturedTiltedCylinder, Cone, PineCone
from transform import normalized, calc_normals
from PIL import Image
import glfw        
import random
from math import radians
       
class Treemapping(Node):
    def __init__(self, shader, position, leavesTextures_path1, leavesTextures_path2, trunkTextures_path, nb_gen, shadow_map_tex):
        super().__init__()
        random.seed()
        self.WATER_LEVEL = -40
        leavesTextures1 = Texture(leavesTextures_path1, GL.GL_REPEAT, *(GL.GL_LINEAR, GL.GL_LINEAR_MIPMAP_LINEAR))
        leavesTextures2 = Texture(leavesTextures_path2, GL.GL_REPEAT, *(GL.GL_LINEAR, GL.GL_LINEAR_MIPMAP_LINEAR))
        trunkTextures = Texture(trunkTextures_path, GL.GL_REPEAT, *(GL.GL_LINEAR, GL.GL_LINEAR_MIPMAP_LINEAR))

        tree_positions = np.empty((nb_gen,3))
        index_tree_positions = []
        cpt = 0
        ttl = 100 #prevent case where we can't generate anymore (or at least too hard)
        while cpt < nb_gen and ttl != 0 :
            tree = random.randint(0, len(position)-1)
            tree_coordinates = position[tree]
            if tree_coordinates[1]<= self.WATER_LEVEL or tree in index_tree_positions or abs(tree_coordinates[0]) < 50 or abs(tree_coordinates[2]) < 40 : 
            #en dessous du niveau de l'eau, deja placee ou dans le cratere
                ttl-=1
            else :
                tree_positions[cpt] = tree_coordinates
                index_tree_positions.append(tree)
                ttl = 100
                cpt+=1
        if cpt != 0 and cpt != 1: # prevent accessing wrong indices

            nb_pine = random.randint(1,cpt-1)
            trunks, leaves = self.generate_pine_tree_forest(nb_pine, tree_positions[:nb_pine], shader, trunkTextures, leavesTextures1, shadow_map_tex)
            self.add(trunks)
            self.add(leaves)
            oak_trunks, oak_leaves = self.generate_oak_tree_forest(cpt-nb_pine, tree_positions[nb_pine:cpt], shader, trunkTextures, leavesTextures2, shadow_map_tex)
            self.add(oak_trunks)
            self.add(oak_leaves)
        

    def generate_pine_tree_forest(self, nb_pine, tree_positions, shad, tex1, tex2, shadow_map_tex):
        trunks = GenerateTrunks(shader=shad, texture=tex1, nb_gen=nb_pine, positions=tree_positions, shadow_map_t=shadow_map_tex)
        leaves = GeneratePineLeaves(shader=shad, texture=tex2, nb_gen=nb_pine, positions=tree_positions, shadow_map_t=shadow_map_tex, t_heights=trunks.trunk_final_height)
        return trunks, leaves
    
    def generate_oak_tree_forest(self, nb_oak, tree_positions, shad, tex1, tex2, shadow_map_tex):
        trunks = GenerateTrunks(shader=shad, texture=tex1, nb_gen=nb_oak, positions=tree_positions, r=0.6, shadow_map_t=shadow_map_tex)
        leaves = GenerateLeaves(shader=shad, texture=tex2, nb_gen=nb_oak, positions=tree_positions, shadow_map_t=shadow_map_tex, t_heights=trunks.trunk_final_height)
        return trunks, leaves
        

class GenerateTrunks(Textured):
    def __init__(self, shader, texture, nb_gen, positions, height=5, divisions=10, r=0.4, shadow_map_t=None):
        self.height = height
        self.divisions = divisions
        self.ray = r
        trunk_vertices_count = self.divisions*2+2
        vertices = [] 
        trunk_vertices = self.generate_trunk_vertices(trunk_vertices_count)  
        tex_coords = [] 
        tex_coords_np = self.generate_trunk_tex_coords(trunk_vertices_count)
        index = []
        trunk_indices = self.generate_trunk_indices()
        self.trunk_final_height = []
        for i in range(0, nb_gen):
            height_offset = random.uniform(0.75,1.25)
            self.trunk_final_height.append(height_offset*self.height)
            tmp_vertices = trunk_vertices*height_offset + np.array(positions[i], np.float32)
            vertices.extend(tmp_vertices.tolist())
            tex_coords.extend(tex_coords_np.tolist())
            index.extend( (trunk_indices + i*len(tmp_vertices)).tolist())
        normals = calc_normals(np.array(vertices), index)
        mesh = Mesh(shader, attributes=dict(position=vertices, tex_coord=tex_coords, normal=normals),
                    index=index, k_a=(0.4,0.4,0.4), k_d=(0.8,0.7,0.7), k_s=(1.0,0.85,0.85), s=8)

        # setup & upload texture to GPU, bind it to shader name 'diffuse_map'
        super().__init__(mesh, diffuse_map=texture, shadow_map=shadow_map_t)


    def generate_trunk_tex_coords(self, size):
        tex_coords = np.empty((size+2,2)) # (0,0)
        tex_coords[0] = [1, 1]
        # top
        for i in range(0, self.divisions):
            tex_coords[i+1] = [i / self.divisions, 0]
        tex_coords[self.divisions+1] =  [0, 0]
        #bottom
        for i in range(0, self.divisions):
            tex_coords[self.divisions+2+i] =  [i / self.divisions, 1]
        tex_coords[size] = [1, 0] # pawn vertex
        tex_coords[size+1] = [1, 1] # pawn vertex
        return tex_coords

    def generate_trunk_indices(self):
        size = 4*(self.divisions-1)+4
        index = np.empty(shape=(size,3), dtype=int)
        # top face
        for i in range(1, self.divisions):
            index[i-1]= [0, i + 1, i]
        index[self.divisions-1] = [0, 2*self.divisions+2, self.divisions] #junction with the pawn vertex
        # bottom face
        for i in range(1, self.divisions):
            index[i-1+self.divisions] = [self.divisions + 1, self.divisions + i + 1, self.divisions + i + 2]
        index[(self.divisions-1)+self.divisions] = [self.divisions + 1, self.divisions * 2 + 1, 2*self.divisions + 3] #same
        # side
        j=0
        for i in range(1, self.divisions):
            index[j+2*self.divisions] = [i, i + 1, self.divisions + i + 1]
            index[j+1+2*self.divisions] = [i + 1, self.divisions + i + 2, self.divisions + i + 1]
            j = j + 2
        index[size-2] = [self.divisions, 2*self.divisions+2, self.divisions * 2 + 1] #junction with the pawn vertex
        index[size-1] = [1, 2*self.divisions + 3, self.divisions * 2 + 1] #junction with the pawn vertex

        return index.flatten()

    def generate_trunk_vertices(self, size):    
        vertices = np.empty(shape=(size+2,3))
        vertices[0] = [0, self.height, 0]
        # top
        i=1
        for angle in np.arange(0, 2 * np.pi, 2 * np.pi / self.divisions):
            vertices[i] = [self.ray * np.cos(angle) , self.height, self.ray * np.sin(angle)]
            i = i + 1
        vertices[i] = [0, 0, 0]
        i = i + 1
        #bottom
        for angle in np.arange(0, 2 * np.pi, 2 * np.pi / self.divisions):
            vertices[i] = [self.ray * np.cos(angle), 0, self.ray * np.sin(angle)]
            i = i + 1
        vertices[size] = [self.ray, self.height, 0] # pawn vertex
        vertices[size+1] = [self.ray, 0, 0] # pawn vertex
        return  vertices 
    

class GeneratePineLeaves(Textured):
    def __init__(self, shader, texture, nb_gen, positions, t_heights, height=5, divisions=10, r=2.5, layer_height=2.5, shadow_map_t=None):
        self.height = height
        self.divisions = divisions
        self.ray = r

        leaves_vertices_count = self.divisions+2
        vertices = [] 
        leaves_vertices = self.generate_leaves_vertices(leaves_vertices_count)  
        tex_coords = [] 
        tex_coords_np = self.generate_leaves_tex_coords(leaves_vertices_count)
        index = []
        leaves_indices = self.generate_leaves_indices()
        forest_nb_layers=0
        for i in range(0, nb_gen):
            nb_layers = random.randint(3,6)
            width_offset = random.uniform(0.7,1.3)
            height_offset = random.uniform(0.5,1.5)
            depth_offset = random.uniform(0.7,1.3)
            layer_height = random.uniform(1.5,2.2)
            leaves_tmp = leaves_vertices * np.array([width_offset, height_offset, depth_offset])
            for j in range(0, nb_layers):
                position = [positions[i][0] , positions[i][1]+j*layer_height*height_offset+t_heights[i] , positions[i][2]]
                tmp_vertices = leaves_tmp*0.9**(j+1) + np.array(position, np.float32)
                vertices.extend(tmp_vertices.tolist())
                tex_coords.extend(tex_coords_np.tolist())
                index.extend( (leaves_indices + (forest_nb_layers+j)*len(tmp_vertices)).tolist())
            forest_nb_layers += nb_layers
        normals = calc_normals(np.array(vertices), index)
        mesh = Mesh(shader, attributes=dict(position=vertices, tex_coord=tex_coords, normal=normals),
                    index=index, k_a=(0.4,0.4,0.4), k_d=(0.8,0.7,0.7), k_s=(1.0,0.85,0.85), s=8)

        # setup & upload texture to GPU, bind it to shader name 'diffuse_map'
        super().__init__(mesh, diffuse_map=texture, shadow_map=shadow_map_t)


    def generate_leaves_tex_coords(self, size):
        tex_coords = np.empty((size,2)) # (0,0)
        tex_coords[0] = [0,0]
        tex_coords[1] = [1,1]
        # top
        for i in range(0, self.divisions):
            tex_coords[i+2] = [i / self.divisions, 1]
        return tex_coords

    def generate_leaves_indices(self):
        size = 2*(self.divisions-2)+2
        index = np.empty(shape=(size,3), dtype=int)
        # sides face
        for i in range(2, self.divisions):
            index[i-2] = [0, i + 1, i]
        index[self.divisions-2] = [0, 2, self.divisions]
        for i in range(2, self.divisions):
            index[self.divisions-3+i] = [1, i , i + 1]
        index[size-1] = [1, self.divisions, 2]
        return index.flatten()

    def generate_leaves_vertices(self, size):    
        vertices = np.empty(shape=(size,3))
        vertices[0] = [0, self.height, 0]
        vertices[1] = [0, 0, 0]
        i=2
        #bottom
        for angle in np.arange(0, 2 * np.pi, 2 * np.pi / self.divisions):
            vertices[i] = [self.ray * np.cos(angle), 0, self.ray * np.sin(angle)]
            i = i + 1
        return  vertices 
    

 
class GenerateLeaves(Textured):
    def __init__(self, shader, texture, nb_gen, positions, t_heights, height=5, stacks=10, sectors=10, r=2.5, layer_height=2.5, shadow_map_t=None):
        self.height = height
        self.stacks = stacks
        self.sectors = sectors
        self.ray = r

        leaves_vertices_count = (self.stacks+1)*(self.sectors+1)
        vertices = [] 
        tex_coords = [] 
        leaves_vertices, tex_coords_np = self.generate_leaves_vertices_and_coords(leaves_vertices_count)  
        index = []
        leaves_indices = self.generate_leaves_indices()
        for i in range(0, nb_gen):
            width_offset = random.uniform(0.8,1.4)
            height_offset = random.uniform(0.8,1.6)
            depth_offset = random.uniform(0.8,1.4)
            leaves_tmp = leaves_vertices * np.array([width_offset, height_offset, depth_offset])
            position = [positions[i][0] , positions[i][1]+t_heights[i]*0.9 , positions[i][2]]
            tmp_vertices = leaves_tmp + np.array(position, np.float32)
            vertices.extend(tmp_vertices.tolist())
            tex_coords.extend(tex_coords_np.tolist())
            index.extend( (leaves_indices + i*len(tmp_vertices)).tolist())
        normals = calc_normals(np.array(vertices), index)
        mesh = Mesh(shader, attributes=dict(position=vertices, tex_coord=tex_coords, normal=normals),
                    index=index, k_a=(0.4,0.4,0.4), k_d=(0.8,0.7,0.7), k_s=(1.0,0.85,0.85), s=8)

        # setup & upload texture to GPU, bind it to shader name 'diffuse_map'
        super().__init__(mesh, diffuse_map=texture, shadow_map=shadow_map_t)

    def generate_leaves_indices(self):
        size = 2*((self.stacks-2)*self.sectors)+ (2*self.sectors)
        index = np.empty(shape=(size,3), dtype=int)
        k = 0
        for i in range(self.stacks):
            k1 = i * (self.sectors + 1)
            k2 = k1 + self.sectors + 1
            for j in range(self.sectors):
                if (i != 0):
                    index[k] = [k1, k1 + 1, k2]
                    k = k + 1
                if (i != (self.stacks - 1)):
                    index[k] = [k1 + 1, k2 + 1, k2]
                    k = k + 1
                k1 = k1 + 1
                k2 = k2 + 1
        return index

    def generate_leaves_vertices_and_coords(self, size):    
        vertices = np.empty(shape=(size,3))
        tex_coords = np.empty(shape=(size,2))

        k = 0
        for i in range(self.stacks + 1):
            stackAngle = np.pi / 2 - i * (np.pi / self.stacks)
            xy = self.ray * np.cos(stackAngle)
            z = self.ray * np.sin(stackAngle) + self.ray

            for j in range(self.sectors + 1):
                sectorAngle = j * (2 * np.pi / self.sectors)
                # vertex position (x, y, z)
                x = xy * np.cos(sectorAngle)
                y = xy * np.sin(sectorAngle)
                vertices[k] = [x, z, y]
                tex_coords[k] = [i / self.stacks, j / self.sectors ]
                k = k + 1
        return vertices, tex_coords
       