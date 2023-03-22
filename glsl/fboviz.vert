#version 330 core

// global color
uniform vec3 global_color;

// input attribute variable, given per vertex
in vec3 position;
in vec3 color;
in vec3 normal;

// global matrix variables
uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

in vec2 tex_coord;

out vec2 frag_tex_coords;


// interpolated color for fragment shader, intialized at vertices
out vec3 fragment_color;

void main() {
    // initialize interpolated colors at vertices
    frag_tex_coords = tex_coord;

    // tell OpenGL how to transform the vertex to clip coordinates
    gl_Position = vec4(0.66+position.x/3, 0.66+position.y/3, 0.0, 1); 
}
