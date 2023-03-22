#version 330 core
in vec3 position;
in vec2 aTexCoord;
in vec3 aColor;



uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;


out vec3 ourColor;
out vec2 TexCoord;

void main()
{
  	gl_Position = projection * view * model * vec4(position, 1.0);
    ourColor = aColor;
    TexCoord = aTexCoord;
}