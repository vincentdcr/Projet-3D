#version 330 core

uniform sampler2D diffuse_map;
uniform sampler2D normal_map;
in vec2 frag_tex_coords;
out vec4 out_color;

// material properties
uniform vec3 k_a;
uniform vec3 k_d;
uniform vec3 k_s;
uniform float s;

in vec3 tangent_light_pos, tangent_view_pos, tangent_frag_pos;
in vec3 w_position;

uniform vec3 w_camera_position;

//Fog specified color
uniform vec3 fog_color;

float computeFog(float d)
{
    const float density = 0.0015;
    return clamp( exp(-density*density * d*d), 0.5, 1.0);
}

void main() {
    vec3 normal = texture(normal_map, frag_tex_coords).rgb;
    // transform normal vector to range [-1,1]
    normal = normalize(normal * 2.0 - 1.0);  // this normal is in tangent space
   
    // compute Lambert illumination (all in tangent space)
    vec3 lightDir = normalize(tangent_light_pos - tangent_frag_pos);
    vec3 r = reflect(-lightDir, normal);
    vec3 view_vector =normalize(tangent_view_pos - tangent_frag_pos);
    vec3 I = k_a + k_d*max(dot(normal, lightDir ),0)+k_s*pow(max(dot(r, view_vector),0), s);
    vec3 texture = texture(diffuse_map, frag_tex_coords).rgb;
    vec3 light_texture = I * texture;
    out_color = mix(vec4(fog_color,1), vec4(light_texture,1), computeFog(distance(w_camera_position, w_position)));
}

