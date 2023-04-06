import numpy as np 
from transform import ortho, lookat, vec
from math import radians

class ShadowMapManager():
    def __init__(self, offset=10.0, mov_tresh=1.0, angle_tresh=15.0, shadow_distance=192.0):
        self.ortho = ortho(-1,1,-1,1,0.1,50)
        self.l = 0 
        self.r = 0 
        self.b = 0 
        self.t = 0
        self.n = 0 
        self.f = 0
        self.OFFSET = offset
        self.i = 0
        self.cam_pos_prev = None
        self.cam_yaw_prev = None
        self.cam_pitch_prev = None
        self.treshold_movement = mov_tresh
        self.treshold_angle = angle_tresh
        self.far_dist = shadow_distance

    def compute_view_matrix_for_shadow_mapping(self, light_pos, center):
        return lookat(vec(light_pos), vec(center), vec(0,1,0))

    def compute_matrices_for_shadow_mapping(self, light_pos, cam, cam_pos, win):
        
        # Add this if the sun is not a moving object, the shadows will be more stable
        # if self.cam_pos_prev is not None and np.linalg.norm(cam_pos - self.cam_pos_prev) < self.treshold_movement and np.linalg.norm((cam.yaw + cam.pitch) - (self.cam_yaw_prev + self.cam_pitch_prev)) < radians(self.treshold_angle):
        #    # camera has not moved much, return cached matrices
        #    return self.view, self.ortho

        # update cached camera position
        self.cam_pos_prev = cam_pos
        self.cam_yaw_prev = cam.yaw
        self.cam_pitch_prev = cam.pitch

        ar = win[0] / win[1]
        near_dist = 0.1
        h_near = 2 * np.tan(radians(cam.fov) / 2) * near_dist
        w_near = h_near * ar
        h_far = 2 * np.tan(radians(cam.fov) / 2) * self.far_dist
        w_far = h_far * ar 
        center_far = cam_pos[:3] + cam.front * self.far_dist

        top_left_far = center_far + (cam.up * h_far / 2) - (cam.right * w_far / 2)
        top_right_far = center_far + (cam.up * h_far / 2) + (cam.right * w_far / 2)
        bottom_left_far = center_far - (cam.up  * h_far / 2) - (cam.right * w_far / 2)
        bottom_right_far = center_far - (cam.up * h_far / 2) + (cam.right * w_far / 2)

        center_near = cam_pos[:3] + cam.front * near_dist

        top_left_near = center_near + (cam.up * h_near / 2) - (cam.right * w_near / 2)
        top_right_near = center_near + (cam.up * h_near / 2) + (cam.right * w_near / 2)
        bottom_left_near = center_near - (cam.up * h_near / 2) - (cam.right * w_near / 2)
        bottom_right_near = center_near - (cam.up * h_near / 2) + (cam.right * w_near / 2)

        frustum_center = (center_far - center_near) * 0.5
        frustum_center4 = (frustum_center[0], frustum_center[1], frustum_center[2], 1.0) 
        # Add this if you want the center to be the middle of the camera frustum instead of the origin of the scene
        #light_view = self.compute_view_matrix_for_shadow_mapping(light_pos, np.dot(np.linalg.inv(cam.view_matrix()),(frustum_center4)))
        light_view = self.compute_view_matrix_for_shadow_mapping(light_pos, (0,0,0))

        frustum_to_light_view = [
            light_view @ np.hstack((bottom_right_near, 1.0)),
            light_view @ np.hstack((top_right_near, 1.0)),
            light_view @ np.hstack((bottom_left_near, 1.0)),
            light_view @ np.hstack((top_left_near, 1.0)),
            light_view @ np.hstack((bottom_right_far, 1.0)),
            light_view @ np.hstack((top_right_far, 1.0)),
            light_view @ np.hstack((bottom_left_far, 1.0)),
            light_view @ np.hstack((top_left_far, 1.0))
        ]

        # find max and min points to define an ortho matrix around
        min_point = np.array([np.inf, np.inf, np.inf])
        max_point = np.array([-np.inf, -np.inf, -np.inf])

        for point in frustum_to_light_view:
            for i in range(3):
                min_point[i] = min(min_point[i], point[i])
                max_point[i] = max(max_point[i], point[i])

        l = min_point[0] - self.OFFSET
        r = max_point[0] + self.OFFSET
        b = min_point[1] - self.OFFSET
        t = max_point[1] + self.OFFSET
        n = -max_point[2] - self.OFFSET
        f = -min_point[2] + self.OFFSET


        self.ortho = ortho(l, r, b, t, n, f)
        self.view = light_view
        return light_view, self.ortho
    
    def getShadowDistance(self):
        return self.far_dist + self.OFFSET
