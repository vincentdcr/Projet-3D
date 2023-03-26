#version 330 core

// input attribute variable, given per vertex
in vec3 position;
in vec2 tex_coord;

// global matrix variables
uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
uniform mat4 light_space_matrix;
uniform float shadow_distance;

out vec4 clip_space;
out vec3 w_position;   // in world coordinates
out vec2 frag_tex_coords;
out vec4 frag_tex_light_space_coords; 
out float out_of_shadow_area_factor;

const float shadow_trans_dist = 10.0;



void main() {
    vec4 w_position4 = (model * vec4(position, 1));
    w_position = w_position4.xyz / w_position4.w;
    float tiling_count = 8; //allow the texture to tile itself over the whole quad
    frag_tex_coords = tex_coord * tiling_count;

    // tell OpenGL how to transform the vertex to clip coordinates
    clip_space = projection * view * model * vec4(position, 1);
    gl_Position = clip_space;


    //compute vertex pos in light space
    frag_tex_light_space_coords = light_space_matrix * w_position4;
    
    // compute a transition period between shadowed / out of shadow area
    // out_of_shadow_area_factor = 0.0 if outside area, 1.0 if before shadow_distance 
    // and a value between 0 and 1 in the transition
    vec4 position_from_camera = view * w_position4;
    float distance = length(position_from_camera) - (shadow_distance - shadow_trans_dist);
    distance = distance / shadow_trans_dist;
    out_of_shadow_area_factor = clamp (1.0-distance, 0.0, 1.0);

}
