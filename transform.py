# pylint: disable=invalid-name, bad-whitespace, too-many-arguments
"""
Basic graphics related geometry tools to complement numpy
Quaternion, graphics 4x4 matrices, and vector utilities.
@author: franco
"""
# Python built-in modules
import math                 # mainly for trigonometry functions
from numbers import Number  # useful to check type of arg: scalar or vector?
# external module
import numpy as np          # matrices, vectors & quaternions are numpy arrays
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *


# Some useful functions on vectors -------------------------------------------
def vec(*iterable):
    """ shortcut to make numpy vector of any iterable(tuple...) or vector """
    return np.asarray(iterable if len(iterable) > 1 else iterable[0], 'f')


def normalized(vector):
    """ normalized version of any vector, with zero division check """
    norm = math.sqrt(sum(vector*vector))
    return vector / norm if norm > 0. else vector


def lerp(point_a, point_b, fraction):
    """ linear interpolation between two quantities with linear operators """
    return point_a + fraction * (point_b - point_a)

def calc_normals(vertices, index):
    normals = np.zeros(vertices.shape, dtype=vertices.dtype)
    a = vertices[index[::3]]  # all 1st pts of triangles
    b = vertices[index[1::3]] # all 2nd pts
    c = vertices[index[2::3]]
    ab = b - a
    ac = c - a
    normal = np.cross(ab, ac)
    normal = np.apply_along_axis(normalized, axis=1, arr=normal)
    np.add.at(normals, index[::3], normal)  # we add to normals elements from the index array the values of normal
    np.add.at(normals, index[1::3], normal)
    np.add.at(normals, index[2::3], normal)
    return np.apply_along_axis(normalized, axis=1, arr=normals)


def catmull_rom_spline(p0, p1, p2, p3, t): # that is a test to make things smoother
    return 0.5 * (
        (-t**3 + 2*t**2 - t) * p0
        + (3*t**3 - 5*t**2 + 2) * p1
        + (-3*t**3 + 4*t**2 + t) * p2
        + (t**3 - t**2) * p3
    )
# Typical 4x4 matrix utilities for OpenGL ------------------------------------
def identity():
    """ 4x4 identity matrix """
    return np.identity(4, 'f')


def ortho(left, right, bot, top, near, far):
    """ orthogonal projection matrix for OpenGL """
    dx, dy, dz = right - left, top - bot, far - near
    rx, ry, rz = -(right+left) / dx, -(top+bot) / dy, -(far+near) / dz
    return np.array([[2/dx, 0,    0,     rx],
                     [0,    2/dy, 0,     ry],
                     [0,    0,    -2/dz, rz],
                     [0,    0,    0,     1]], 'f')


def perspective(fovy, aspect, near, far):
    """ perspective projection matrix, from field of view and aspect ratio """
    _scale = 1.0/math.tan(math.radians(fovy)/2.0)
    sx, sy = _scale / aspect, _scale
    zz = (far + near) / (near - far)
    zw = 2 * far * near/(near - far)
    return np.array([[sx, 0,  0,  0],
                     [0,  sy, 0,  0],
                     [0,  0, zz, zw],
                     [0,  0, -1,  0]], 'f')


def frustum(xmin, xmax, ymin, ymax, zmin, zmax):
    """ frustum projection matrix for OpenGL, from min and max coordinates"""
    a = (xmax+xmin) / (xmax-xmin)
    b = (ymax+ymin) / (ymax-ymin)
    c = -(zmax+zmin) / (zmax-zmin)
    d = -2*zmax*zmin / (zmax-zmin)
    sx = 2*zmin / (xmax-xmin)
    sy = 2*zmin / (ymax-ymin)
    return np.array([[sx, 0,  a, 0],
                     [0, sy,  b, 0],
                     [0,  0,  c, d],
                     [0,  0, -1, 0]], 'f')


def translate(x=0.0, y=0.0, z=0.0):
    """ matrix to translate from coordinates (x,y,z) or a vector x"""
    matrix = np.identity(4, 'f')
    matrix[:3, 3] = vec(x, y, z) if isinstance(x, Number) else vec(x)
    return matrix


def scale(x, y=None, z=None):
    """scale matrix, with uniform (x alone) or per-dimension (x,y,z) factors"""
    x, y, z = (x, y, z) if isinstance(x, Number) else (x[0], x[1], x[2])
    y, z = (x, x) if y is None or z is None else (y, z)  # uniform scaling
    return np.diag((x, y, z, 1))


def sincos(degrees=0.0, radians=None):
    """ Rotation utility shortcut to compute sine and cosine of an angle. """
    radians = radians if radians else math.radians(degrees)
    return math.sin(radians), math.cos(radians)


def rotate(axis=(1., 0., 0.), angle=0.0, radians=None):
    """ 4x4 rotation matrix around 'axis' with 'angle' degrees or 'radians' """
    x, y, z = normalized(vec(axis))
    s, c = sincos(angle, radians)
    nc = 1 - c
    return np.array([[x*x*nc + c,   x*y*nc - z*s, x*z*nc + y*s, 0],
                     [y*x*nc + z*s, y*y*nc + c,   y*z*nc - x*s, 0],
                     [x*z*nc - y*s, y*z*nc + x*s, z*z*nc + c,   0],
                     [0,            0,            0,            1]], 'f')


def lookat(eye, target, up):
    """ Computes 4x4 view matrix from 3d point 'eye' to 'target',
        'up' 3d vector fixes orientation """
    view = normalized(vec(target)[:3] - vec(eye)[:3])
    up = normalized(vec(up)[:3])
    right = np.cross(view, up)
    up = np.cross(right, view)
    rotation = np.identity(4)
    rotation[:3, :3] = np.vstack([right, up, -view])
    return rotation @ translate(-eye)


# quaternion functions -------------------------------------------------------
def quaternion(x=vec(0., 0., 0.), y=0.0, z=0.0, w=1.0):
    """ Init quaternion, w=real and, x,y,z or vector x imaginary components """
    x, y, z = (x, y, z) if isinstance(x, Number) else (x[0], x[1], x[2])
    return np.array((w, x, y, z), 'f')


def quaternion_from_axis_angle(axis, degrees=0.0, radians=None):
    """ Compute quaternion from an axis vec and angle around this axis """
    sin, cos = sincos(radians=radians*0.5) if radians else sincos(degrees*0.5)
    return quaternion(normalized(vec(axis))*sin, w=cos)


def quaternion_from_euler(yaw=0.0, pitch=0.0, roll=0.0, radians=None):
    """ Compute quaternion from three euler angles in degrees or radians """
    siy, coy = sincos(yaw * 0.5, radians[0] * 0.5 if radians else None)
    sir, cor = sincos(roll * 0.5, radians[1] * 0.5 if radians else None)
    sip, cop = sincos(pitch * 0.5, radians[2] * 0.5 if radians else None)
    return quaternion(x=coy*sir*cop - siy*cor*sip, y=coy*cor*sip + siy*sir*cop,
                      z=siy*cor*cop - coy*sir*sip, w=coy*cor*cop + siy*sir*sip)


def quaternion_mul(q1, q2):
    """ Compute quaternion which composes rotations of two quaternions """
    return np.dot(np.array([[q1[0], -q1[1], -q1[2], -q1[3]],
                            [q1[1],  q1[0], -q1[3],  q1[2]],
                            [q1[2],  q1[3],  q1[0], -q1[1]],
                            [q1[3], -q1[2],  q1[1],  q1[0]]]), q2)


def quaternion_matrix(q):
    """ Create 4x4 rotation matrix from quaternion q """
    q = normalized(q)  # only unit quaternions are valid rotations.
    nxx, nyy, nzz = -q[1]*q[1], -q[2]*q[2], -q[3]*q[3]
    qwx, qwy, qwz = q[0]*q[1], q[0]*q[2], q[0]*q[3]
    qxy, qxz, qyz = q[1]*q[2], q[1]*q[3], q[2]*q[3]
    return np.array([[2*(nyy + nzz)+1, 2*(qxy - qwz),   2*(qxz + qwy),   0],
                     [2 * (qxy + qwz), 2 * (nxx + nzz) + 1, 2 * (qyz - qwx), 0],
                     [2 * (qxz - qwy), 2 * (qyz + qwx), 2 * (nxx + nyy) + 1, 0],
                     [0, 0, 0, 1]], 'f')


def quaternion_slerp(q0, q1, fraction):
    """ Spherical interpolation of two quaternions by 'fraction' """
    # only unit quaternions are valid rotations.
    q0, q1 = normalized(q0), normalized(q1)
    dot = np.dot(q0, q1)

    # if negative dot product, the quaternions have opposite handedness
    # and slerp won't take the shorter path. Fix by reversing one quaternion.
    q1, dot = (q1, dot) if dot > 0 else (-q1, -dot)

    theta_0 = math.acos(np.clip(dot, -1, 1))  # angle between input vectors
    theta = theta_0 * fraction                # angle between q0 and result
    q2 = normalized(q1 - q0*dot)              # {q0, q2} now orthonormal basis

    return q0*math.cos(theta) + q2*math.sin(theta)


# a trackball class based on provided quaternion functions -------------------
# OLD VERSION - SEE LATER FOR VIEWPORT VERSION
class Trackball:
    """Virtual trackball for 3D scene viewing. Independent of window system."""

    def __init__(self, yaw=0., roll=0., pitch=0., distance=3., radians=None):
        """ Build a new trackball with specified view, angles in degrees """
        self.rotation = quaternion_from_euler(yaw, roll, pitch, radians)
        self.distance = max(distance, 0.001)
        self.pos2d = vec(0.0, 0.0)

    def drag(self, old, new, winsize):
        """ Move trackball from old to new 2d normalized window position """
        old, new = ((2*vec(pos) - winsize) / winsize for pos in (old, new))
        self.rotation = quaternion_mul(self._rotate(old, new), self.rotation)

    def zoom(self, delta, size):
        """ Zoom trackball by a factor delta normalized by window size """
        self.distance = max(0.001, self.distance * (1 - 50*delta/size))

    def pan(self, old, new):
        """ Pan in camera's reference by a 2d vector factor of (new - old) """
        self.pos2d += (vec(new) - old) * 0.005 * self.distance

    def up(self):
        """ Move up vector by a 2d vector factor of (new - old) """
        self.pos2d += -1 * 0.005 * self.distance
        
    def view_matrix(self):
        """ View matrix transformation, including distance to target point """
        return translate(*self.pos2d, -self.distance) @ self.matrix()

    def projection_matrix(self, winsize):
        """ Projection matrix with z-clipping range adaptive to distance """
        z_range = vec(0.1, 100) * self.distance  # proportion to dist
        return perspective(70, winsize[0] / winsize[1], *z_range)

    def matrix(self):
        """ Rotational component of trackball position """
        return quaternion_matrix(self.rotation)

    def _project3d(self, position2d, radius=0.8):
        """ Project x,y on sphere OR hyperbolic sheet if away from center """
        p2, r2 = sum(position2d*position2d), radius*radius
        zcoord = math.sqrt(r2 - p2) if 2*p2 < r2 else r2 / (2*math.sqrt(p2))
        return vec(*position2d, zcoord)

    def _rotate(self, old, new):
        """ Rotation of axis orthogonal to old & new's 3D ball projections """
        old, new = (normalized(self._project3d(pos)) for pos in (old, new))
        phi = 2 * math.acos(np.clip(np.dot(old, new), -1, 1))
        return quaternion_from_axis_angle(np.cross(old, new), radians=phi)
    
    def getRotationMatrix(self):
        R1 = ( 2*self.rotation[0]**2 + 2*self.rotation[1]**2 - 1, 2*self.rotation[1]*self.rotation[2] + 2*self.rotation[0]*self.rotation[3], 2*self.rotation[1]*self.rotation[3] - 2*self.rotation[0]*self.rotation[2] , 0)
        R2 = ( 2*self.rotation[1]*self.rotation[2] - 2*self.rotation[0]*self.rotation[3], 2*self.rotation[0]**2 + 2*self.rotation[2]**2 - 1, 2*self.rotation[2]*self.rotation[3] + 2*self.rotation[0]*self.rotation[1] , 0)
        R3 = ( 2*self.rotation[1]*self.rotation[3] + 2*self.rotation[0]*self.rotation[2], 2*self.rotation[2]*self.rotation[3] - 2*self.rotation[0]*self.rotation[1], 2*self.rotation[0]**2 + 2*self.rotation[3]**2  - 1, 0)
        R4 = ( 0, 0, 0, 1)
        return np.array( [R1, R2, R3], 'f')

    def getDirectionVector(self):
        dir_world = self.getRotationMatrix() @ vec(0.0,0.0,-1.0,0.0)
        return normalized(dir_world)
    
    def getNearFarPlane(self):
        return vec(0.1, 100) * self.distance  # proportion to dist
    
class FlyoutCamera:
    def __init__(self, position=vec(0,0,0), up=vec(0,1,0), pitch=0.0, yaw=math.radians(-90.0), fov=70.0, near_clip=0.1, far_clip=512, sensitivity=0.2, max_speed=90.0, interp_time=0.0):
        self.position = position
        self.w_up = up
        self.pitch = pitch
        self.yaw = yaw
        self.fov = fov
        self.near_clip = near_clip
        self.far_clip = far_clip
        self.sensitivity = sensitivity
        self.max_speed = max_speed
        self.move_speed = 0.0
        self.acceleration = 4.0
        self.interpolation_time = interp_time 
        self.target_yaw = math.radians(-90.0)
        self.target_pitch = 0.0
        self._update()

    def view_matrix(self):
        return lookat(self.position, self.position + self.front, self.up) 

    def projection_matrix(self, winsize):
        return perspective(self.fov, winsize[0] / winsize[1], self.near_clip, self.far_clip)

    def rotate(self, old, new, delta) -> None:
        x_offset = self.sensitivity /15 * (new[0] - old[0])
        y_offset = self.sensitivity /15 * (new[1] - old[1])
    
        self.target_yaw += x_offset
        self.target_yaw = self.target_yaw % (np.pi*2) # to prevent a possible overflow error / high float imprecisions
        self.target_pitch += y_offset
        
        # prevent camera from flipping and singular matrix error
        self.target_pitch = max(math.radians(-89), min(self.target_pitch, math.radians(89)))

        # compute interpolation factor based on time since last input
        if (self.interpolation_time==0):
            t = 1.0
        else:
            t = min(1.0, delta / self.interpolation_time)
        
        # linear interpolation to smoothly move from the current yaw/pitch to the target values
        self.yaw = lerp(self.yaw, self.target_yaw, t)
        self.pitch = lerp(self.pitch, self.target_pitch, t)
        
        self._update()

    def pan(self, old, new) -> None:
        x_offset = self.sensitivity * (new[0] - old[0])
        y_offset = self.sensitivity * (new[1] - old[1])
        self.position += self.right * x_offset + self.up * y_offset

    def zoom(self, delta):
        self.fov -= delta * self.sensitivity
        self.fov = max(min(self.fov, 120), 30)

    def move_keyboard(self, direction, delta):
        self.move_speed = min(self.move_speed + delta * self.max_speed, self.max_speed)
        # logarithmic like acceleration curve up to max speed, normalized
        acceleration_ratio = (1.0 - math.exp(-self.acceleration * delta)) / (1.0 - math.exp(-self.acceleration))

        if direction == "forward":
            self.position += acceleration_ratio * self.move_speed * self.front
        elif direction == "backward":
            self.position -= acceleration_ratio * self.move_speed * self.front
        elif direction == "left":
            self.position -= acceleration_ratio * self.move_speed * self.right
        elif direction == "right":
            self.position += acceleration_ratio * self.move_speed * self.right
        elif direction == "up":
            self.position += acceleration_ratio * self.move_speed * self.up
        elif direction == "down":
            self.position -= acceleration_ratio * self.move_speed * self.up


    def stop_keyboard(self):
        # called if no directional keys are pressed
        self.move_speed = 0.0

    def get_look_direction(self):
        return np.array([
            np.cos(self.yaw) * np.cos(self.pitch),
            np.sin(self.pitch),
            np.sin(self.yaw) * np.cos(self.pitch)
        ])
    
    def underwater_cam(self, water_height):
        # place ourselves at the same distance underwater as we are over it with a flipped pitch
        self.position[1] = self.position[1] - 2*(self.position[1] - water_height)
        self.pitch = -self.pitch
        self._update()

    # we set the yaw to -90 to get the correct front vector at the start (0,0,-1) (instead of (1,0,0))
    def _update(self):
        self.front = normalized(self.get_look_direction())
        self.right = normalized(np.cross(self.front, self.w_up))
        self.up    = normalized(np.cross(self.right, self.front))

