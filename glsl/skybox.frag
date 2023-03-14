#version 330 core
out vec4 out_color;

in vec3 frag_tex_coords;

uniform samplerCube cube_map;
uniform vec3 fog_color;

// determine the limits for the skybox fading into the fog
const float lower_limit = 0.0;
const float upper_limit = 0.1;

void main()
{    
    vec4 color = texture(cube_map, frag_tex_coords);
    // float alpha = clamp((frag_tex_coords.y - lower_limit) / (upper_limit - lower_limit), 0.0, 1.0); decomment once it makes sense to use it
    float alpha = 1.0;
    out_color = mix (vec4(fog_color,1), color, alpha);
}