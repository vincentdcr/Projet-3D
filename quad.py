from texture import Texture, Textured

class Quad(Textured):
    """ Simple first textured object """
    def __init__(self, tex, mesh):
        super().__init__(mesh, diffuse_map=tex) 