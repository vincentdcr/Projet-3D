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
uniform vec3 k_d;
uniform vec3 k_s;
uniform vec3 k_a;
uniform float s;

// world camera position
uniform vec3 w_camera_position;

void main() {
        // compute Lambert illumination
    vec3 r = reflect(-light_dir, w_normal);
    vec3 view_vector =normalize(w_camera_position - w_position);
    vec3 I = k_a + max(k_d*dot(normalize(w_normal), light_dir ),0)+k_s*pow(max(dot(view_vector, r),0), s);
    vec3 texture = texture(diffuse_map, frag_tex_coords).rgb;
    vec3 light_texture = I * texture;
    out_color = vec4(texture,1); // put back light_texture once normals are computed
}
