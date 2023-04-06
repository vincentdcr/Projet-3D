#version 330 core

// input attribute variable, given per vertex
in vec3 position;
in vec2 tex_coord;

// global matrix variables
uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

out vec4 clip_space;
out vec3 w_position;   // in world coordinates
out vec2 frag_tex_coords;


void main() {
    vec4 w_position4 = (model * vec4(position, 1));
    w_position = w_position4.xyz / w_position4.w;
    float tiling_count = 8; //allow the texture to tile itself over the whole quad
    frag_tex_coords = tex_coord * tiling_count;

    // tell OpenGL how to transform the vertex to clip coordinates
    clip_space = projection * view * model * vec4(position, 1);
    gl_Position = clip_space;
}
