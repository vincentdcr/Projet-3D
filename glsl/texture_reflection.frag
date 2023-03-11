#version 330 core

uniform samplerCube cube_map;
in vec2 frag_tex_coords;
out vec4 out_color;

// fragment position and normal of the fragment, in WORLD coordinates
// (you can also compute in VIEW coordinates, your choice! rename variables)
in vec3 w_position, w_normal;   // in world coodinates

// light dir, in world coordinates
uniform vec3 light_dir;

// material properties
uniform vec3 k_d;
uniform vec3 k_s;
uniform vec3 k_a; 
uniform float s;

// world camera position
uniform vec3 w_camera_position;

void main() {
    // compute reflection/refraction from the object
    // float ratio = 1.00 / 1.52; decomment and change reflect by refract on the next line to compute refraction
    vec3 I = normalize(w_position - w_camera_position);
    vec3 R = reflect(I, normalize(w_normal)); // add the ratio parameter for refraction
    out_color = vec4(texture(cube_map, R).rgb, 1.0);
}
