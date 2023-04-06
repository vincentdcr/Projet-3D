#version 330 core

// input attribute variable, given per vertex
in vec3 position;

in vec2 tex_coord;

out vec2 frag_tex_coords;

void main() {
    frag_tex_coords = tex_coord;

    // tell OpenGL how to transform the vertex to screen coordinates
    gl_Position = vec4(0.75+position.x/5.33, 0.66+position.y/3, 0.0, 1); 
}
