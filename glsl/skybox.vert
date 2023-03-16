#version 330 core

out vec3 frag_tex_coords;
in vec3 position;

uniform mat4 projection;
uniform mat4 view;

void main()
{
    frag_tex_coords = position;
    vec4 pos = projection * mat4(mat3(view)) * vec4(position, 1.0); // disabled the translation component of the view matrix
    gl_Position = pos.xyww;
}  



