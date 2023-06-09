# Python built-in modules
import os                           # os function, i.e. checking file status
from itertools import cycle         # allows easy circular choice list
import atexit                       # launch a function at exit

# External, non built-in modules
import OpenGL.GL as GL              # standard Python OpenGL wrapper
import glfw                         # lean window system wrapper for OpenGL
import numpy as np                  # all matrix manipulations & OpenGL args
import assimpcy                     # 3D resource loader

# our transform functions
from transform import identity, vec, FlyoutCamera
from waterFrameBuffer import WaterFrameBuffers
from shadowFrameBuffer import ShadowFrameBuffer
from quad import Quad
import water
from texture import Textured
from shadow_map_manager import ShadowMapManager
import cloud
import particles

#text functions
from renderText import RenderText

# initialize and automatically terminate glfw on exit
glfw.init()
atexit.register(glfw.terminate)


# ------------ low level OpenGL object wrappers ----------------------------
class Shader:
    """ Helper class to create and automatically destroy shader program """
    @staticmethod
    def _compile_shader(src, shader_type):
        src = open(src, 'r').read() if os.path.exists(src) else src
        src = src.decode('ascii') if isinstance(src, bytes) else src
        shader = GL.glCreateShader(shader_type)
        GL.glShaderSource(shader, src)
        GL.glCompileShader(shader)
        status = GL.glGetShaderiv(shader, GL.GL_COMPILE_STATUS)
        src = ('%3d: %s' % (i+1, l) for i, l in enumerate(src.splitlines()))
        if not status:
            log = GL.glGetShaderInfoLog(shader).decode('ascii')
            GL.glDeleteShader(shader)
            src = '\n'.join(src)
            print('Compile failed for %s\n%s\n%s' % (shader_type, log, src))
            os._exit(1)
        return shader

    def __init__(self, vertex_source, fragment_source, geom_source=None, debug=False):
        """ Shader can be initialized with raw strings or source file names """
        vert = self._compile_shader(vertex_source, GL.GL_VERTEX_SHADER)
        frag = self._compile_shader(fragment_source, GL.GL_FRAGMENT_SHADER)
        if (not geom_source is None):
            geom = self._compile_shader(geom_source, GL.GL_GEOMETRY_SHADER)
        if vert and frag:
            self.glid = GL.glCreateProgram()  # pylint: disable=E1111
            GL.glAttachShader(self.glid, vert)
            GL.glAttachShader(self.glid, frag)
            if (not geom_source is None):
                GL.glAttachShader(self.glid, geom)
            GL.glLinkProgram(self.glid)
            GL.glDeleteShader(vert)
            GL.glDeleteShader(frag)
            if (not geom_source is None):
                GL.glDeleteShader(geom)
            status = GL.glGetProgramiv(self.glid, GL.GL_LINK_STATUS)
            if not status:
                print(GL.glGetProgramInfoLog(self.glid).decode('ascii'))
                os._exit(1)

        # get location, size & type for uniform variables using GL introspection
        self.uniforms = {}
        self.debug = debug
        get_name = {int(k): str(k).split()[0] for k in self.GL_SETTERS.keys()}
        for var in range(GL.glGetProgramiv(self.glid, GL.GL_ACTIVE_UNIFORMS)):
            name, size, type_ = GL.glGetActiveUniform(self.glid, var)
            name = name.decode().split('[')[0]   # remove array characterization
            args = [GL.glGetUniformLocation(self.glid, name), size]
            # add transpose=True as argument for matrix types
            if type_ in {GL.GL_FLOAT_MAT2, GL.GL_FLOAT_MAT3, GL.GL_FLOAT_MAT4}:
                args.append(True)
            if debug:
                call = self.GL_SETTERS[type_].__name__
                print(f'uniform {get_name[type_]} {name}: {call}{tuple(args)}')
            self.uniforms[name] = (self.GL_SETTERS[type_], args)

    def set_uniforms(self, uniforms):
        """ set only uniform variables that are known to shader """
        for name in uniforms.keys() & self.uniforms.keys():
            set_uniform, args = self.uniforms[name]
            set_uniform(*args, uniforms[name])

    def __del__(self):
        GL.glDeleteProgram(self.glid)  # object dies => destroy GL object

    GL_SETTERS = {
        GL.GL_UNSIGNED_INT:      GL.glUniform1uiv,
        GL.GL_UNSIGNED_INT_VEC2: GL.glUniform2uiv,
        GL.GL_UNSIGNED_INT_VEC3: GL.glUniform3uiv,
        GL.GL_UNSIGNED_INT_VEC4: GL.glUniform4uiv,
        GL.GL_FLOAT:      GL.glUniform1fv, GL.GL_FLOAT_VEC2:   GL.glUniform2fv,
        GL.GL_FLOAT_VEC3: GL.glUniform3fv, GL.GL_FLOAT_VEC4:   GL.glUniform4fv,
        GL.GL_INT:        GL.glUniform1iv, GL.GL_INT_VEC2:     GL.glUniform2iv,
        GL.GL_INT_VEC3:   GL.glUniform3iv, GL.GL_INT_VEC4:     GL.glUniform4iv,
        GL.GL_SAMPLER_1D: GL.glUniform1iv, GL.GL_SAMPLER_2D:   GL.glUniform1iv,
        GL.GL_SAMPLER_3D: GL.glUniform1iv, GL.GL_SAMPLER_CUBE: GL.glUniform1iv,
        GL.GL_FLOAT_MAT2: GL.glUniformMatrix2fv,
        GL.GL_FLOAT_MAT3: GL.glUniformMatrix3fv,
        GL.GL_FLOAT_MAT4: GL.glUniformMatrix4fv,
        GL.GL_SAMPLER_2D_SHADOW: GL.glUniform1iv,
        GL.GL_SAMPLER_2D_ARRAY: GL.glUniform1iv,
    }


class VertexArray:
    """ helper class to create and self destroy OpenGL vertex array objects."""
    def __init__(self, shader, attributes, index=None, usage=GL.GL_STATIC_DRAW):
        """ Vertex array from attributes and optional index array. Vertex
            Attributes should be list of arrays with one row per vertex. """

        # create vertex array object, bind it
        self.glid = GL.glGenVertexArrays(1)
        GL.glBindVertexArray(self.glid)
        self.buffers = {}  # we will store buffers in a named dict
        nb_primitives, size = 0, 0

        # load buffer per vertex attribute (in list with index = shader layout)
        for name, data in attributes.items():
            #print (shader.name, name, data)
            loc = GL.glGetAttribLocation(shader.glid, name)
            #print (loc)
            if loc >= 0:
                # bind a new vbo, upload its data to GPU, declare size and type
                self.buffers[name] = GL.glGenBuffers(1)
                data = np.array(data, np.float32, copy=False)  # ensure format
                nb_primitives, size = data.shape
                GL.glEnableVertexAttribArray(loc)
                GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.buffers[name])
                GL.glBufferData(GL.GL_ARRAY_BUFFER, data, usage)
                GL.glVertexAttribPointer(loc, size, GL.GL_FLOAT, False, 0, None)

        # optionally create and upload an index buffer for this object
        self.draw_command = GL.glDrawArrays
        self.arguments = (0, nb_primitives)
        if index is not None:
            self.buffers['index'] = GL.glGenBuffers(1)
            index_buffer = np.array(index, np.int32, copy=False)  # good format
            GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, self.buffers['index'])
            GL.glBufferData(GL.GL_ELEMENT_ARRAY_BUFFER, index_buffer, usage)
            self.draw_command = GL.glDrawElements
            self.arguments = (index_buffer.size, GL.GL_UNSIGNED_INT, None)

    def execute(self, primitive, attributes=None):
        """ draw a vertex array, either as direct array or indexed array """

        # optionally update the data attribute VBOs, useful for e.g. particles
        attributes = attributes or {}
        for name, data in attributes.items():
            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.buffers[name])
            GL.glBufferSubData(GL.GL_ARRAY_BUFFER, 0, data)
        GL.glBindVertexArray(self.glid)
        self.draw_command(primitive, *self.arguments)

    def __del__(self):  # object dies => kill GL array and buffers from GPU
        GL.glDeleteVertexArrays(1, [self.glid])
        GL.glDeleteBuffers(len(self.buffers), list(self.buffers.values()))


# ------------  Mesh is the core drawable -------------------------------------
class Mesh:
    """ Basic mesh class, attributes and uniforms passed as arguments """
    def __init__(self, shader, attributes, index=None,
                 usage=GL.GL_STATIC_DRAW, **uniforms):
        self.shader = shader
        self.uniforms = uniforms
        self.vertex_array = VertexArray(shader, attributes, index, usage)

    def draw(self, primitives=GL.GL_TRIANGLES, attributes=None, **uniforms):
        GL.glUseProgram(self.shader.glid)
        self.shader.set_uniforms({**self.uniforms, **uniforms})
        self.vertex_array.execute(primitives, attributes)


# ------------  Node is the core drawable for hierarchical scene graphs -------
class Node:
    """ Scene graph transform and parameter broadcast node """
    def __init__(self, children=(), transform=identity()):
        self.transform = transform
        self.world_transform = identity()
        self.children = list(iter(children))

    def add(self, *drawables):
        """ Add drawables to this node, simply updating children list """
        self.children.extend(drawables)

    def draw(self, model=identity(), draw_water_flag=True, draw_cloud_flag=True, **other_uniforms):
        """ Recursive draw, passing down updated model matrix. """
        self.world_transform = model @ self.transform
        for child in self.children:
            if (not isinstance(child, water.Water) or draw_water_flag): 
                if ( isinstance(child, cloud.Cloud)):
                    if (not draw_cloud_flag):
                        continue
                    GL.glDisable(GL.GL_CULL_FACE)
                    child.draw(model=self.world_transform, **other_uniforms)
                    GL.glEnable(GL.GL_CULL_FACE)
                elif (isinstance(child, particles.ParticlesEmitter)):
                    if (child.get_activity()):
                        GL.glDisable(GL.GL_CULL_FACE)
                        child.draw(model=self.world_transform, **other_uniforms)
                        GL.glEnable(GL.GL_CULL_FACE)
                    else:
                        continue
                else:
                    child.draw(model=self.world_transform, **other_uniforms)

    # remove nodes once they aren't needed anymore
    def remove(self, *drawables):
        """ Add drawables to this node, simply updating children list """
        self.children.remove(*drawables)


    def key_handler(self, key):
        """ Dispatch keyboard events to children with key handler """
        for child in (c for c in self.children if hasattr(c, 'key_handler')):
            child.key_handler(key)
    



# -------------- 3D resource loader -------------------------------------------
MAX_BONES = 128

# optionally load texture module
try:
    from texture import Texture, Textured
except ImportError:
    Texture, Textured = None, None

# optionally load animation module
try:
    from animation import KeyFrameControlNode, Skinned
except ImportError:
    KeyFrameControlNode, Skinned = None, None


def load(file, shader, tex_file=None, **params):
    """ load resources from file using assimp, return node hierarchy """
    try:
        pp = assimpcy.aiPostProcessSteps
        flags = pp.aiProcess_JoinIdenticalVertices | pp.aiProcess_FlipUVs
        flags |= pp.aiProcess_OptimizeMeshes | pp.aiProcess_Triangulate
        flags |= pp.aiProcess_GenSmoothNormals
        flags |= pp.aiProcess_ImproveCacheLocality
        flags |= pp.aiProcess_RemoveRedundantMaterials
        scene = assimpcy.aiImportFile(file, flags)
    except assimpcy.all.AssimpError as exception:
        print('ERROR loading', file + ': ', exception.args[0].decode())
        return []
    # ----- Pre-load textures; embedded textures not supported at the moment
    path = os.path.dirname(file) if os.path.dirname(file) != '' else './'
    for mat in scene.mMaterials:
        if tex_file:
            tfile = tex_file
        elif 'TEXTURE_BASE' in mat.properties:  # texture token
            name = mat.properties['TEXTURE_BASE'].split('/')[-1].split('\\')[-1]
            # search texture in file's whole subdir since path often screwed up
            paths = os.walk(path, followlinks=True)
            tfile = next((os.path.join(d, f) for d, _, n in paths for f in n
                     if name.startswith(f) or f.startswith(name)), None)
            assert tfile, 'Cannot find texture %s in %s subtree' % (name, path)
        else:
            tfile = None
        if Texture is not None and tfile:
            mat.properties['diffuse_map'] = Texture(tex_file=tfile)

    # ----- load animations
    def conv(assimp_keys, ticks_per_second):
        """ Conversion from assimp key struct to our dict representation """
        return {key.mTime / ticks_per_second: key.mValue for key in assimp_keys}

    # load first animation in scene file (could be a loop over all animations)
    transform_keyframes = {}
    if scene.HasAnimations:
        anim = scene.mAnimations[0]
        for channel in anim.mChannels:
            # for each animation bone, store TRS dict with {times: transforms}
            transform_keyframes[channel.mNodeName] = (
                conv(channel.mPositionKeys, anim.mTicksPerSecond),
                conv(channel.mRotationKeys, anim.mTicksPerSecond),
                conv(channel.mScalingKeys, anim.mTicksPerSecond)
            )

    # ---- prepare scene graph nodes
    nodes = {}                                       # nodes name -> node lookup
    nodes_per_mesh_id = [[] for _ in scene.mMeshes]  # nodes holding a mesh_id

    def make_nodes(assimp_node):
        """ Recursively builds nodes for our graph, matching assimp nodes """
        keyframes = transform_keyframes.get(assimp_node.mName, None)
        if keyframes and KeyFrameControlNode:
            node = KeyFrameControlNode(*keyframes, assimp_node.mTransformation)
        else:
            node = Node(transform=assimp_node.mTransformation)
        nodes[assimp_node.mName] = node
        for mesh_index in assimp_node.mMeshes:
            nodes_per_mesh_id[mesh_index] += [node]
        node.add(*(make_nodes(child) for child in assimp_node.mChildren))
        return node

    root_node = make_nodes(scene.mRootNode)

    # ---- create optionally decorated (Skinned, Textured) Mesh objects
    for mesh_id, mesh in enumerate(scene.mMeshes):
        # retrieve materials associated to this mesh
        mat = scene.mMaterials[mesh.mMaterialIndex].properties

        # initialize mesh with args from file, merge and override with params
        index = mesh.mFaces
        uniforms = dict(
            k_d=mat.get('COLOR_DIFFUSE', (1, 1, 1)),
            k_s=mat.get('COLOR_SPECULAR', (1, 1, 1)),
            k_a=mat.get('COLOR_AMBIENT', (0.4, 0.4, 0.4)),
            s=mat.get('SHININESS', 32),
            
        )
        attributes = dict(
            position=mesh.mVertices,
            normal=mesh.mNormals,
        )
        # ---- optionally add texture coordinates attribute if present
        if mesh.HasTextureCoords[0]:
            attributes.update(tex_coord=mesh.mTextureCoords[0])

        # --- optionally add vertex colors as attributes if present
        if mesh.HasVertexColors[0]:
            attributes.update(color=mesh.mColors[0])

        # ---- compute and add optional skinning vertex attributes
        if mesh.HasBones:
            # skinned mesh: weights given per bone => convert per vertex for GPU
            # first, populate an array with MAX_BONES entries per vertex
            vbone = np.array([[(0, 0)] * MAX_BONES] * mesh.mNumVertices,
                             dtype=[('weight', 'f4'), ('id', 'u4')])
            for bone_id, bone in enumerate(mesh.mBones[:MAX_BONES]):
                for entry in bone.mWeights:  # need weight,id pairs for sorting
                    vbone[entry.mVertexId][bone_id] = (entry.mWeight, bone_id)

            vbone.sort(order='weight')   # sort rows, high weights last
            vbone = vbone[:, -4:]        # limit bone size, keep highest 4

            attributes.update(bone_ids=vbone['id'],
                              bone_weights=vbone['weight'])

        new_mesh = Mesh(shader, attributes, index, **{**uniforms, **params})

        if Textured is not None and 'diffuse_map' in mat:
            new_mesh = Textured(new_mesh, diffuse_map=mat['diffuse_map'])
        if Skinned and mesh.HasBones:
            # make bone lookup array & offset matrix, indexed by bone index (id)
            bone_nodes = [nodes[bone.mName] for bone in mesh.mBones]
            bone_offsets = [bone.mOffsetMatrix for bone in mesh.mBones]
            new_mesh = Skinned(new_mesh, bone_nodes, bone_offsets)
        for node_to_populate in nodes_per_mesh_id[mesh_id]:
            node_to_populate.add(new_mesh)

    nb_triangles = sum((mesh.mNumFaces for mesh in scene.mMeshes))
    print('Loaded', file, '\t(%d meshes, %d faces, %d nodes, %d animations)' %
          (scene.mNumMeshes, nb_triangles, len(nodes), scene.mNumAnimations))
    return [root_node]

def timer():
    return glfw.get_time()


# ------------  Viewer class & window management ------------------------------
class Viewer(Node):
    """ GLFW viewer window, with classic initialization & graphics loop """

    def __init__(self, width=1280, height=720):
        super().__init__()

        # version hints: create GL window with >= OpenGL 3.3 and core profile
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL.GL_TRUE)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.RESIZABLE, True)
        self.win = glfw.create_window(width, height, 'Viewer', None, None)

        # make win's OpenGL context current; no OpenGL calls can happen before
        glfw.make_context_current(self.win)

        # initialize FlyoutCamera
        self.camera = FlyoutCamera(position=vec(0.0,0.0,1.0))
        self.mouse = (0, 0)

        # register event handlers
        glfw.set_key_callback(self.win, self.on_key)
        glfw.set_cursor_pos_callback(self.win, self.on_mouse_move)
        glfw.set_scroll_callback(self.win, self.on_scroll)
        glfw.set_window_size_callback(self.win, self.on_size)

        # useful message to check OpenGL renderer characteristics
        print('OpenGL', GL.glGetString(GL.GL_VERSION).decode() + ', GLSL',
              GL.glGetString(GL.GL_SHADING_LANGUAGE_VERSION).decode() +
              ', Renderer', GL.glGetString(GL.GL_RENDERER).decode())

        # initialize GL by setting viewport and default render characteristics
        GL.glClearColor(0, 0, 0.2, 1)
        GL.glEnable(GL.GL_CULL_FACE)   # backface culling enabled (TP2)
        GL.glEnable(GL.GL_DEPTH_TEST)  # depth test now enabled (TP2)

        # cyclic iterator to easily toggle polygon rendering modes
        self.fill_modes = cycle([GL.GL_LINE, GL.GL_POINT, GL.GL_FILL])

        #init global light
        self.main_light = (4,1,4)
        self.DAY_TIME = 30 #tps du jour en secondes

        #init lava_starting to flow flag and particles starting to appear flag
        self.flag_lava_start = 0
        self.launch_particles = False
        
        self.waterFrameBuffers = WaterFrameBuffers(self.win)
        self.shadowFrameBuffer = ShadowFrameBuffer(self.win)
        self.shadow_map_manager = ShadowMapManager(10.0,1.0,15.0, 200.0)
        
        # inti shader used for animation
        self.shader = Shader("glsl/texture.vert", "glsl/texture.frag")

    def run(self):
        """ Main render loop for this OpenGL window """

        #init time counter
        self.last_time = timer()

        quadShader = Shader("glsl/fboviz.vert", "glsl/fboviz.frag")

        # setup quad mesh for FBO vizualisation
        base_coords = ((-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0))
        indices = np.array((1, 3, 0, 1 , 2 , 3), np.uint32)
        texcoords = ([0,0], [1, 0], [1, 1], [0, 1])
        mesh = Mesh(quadShader, attributes=dict(position=base_coords, tex_coord=texcoords), index=indices)

        WATER_HEIGHT = -40 # Should be synced with water height from water.py
        WAVE_SPEED_FACTOR = 0.02
        reflection_clip_plane = (0.0,1.0,0.0,-WATER_HEIGHT+0.5) # 4th param = -(water height) + small overlap to prevent glitches
        refraction_clip_plane = (0.0,-1.0,0.0,WATER_HEIGHT+0.5)  # = water height
        fog = (0.75,0.4,0.25)

        print(f'\n============== CONTROLS ==============\n'
            f' WASD       : move the camera forward/backward/left/right\n'
            f' X/SPACE    : move the camera down/up\n'
            f' Enter      : (re)launch the animation\n'
            f' R          : restart the global timer\n'
            f' W          : show the wireframe/vertex view\n'
            f' LeftClick  : change camera orientation\n'
            f' RightClick : pan the camera in the scene\n'
            f' ScrollWheel: change the fov of the camera\n')

        while not glfw.window_should_close(self.win):

            current_time = timer()
            self.delta_time = current_time - self.last_time
            self.last_time = current_time
                
            # clear draw buffer and depth buffer (<-TP2)
            GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

            win_size = glfw.get_window_size(self.win)
            self.main_light = ( 256 * np.cos(timer() / self.DAY_TIME), 256 * np.abs(np.sin(timer () / self.DAY_TIME)), 
                               np.abs(256 * np.sin(timer() / self.DAY_TIME)) )
            cam_pos = np.linalg.inv(self.camera.view_matrix())[:, 3]

            self.particles_emitter.update(self.delta_time, cam_pos[:3], self.launch_particles)

            # draw our scene objects
            self.shadowFrameBuffer.bindFrameBuffer()
            GL.glEnable(GL.GL_DEPTH_CLAMP) # so that object in front of the frustum can still cast shadows
            light_view, light_projection = self.shadow_map_manager.compute_matrices_for_shadow_mapping(self.main_light, 
                                                                                                       self.camera, cam_pos,
                                                                                                       win_size)
 
            self.draw(view=light_view,
                      projection=light_projection,
                      model=identity(),
                      draw_water_flag = False,
                      draw_cloud_flag = False,
                      light_dir=self.main_light)
            GL.glDisable(GL.GL_DEPTH_CLAMP)
            self.shadowFrameBuffer.unbindCurrentFrameBuffer()

            self.waterFrameBuffers.bindReflectionFrameBuffer()
            GL.glEnable(GL.GL_CLIP_PLANE0) # for reflection/refraction clip planes
            
            self.camera.underwater_cam(WATER_HEIGHT)
            self.draw(view=self.camera.view_matrix(),
                      projection=self.camera.projection_matrix(win_size),
                      model=identity(),
                      draw_water_flag = False,
                      w_camera_position=self.camera.position,
                      light_dir=self.main_light,
                      fog_color=fog,
                      time_of_day = self.getCurrentTimeOfDay(),
                      clipping_plane= reflection_clip_plane,
                      light_space_matrix = light_projection @ light_view,
                      shadow_distance=self.shadow_map_manager.getShadowDistance())
            self.camera.underwater_cam(WATER_HEIGHT)
            self.waterFrameBuffers.unbindCurrentFrameBuffer()
            self.waterFrameBuffers.bindRefractionFrameBuffer()
            self.draw(view=self.camera.view_matrix(),
                      projection=self.camera.projection_matrix(win_size),
                      model=identity(),
                      draw_water_flag = False,
                      w_camera_position=cam_pos,
                      light_dir=self.main_light,
                      fog_color=fog,
                      time_of_day = self.getCurrentTimeOfDay(),
                      clipping_plane= refraction_clip_plane,
                      light_space_matrix = light_projection @ light_view,
                      shadow_distance=self.shadow_map_manager.getShadowDistance())
            self.waterFrameBuffers.unbindCurrentFrameBuffer()
            GL.glDisable(GL.GL_CLIP_PLANE0) # for reflection/refraction clip planes
            GL.glEnable(GL.GL_FRAMEBUFFER_SRGB)
            
            #if pour la lave ou non 
            time=0
            if (self.flag_lava_start != 0) :
                time = timer() - self.flag_lava_start
            
            
            self.draw(view=self.camera.view_matrix(),
                    projection=self.camera.projection_matrix(win_size),
                    model=identity(),
                    w_camera_position=cam_pos,
                    light_dir=self.main_light,
                    fog_color=fog,
                    time_of_day = self.getCurrentTimeOfDay(),
                    displacement_speed = current_time * WAVE_SPEED_FACTOR % 1,
                    lava_speed = min(time / 30 , 1.0),
                    near = self.camera.near_clip,
                    far = self.camera.far_clip,           
                    light_space_matrix = light_projection @ light_view,
                    shadow_distance=self.shadow_map_manager.getShadowDistance())
        
            GL.glDisable(GL.GL_FRAMEBUFFER_SRGB)
            #Draw the FBOS texture in a quad in the corner of the screen
            #Quad(self.shadowFrameBuffer.getDepthTexture(), mesh).draw(model=identity())
            
            
            # flush render commands, and swap draw buffers
            glfw.swap_buffers(self.win)

            # Poll for and process events
            glfw.poll_events()

    def on_key(self, _win, key, _scancode, action, _mods):
        #print( "position camera = ",self.camera.position)
        """ 'Q' or 'Escape' quits """
        if action == glfw.PRESS or action == glfw.REPEAT:
            self.key_handler(key)
            if key == glfw.KEY_ESCAPE or key == glfw.KEY_Q:
                glfw.set_window_should_close(self.win, True)
            if key == glfw.KEY_Z:
                GL.glPolygonMode(GL.GL_FRONT_AND_BACK, next(self.fill_modes))
            if key == glfw.KEY_R:
                glfw.set_time(0.0)
                self.flag_lava_start = 0
                self.launch_particles = False
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
            if key== glfw.KEY_ENTER and action==glfw.PRESS:
                self.flag_lava_start = timer() - 3
                self.launch_particles = True
        elif action == glfw.RELEASE:
            if key == glfw.KEY_W or key == glfw.KEY_S or key == glfw.KEY_A or key == glfw.KEY_D or key == glfw.KEY_SPACE or key == glfw.KEY_X :
                self.camera.stop_keyboard()
            

    def on_mouse_move(self, win, xpos, ypos):
        """ Rotate on left-click & drag, pan on right-click & drag """
        old = self.mouse
        self.mouse = (xpos, glfw.get_window_size(win)[1] - ypos)
        if glfw.get_mouse_button(win, glfw.MOUSE_BUTTON_LEFT):
            self.camera.rotate(old, self.mouse, self.delta_time)
        if glfw.get_mouse_button(win, glfw.MOUSE_BUTTON_RIGHT):
            self.camera.pan(old, self.mouse)
 
    def on_scroll(self, win, _deltax, deltay):
        """ Scroll controls the camera distance to trackball center """
        self.camera.zoom(deltay)

    def on_size(self, _win, _width, _height):
        """ window size update => update viewport to new framebuffer size """
        GL.glViewport(0, 0, *glfw.get_framebuffer_size(self.win))

    def getLightPos(self):
        return self.main_light
    
    def getCurrentTimeOfDay(self):
        """ return a value between 1 (day) and 0 (night) to be used in the skyboxShader"""
        t = timer()
        return (np.cos((t*np.pi)/self.DAY_TIME)+1)/2
    
    def getWaterFrameBuffers(self):
        return self.waterFrameBuffers
    
    def getShadowFrameBuffer(self):
        return self.shadowFrameBuffer
    
    def setParticlesEmitter(self, emitter):
        self.particles_emitter = emitter
    