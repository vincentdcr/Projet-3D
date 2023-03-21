import OpenGL.GL as GL              # standard Python OpenGL wrapper
import glfw                         # lean window system wrapper for OpenGL

# Class obtained from ThinMatrix tutorial, rewritten by us in Python


class WaterFrameBuffers:

    REFLECTION_WIDTH = 320
    REFLECTION_HEIGHT = 180
    
    REFRACTION_WIDTH = 1280
    REFRACTION_HEIGHT = 720

    reflectionFrameBuffer = 0
    reflectionTexture = 0
    reflectionDepthBuffer = 0
    
    refractionFrameBuffer = 0
    refractionTexture = 0
    refractionDepthTexture = 0
    
    def __init__(self, window):
        self.win = window
        self.initialiseReflectionFrameBuffer()
        self.initialiseRefractionFrameBuffer()

    def initialiseReflectionFrameBuffer(self):
        self.reflectionFrameBuffer = self.createFrameBuffer()
        self.reflectionTexture = self.createTextureAttachment(self.REFLECTION_WIDTH,self.REFLECTION_HEIGHT)
        self.reflectionDepthBuffer = self.createDepthBufferAttachment(self.REFLECTION_WIDTH,self.REFLECTION_HEIGHT)
        self.unbindCurrentFrameBuffer()
    
    def initialiseRefractionFrameBuffer(self):
        self.refractionFrameBuffer = self.createFrameBuffer()
        self.refractionTexture = self.createTextureAttachment(self.REFRACTION_WIDTH,self.REFRACTION_HEIGHT)
        self.refractionDepthTexture = self.createDepthTextureAttachment(self.REFRACTION_WIDTH,self.REFRACTION_HEIGHT)
        self.unbindCurrentFrameBuffer()    
   
    def createFrameBuffer(self):
        frameBuffer = GL.glGenFramebuffers(1)
        #generate name for frame buffer
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, frameBuffer)
        #create the framebuffer
        GL.glDrawBuffer(GL.GL_COLOR_ATTACHMENT0)
        #indicate that we will always render to color attachment 0
        return frameBuffer

    def createTextureAttachment(self,width,height):
        texture = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, texture)
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGB, width, height, 0, GL.GL_RGB, GL.GL_UNSIGNED_BYTE, None)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)
        GL.glFramebufferTexture2D(GL.GL_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT0, GL.GL_TEXTURE_2D, texture, 0)
        return texture

    def createDepthTextureAttachment(self, width,height):
        texture = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, texture)
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_DEPTH_COMPONENT32, width, height, 0, GL.GL_DEPTH_COMPONENT, GL.GL_FLOAT,  None)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
        GL.glFramebufferTexture(GL.GL_FRAMEBUFFER, GL.GL_DEPTH_ATTACHMENT, texture, 0)
        return texture

    def createDepthBufferAttachment(self, width, height):
        depthBuffer = GL.glGenRenderbuffers(1)
        GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, depthBuffer)
        GL.glRenderbufferStorage(GL.GL_RENDERBUFFER, GL.GL_DEPTH_COMPONENT, width, height)
        GL.glFramebufferRenderbuffer(GL.GL_FRAMEBUFFER, GL.GL_DEPTH_ATTACHMENT, GL.GL_RENDERBUFFER, depthBuffer)
        return depthBuffer

    def bindReflectionFrameBuffer(self): #call before rendering to this FBO
        self.bindFrameBuffer(self.reflectionFrameBuffer,self.REFLECTION_WIDTH,self.REFLECTION_HEIGHT)
    
    def bindRefractionFrameBuffer(self): #call before rendering to this FBO
        self.bindFrameBuffer(self.refractionFrameBuffer,self.REFRACTION_WIDTH,self.REFRACTION_HEIGHT)
    
    def unbindCurrentFrameBuffer(self): #call to switch to default frame buffer
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)
        GL.glViewport(0, 0, *glfw.get_framebuffer_size(self.win))

    def getReflectionTexture(self): #get the resulting texture
        return self.reflectionTexture
    
    def getRefractionTexture(self): #get the resulting texture
        return self.refractionTexture
    
    def getRefractionDepthTexture(self): #get the resulting depth texture
        return self.refractionDepthTexture
    
    def bindFrameBuffer(self,frameBuffer,width,height):
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)#To make sure the texture isn't bound
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, frameBuffer)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        GL.glViewport(0, 0, width, height)

    def cleanUp(self):
        GL.glDeleteFramebuffers(self.reflectionFrameBuffer)
        GL.glDeleteTextures(self.reflectionTexture)
        GL.glDeleteRenderbuffers(self.reflectionDepthBuffer)
        GL.glDeleteFramebuffers(self.refractionFrameBuffer)
        GL.glDeleteTextures(self.refractionTexture)
        GL.glDeleteTextures(self.refractionDepthTexture)


