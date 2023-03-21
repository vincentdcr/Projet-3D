#version 330 core

// receiving interpolated color for fragment shader
in vec3 fragment_color;
uniform sampler2D diffuse_map;
in vec2 frag_tex_coords;

// output fragment color for OpenGL
out vec4 out_color;

void main() {
    vec3 texture = texture(diffuse_map, frag_tex_coords).rgb;
    out_color = vec4(texture, 1);
}
