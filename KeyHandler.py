import glfw
import OpenGL as GL

#se charge d'appeller les méthodes qui correspondent a chaque keypressed ( utile pour séparer les event du core)

class KeyHandler():
    def __init__(self,camera, _win, key, _scancode, action, _mods):
        if action == glfw.PRESS or action == glfw.REPEAT:
            if key == glfw.KEY_ESCAPE or key == glfw.KEY_Q:
                glfw.set_window_should_close(self.win, True)
            if key == glfw.KEY_Z:
                GL.glPolygonMode(GL.GL_FRONT_AND_BACK, next(self.fill_modes))
            if key == glfw.KEY_R:
                glfw.set_time(0.0)
            if  key== glfw.KEY_W:
                self.camera.move_keyboard("forward", self.delta_time)
            if  key== glfw.KEY_S:
                self.camera.move_keyboard("backward", self.delta_time)
            if  key== glfw.KEY_A:
                self.camera.move_keyboard("left", self.delta_time)
            if  key== glfw.KEY_D:
                self.camera.move_keyboard("right", self.delta_time)
            if  key== glfw.KEY_SPACE:
                self.camera.move_keyboard("up", self.delta_time)
            if  key== glfw.KEY_X:
                self.camera.move_keyboard("down", self.delta_time) 
            if key == glfw.KEY_ENTER:
                print("Début de l'animation")
                #ici on fait juste le call de la clé (comme animation rocks est le seul obj avec un key_handler)
                self.key_handler(key)                        
        elif action == glfw.RELEASE:
            if key == glfw.KEY_W or key == glfw.KEY_S or key == glfw.KEY_A or key == glfw.KEY_D or key == glfw.KEY_SPACE or key == glfw.KEY_X :
                self.camera.stop_keyboard()
            # call Node.key_handler which calls key_handlers for all drawables
            self.key_handler(key)

       
    def KeyHandling_WithCamera (self,camera, _win, key, _scancode, action, _mods):
        pass
    
    def KeyHandling_NoCamera (self,camera, _win, key, _scancode, action, _mods):
        pass