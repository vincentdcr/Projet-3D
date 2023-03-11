#version 330 core
out vec4 out_color;

in vec3 frag_tex_coords;

uniform samplerCube cube_map;

void main()
{    
    out_color = texture(cube_map, frag_tex_coords);
}