#version 330 core
in vec3 position;
in vec4 color;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

out vec4 fragment_color;

void main()
{
    fragment_color = color;
    mat4 modelview = model * view;
    gl_Position = projection * modelview * vec4(position, 1.0);
}