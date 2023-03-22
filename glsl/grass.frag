#version 330 core
out vec4 Frag_color;

uniform sampler2D ourTexture;
in vec2 TexCoord;

void main()
{
    Frag_color = texture(ourTexture, TexCoord); 
}