#version 330 core

uniform sampler2D diffuse_map;
in vec2 frag_tex_coords;
out vec4 out_color;

// fragment position and normal of the fragment, in WORLD coordinates
// (you can also compute in VIEW coordinates, your choice! rename variables)
in vec3 w_position, w_normal;   // in world coodinates

// light dir, in world coordinates
uniform vec3 light_dir;

// material properties
uniform vec3 k_a;
uniform vec3 k_d;
uniform vec3 k_s;
uniform float s;

// world camera position
uniform vec3 w_camera_position;

void main() {
        // compute Lambert illumination
    vec3 r = reflect(-light_dir, w_normal);
    vec3 view_vector =normalize(w_camera_position - w_position);
    vec3 I = vec3(0.7000,0.7000,0.7000) + max(vec3(1.000,1.000,1.000)*dot(normalize(w_normal), light_dir ),0)+vec3(0.3000,0.3000,0.3000)*pow(max(dot(view_vector, r),0), 0.2);
    vec3 texture = texture(diffuse_map, frag_tex_coords).rgb;
    vec3 light_texture = I * texture;
    out_color = vec4(light_texture,1); // put back light_texture once normals are computed
}

