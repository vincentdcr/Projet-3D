#version 330 core
out vec4 out_color;

uniform sampler2D reflection_tex;
uniform sampler2D refraction_tex;
uniform sampler2D dudv_map;
uniform sampler2D normal_map;
uniform sampler2D noise_map;
uniform sampler2DShadow shadow_map;

in vec4 clip_space;
in vec3 w_position;   // in world coodinates
in vec2 frag_tex_coords;
in vec4 frag_tex_light_space_coords; 
in float out_of_shadow_area_factor;

// light dir, in world coordinates
uniform vec3 light_dir;

// material properties
uniform vec3 k_a;
uniform vec3 k_d;
uniform vec3 k_s;
uniform float s;

uniform float displacement_speed;

// world camera position
uniform vec3 w_camera_position;

//Fog specified color
uniform vec3 fog_color;

//Near and far plane for floor depth calc
uniform float near;
uniform float far;

const float DISTORSION_STRENGTH = 0.55;

float computeFog(float d)
{
    const float density = 0.0055;
    return clamp( exp(-density*density * d*d), 0.7, 1.0);
}

// returns a linear depth value which rises to 1 and then has a treshold for a certain depth distance
float computeDepth(float depth, float treshold) 
{
    return clamp(depth / treshold , 0.0, 1.0);
}



float shadow_calculation(vec4 frag_tex_light_space_coords, vec3 normal, vec3 lightDir)
{
    float bias = max(0.02 * (1.0 - dot(normal, lightDir)), 0.001);

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

void main()
{
   
  
    //compute the dudv map distorsion value for the rippling effect
    vec2 dudv_distortion_coords = texture(dudv_map, vec2(frag_tex_coords.x, frag_tex_coords.y - 0.5* displacement_speed)).rg * 0.5 ;
    dudv_distortion_coords = frag_tex_coords + vec2(dudv_distortion_coords.x + displacement_speed, dudv_distortion_coords.y + displacement_speed);
    vec2 dudv_distortion = (texture(dudv_map, dudv_distortion_coords).rg * 2.0 - 1.0) * DISTORSION_STRENGTH;


    //normal calculation from normal map
    vec4 normal_map_color = texture(normal_map, dudv_distortion_coords);
    // we extract the normal of the distorted fragment by taking the value pointing up and clamping the others to (-1;1)
    vec3 normal = vec3(normal_map_color.r *2.0 - 1.0 , normal_map_color.b * 2.5, normal_map_color.g * 2.0 - 1.0);
    normal = normalize(normal);

    //Phong illumination using normal from normal map
    vec3 lightDir = normalize(light_dir - w_position);
    vec3 r = reflect(-lightDir, normal);
    vec3 view_vector =normalize(w_camera_position - w_position);
    float shadow = (1 - shadow_calculation(frag_tex_light_space_coords, normal, lightDir));
    vec3 diffuse = k_d*max(dot(normal, lightDir ),0) * shadow;
    vec3 specular = k_s*pow(max(dot(r, view_vector),0), s) * shadow;
    vec3 I = k_a + diffuse + specular;

    //+ c'est petit + maillage fin, + c'est grand + maillage grossier (entre 0 et 1(environ))
    vec3 color_offset = texture(noise_map, dudv_distortion_coords*0.08).rgb ;
   
    vec4 final_color = vec4(0.8,0.01,0.0,1.0)+ vec4((vec3(0.2,0.2,0.0)*color_offset.x),1.0); //red, a expérimenter (clamper final_color entre 0 et 1), le 0.1 ds vec4 c'est la quantité de couleur de base sur la noise map
    vec4 lighted_color = vec4(I,1.0) * final_color; 
    out_color = mix(vec4(fog_color,1), lighted_color, computeFog(distance(w_camera_position, w_position)));

}