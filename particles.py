#!/usr/bin/env python3
import OpenGL.GL as GL              # standard Python OpenGL wrapper
import numpy as np                  # all matrix manipulations & OpenGL args
import core
from texture import Texture, Textured
from transform import normalized
from PIL import Image
from waterFrameBuffer import WaterFrameBuffers
import random

# -------------- Particles ---------------------------------
class Particle():
    def __init__(self, scale, color, life, pos, speed):

        base_coords = np.array([[-1, -1, 0], [1, -1, 0], [1, 1, 0], [-1, 1, 0]])
        self.coords = scale * base_coords + pos
        self.color = color
        self.life = life
        self.pos = pos
        self.speed = speed.copy()
    
    def update(self, delta, camera_position):
        if(self.life > 0.0):
            self.life -= delta
            if (self.life > 0.0):
                self.speed += np.array([0.0,-9.81, 0.0]) * delta * 0.5
                self.coords += self.speed * delta
                self.cameradistance = ( self.pos - camera_position )
                self.color[3] -= delta * 2.5
                return self
            else:
                self.camera_distance = -1.0

class ParticlesEmitter(Textured):
    def __init__(self, shader, scale=0.25, color=(0.7,0.2,0.0,1.0), life=2.0, pos=np.array([0.0,23.0,0.0]), speed=np.array([0.0,10.0,0.0]), max_count=1000):
        self.max_particles_count = max_count
        self.shader = shader
        self.scale = scale
        self.color = color
        self.life = life
        self.pos = pos
        self.speed = speed
        self.last_used_particle = 0
        self.is_active = False # allows us to stop the emitter
        random.seed() 

        self.particles_instances = []

    def update(self, delta, cam_pos, create_new_particles):
        if (create_new_particles): # if the emitter was asked to create new particles
            self.is_active = True
            nb_new_particles = 100
            for i in range(nb_new_particles):
                if(len(self.particles_instances) < self.max_particles_count):
                    self.particles_instances.append(self.generate_particle())
                    continue
                particle_index = self.find_dead_particle()
                self.particles_instances[particle_index] = self.generate_particle()

        living_particles = []
        for particle in self.particles_instances:
            particle = particle.update(delta, cam_pos)
            if (particle != None):
                living_particles.append(particle)
        if (len(living_particles)!=0):   #if there is at least one particle to draw 
            particles_coords = []
            particles_color = []
            particles_index = []
            particle_index = np.array((1, 0, 3, 1 , 3 , 2), np.uint32)
            for i in range(len(living_particles)):
                particle_coords = living_particles[i].coords.tolist()
                particles_coords.extend(particle_coords)
                particles_color.extend(np.array([living_particles[i].color] * len(particle_coords)).tolist()) # 1 color per vertex
                particles_index.extend(particle_index + i*4) #*4 because it's the nb of vertices of the particles
            mesh = core.Mesh(self.shader, attributes=dict(position=particles_coords, color=particles_color), index=particles_index, k_a=(0.1,0.1,0.1), k_d=(0.4,0.4,0.4), k_s=(1.0,0.9,0.8), s=16)    
            super().__init__(mesh)
        else:
            self.is_active = False


    def find_dead_particle(self):
        for i in range (self.last_used_particle, self.max_particles_count):
            if (self.particles_instances[i].life < 0):
                self.last_used_particle = i
                return i

        for i in range (0, self.last_used_particle):
            if (self.particles_instances[i].life < 0):
                self.last_used_particle = i
                return i

        return 0 # overrides particle 
    
    def generate_particle(self):
        part_pos = np.array([random.uniform(-65.0,20.0),random.randint(0,5),random.uniform(-60.0,20.0)])
        part_color = np.array(self.color) 
        return Particle(self.scale, part_color, self.life+random.uniform(-2,2), self.pos + part_pos, self.speed)
    
    def get_activity(self):
        return self.is_active

