#version 330 core

uniform sampler2D diffuse_map;
uniform sampler2D normal_map;
uniform sampler2D diffuse_map2;
uniform sampler2D normal_map2;
uniform sampler2D noise_map;
uniform sampler2DShadow shadow_map;
in vec2 frag_tex_coords;
in vec4 frag_tex_light_space_coords; 
out vec4 out_color;

// material properties
uniform vec3 k_a;
uniform vec3 k_d;
uniform vec3 k_s;
uniform float s;

in vec3 w_position, w_normal;
in float out_of_shadow_area_factor;


uniform vec3 w_camera_position, light_dir;

//Fog specified color
uniform vec3 fog_color;

const vec3 BLEND_SHARPNESS = vec3(16.0,16.0,16.0);
const float TILE_SCALE = 2.0;


float computeFog(float d)
{
    const float density = 0.001;
    return clamp( exp(-density*density * d*d), 0.75, 1.0);
}

float shadow_calculation(vec4 frag_tex_light_space_coords, vec3 normal, vec3 lightDir)
{
    float bias = max(0.002 * (1.0 - dot(normal, lightDir)), 0.001);

    // perspective divide 
    vec3 proj_coords = frag_tex_light_space_coords.xyz / frag_tex_light_space_coords.w;
    // transform from [-1,1] to [0,1] range
    proj_coords = proj_coords * 0.5 + 0.5;
    // get depth of current fragment from light's perspective
    float frag_depth = proj_coords.z - bias;
    // check whether current frag pos is in shadow by comparing the closest depth with the fragment depth 
    // (returns 1.0 if frag_depth is higher than the depth contained in the shadow map = in shadow)
    // we're getting a free PCF 2x2 thanks to the linear filtering of the shadow map
    float shadow = texture(shadow_map, vec3(proj_coords.xy,frag_depth)); 
  
    return shadow * out_of_shadow_area_factor;
} 


void main() {
    vec3 texture = texture(diffuse_map, frag_tex_coords).rgb;
   
    //Phong illumination using normal from normal map
    vec3 lightDir = normalize(light_dir - w_position);
    vec3 r = reflect(-lightDir, normalize(w_normal));
    vec3 view_vector = normalize(w_camera_position - w_position);
    float shadow = (1 - shadow_calculation(frag_tex_light_space_coords, w_normal, lightDir));
    vec3 diffuse = k_d*max(dot(normalize(w_normal), lightDir ),0) * shadow;
    vec3 specular = k_s*pow(max(dot(r, view_vector),0), s) * shadow;
    vec3 I = k_a + diffuse + specular;
    vec3 light_texture = I * texture;

    // add the fog to the final fragment color
    out_color = mix(vec4(fog_color,1), vec4(light_texture,1), computeFog(distance(w_camera_position, w_position)));
}