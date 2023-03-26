import OpenGL.GL as GL              # standard Python OpenGL wrapper
import glfw                         # lean window system wrapper for OpenGL

class ShadowFrameBuffer:
    
    TEX_WIDTH = 4096
    TEX_HEIGHT = 4096
    
    frameBuffer = 0
    depthTexture = 0
    
    def __init__(self, window):
        self.win = window
        self.initialiseFrameBuffer()

    def initialiseFrameBuffer(self):
        self.frameBuffer = self.createFrameBuffer()
        self.depthTexture = self.createDepthTextureAttachment(self.TEX_WIDTH,self.TEX_HEIGHT)
        self.unbindCurrentFrameBuffer()    
   
    def createFrameBuffer(self):
        frameBuffer = GL.glGenFramebuffers(1)
        #generate name for frame buffer
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, frameBuffer)
        #create the framebuffer
        GL.glDrawBuffer(GL.GL_NONE)
        GL.glReadBuffer(GL.GL_NONE)
        return frameBuffer

    def createDepthTextureAttachment(self, width, height):
        texture = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, texture)
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_DEPTH_COMPONENT32, width, height, 0, GL.GL_DEPTH_COMPONENT, GL.GL_FLOAT,  None)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
        # clamp to border to prevent zone outside light's frustum from being in shadow
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_BORDER)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_BORDER) 
        borderColor = (1.0,1.0,1.0,1.0) # by defining the depth of every fragment over the limit to 1.0
        GL.glTexParameterfv(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_BORDER_COLOR, borderColor);  
        # Change the sampler type to a shadow Sampler to get free 2x2 PCF 
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_COMPARE_MODE, GL.GL_COMPARE_REF_TO_TEXTURE)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_COMPARE_FUNC, GL.GL_GEQUAL)
        GL.glFramebufferTexture2D(GL.GL_FRAMEBUFFER, GL.GL_DEPTH_ATTACHMENT, GL.GL_TEXTURE_2D, texture, 0)
        return texture

    def bindFrameBuffer(self): #call before rendering to this FBO
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)#To make sure the texture isn't bound
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.frameBuffer)
        GL.glClear(GL.GL_DEPTH_BUFFER_BIT)
        GL.glViewport(0, 0, self.TEX_WIDTH, self.TEX_HEIGHT)
    
    def unbindCurrentFrameBuffer(self): #call to switch to default frame buffer
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)
        GL.glViewport(0, 0, *glfw.get_framebuffer_size(self.win))

    def getDepthTexture(self): #get the resulting depth texture
        return self.depthTexture

    def cleanUp(self):
        GL.glDeleteFramebuffers(self.refractionFrameBuffer)
        GL.glDeleteTextures(self.refractionTexture)
        GL.glDeleteTextures(self.refractionDepthTexture)


