#version 330 core

// input attribute variable, given per vertex
in vec3 position;

in vec2 tex_coord;

out vec2 frag_tex_coords;

void main() {
    // initialize interpolated colors at vertices
    frag_tex_coords = tex_coord;

    // tell OpenGL how to transform the vertex to screen coordinates
    gl_Position = vec4(0.66+position.x/3, 0.66+position.y/3, 0.0, 1); 
}
