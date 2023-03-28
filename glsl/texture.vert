#version 330 core

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
uniform vec4 clipping_plane;
uniform mat4 light_space_matrix;

uniform float shadow_distance;

in vec3 position;
in vec2 tex_coord;
in vec3 normal;

out vec2 frag_tex_coords;
out vec4 frag_tex_light_space_coords; 

out vec3 w_position, w_normal;
out float out_of_shadow_area_factor;

const float shadow_trans_dist = 10.0 ;

void main() {
    // Transform the position into world coordinates
    vec4 w_position4 = model * vec4(position, 1.0);
    w_position = w_position4.xyz / w_position4.w;
    w_normal = normalize( transpose(inverse(mat3(model))) * normal);

    // Set the clipping plane
    gl_ClipDistance[0] = dot(w_position4, clipping_plane);  // tell GLSL to cull every vertices above/below clipping plane
    vec4 position_from_camera = view * w_position4;
    gl_Position = projection * position_from_camera;
    frag_tex_coords = tex_coord ;

    //compute vertex pos in light space
    frag_tex_light_space_coords = light_space_matrix * w_position4;

    // compute a transition period between shadowed / out of shadow area
    // out_of_shadow_area_factor = 0.0 if outside area, 1.0 if before shadow_distance 
    // and a value between 0 and 1 in the transition
    float distance = length(position_from_camera) - (shadow_distance - shadow_trans_dist);
    distance = distance / shadow_trans_dist;
    out_of_shadow_area_factor = clamp (1.0-distance, 0.0, 1.0);

}