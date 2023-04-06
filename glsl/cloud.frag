#version 330 core
out vec4 out_color;

uniform sampler2D cloud_map;

uniform float displacement_speed;
in vec2 frag_tex_coords;


void main()
{
    vec4 color = texture(cloud_map, frag_tex_coords/4 + displacement_speed/16);
    out_color = vec4(color.x);
}