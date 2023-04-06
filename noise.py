import numpy as np                  # all matrix manipulations & OpenGL args
import core
from texture import Texture, Textured
from transform import normalized
from PIL import Image
from waterFrameBuffer import WaterFrameBuffers
import random
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from scipy.signal import medfilt2d


class Noise():
    map32 = np.zeros((32 , 32))
    map256 = np.zeros((256 , 256))
    def __init__(self):
        self.SetNoise()
        
    def getNoiseMap(self):
        self.OverlapOctaves(self.map32, self.map256)
        self.ExpFilter(self.map256)
        return np.array(self.map256)

    def getNoiseMapTexture(self):
        
        return Texture(self.getNoiseMap(), GL_REPEAT, *(GL_LINEAR, GL_LINEAR_MIPMAP_LINEAR))

    def noise(self,x, y):
        """
        A simple noise function that returns a random value between -1 and 1
        based on the input x and y values.
        """
        random.seed(x * 1337 + y * 7331)
        return random.uniform(-1, 1)

    def SetNoise(self):
        temp = np.zeros((34, 34), dtype=np.float32)
        for i in range(1, 33):
            for j in range(1, 33):               
                temp[i][j] = 128.0 + (self.noise(i,j)) *128.0
      

        
        for i in range(1, 33):
            temp[0][i] = temp[32][i]
            temp[33][i] = temp[1][i]
            temp[i][0] = temp[i][32]
            temp[i][33] = temp[i][1]
        temp[0][0] = temp[32][32]
        temp[33][33] = temp[1][1]
        temp[0][33] = temp[32][1]
        temp[33][0] = temp[1][32]
        
        
    # 4 2 12      
        
        for i in range(1, 33):
            for j in range(1, 33):
                center = temp[i][j]/4
                sides = (temp[i+1][j] + temp[i-1][j] + temp[i][j+1] + temp[i][j-1])/2.0
                corners = (temp[i+1][j+1] + temp[i+1][j-1] + temp[i-1][j+1] + temp[i-1][j-1])/12.0
                
                self.map32[i-1][j-1] = center +sides+corners
        #self.smooth()

        

    def smooth(self,type="mean",kernel=3) : # type : convol, mean, median, sd...
        img = np.array(self.map32)
        img1 = img.copy()
        border = (kernel-1)/2
        border = int(border)
        if (len(img.shape)==3) :
            colored = img.shape[2]
        else : 
            img = img.reshape(img.shape[0],img.shape[1],1)
            img1 =img1.reshape(img1.shape[0],img1.shape[1],1)
            colored = 1
        for color in range(0,colored) :
            lignemax = (img.shape[0]-border-1)
            lignemax = int(lignemax)
            for ligne in range(0,img.shape[0]) :
                for colonne in range(0,img.shape[1]) :
                    lignemin = (ligne-border)
                    if (lignemin<0) :lignemin=0
                    lignemax = (ligne+border+1) 
                    if (lignemax>(img.shape[0]-1)) : lignemax = img.shape[0]-1
                    colmin = (colonne-border)
                    if colmin < 0 : colmin=0
                    colmax = (colonne+border+1)
                    if colmax>(img.shape[1]-1) : colmax = img.shape[1]-1
                    extrait = img[lignemin:lignemax,colmin:colmax,(color):(color+1)]
                    if type == "mean" :
                        new_value = np.mean(extrait)
                    elif type == "median" :
                        new_value = np.median(extrait)
                    elif type == "sd" :
                        new_value = np.std(extrait, ddof  =1)
                    img1[ligne,colonne,color] =  new_value
        if (colored==1):
            img1 = img1.reshape(img.shape[0],img.shape[1])
        self.map32 = np.asarray(img1)     

                
        
    
                
    def Interpolate(self, x, y, map):
        Xint = int(x)
        Yint = int(y)

        Xfrac = x - Xint
        Yfrac = y - Yint

        X0 = Xint % 32
        Y0 = Yint % 32
        X1 = (Xint + 1) % 32
        Y1 = (Yint + 1) % 32

        bot = map[X0][Y0] + Xfrac * (map[X1][Y0] - map[X0][Y0])
        top = map[X0][Y1] + Xfrac * (map[X1][Y1] - map[X0][Y1])

        return (bot + Yfrac * (top - bot))
        

    def OverlapOctaves(self, map32, map256):
        # Reset all values in map256 to 0
        for i in range(len(map256)):
            map256[i] = 0.0

        # Iterate over 4 octaves
        for octave in range(4):
            # Iterate over each pixel in the 256x256 map
            for x in range(256):
                for y in range(256):
                    # Calculate the scale and noise for this pixel and octave
                    scale = 1.0 / pow(2, 3 - octave)
                    noise = self.Interpolate(x * scale, y * scale, map32)

                    # Add the noise value to the corresponding pixel in map256
                    map256[y][x] += noise / pow(2, octave)
                    
        tex = Image.fromarray(map256)
        tex.show()
                    
    def ExpFilter(self, map):
        cover = 20.0
        sharpness = 0.95

        for x in range(256):
            for y in range(256):
                c = map[x][y] - (255.0 - cover)
                if c < 0:
                    c = 0
                map[x][y] = 255.0 - (pow(sharpness, c) * 255.0)
            
    


    