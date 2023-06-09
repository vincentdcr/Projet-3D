#version 330 core
out vec4 out_color;

uniform sampler2D reflection_tex;
uniform sampler2D refraction_tex;
uniform sampler2D depth_map;
uniform sampler2D dudv_map;
uniform sampler2D normal_map;
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

const float DISTORSION_STRENGTH = 0.02;

float computeFog(float d)
{
    const float density = 0.0015;
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
    //change coordinate system (projection mapping of the refle/refra texture)
    vec2 screen_space_coords = (clip_space.xy / clip_space.w) / 2.0 + 0.5;

    // compute the coords of the fragment before displacement (+ we flip the reflection texture)
    vec2 reflection_coords = vec2(screen_space_coords.x, -screen_space_coords.y);
    vec2 refraction_coords = vec2(screen_space_coords.x, screen_space_coords.y);

    //compute the depth from the water surface
    float depth = texture(depth_map, refraction_coords).x; 
    float floor_dist = 2.0 * near * far / (far + near - (2.0 * depth - 1.0) * (far - near));
    depth = gl_FragCoord.z;
    float water_dist =  2.0 * near * far / (far + near - (2.0 * depth - 1.0) * (far - near));
    float water_depth = floor_dist - water_dist;

    //compute the dudv map distorsion value for the rippling effect
    vec2 dudv_distortion_coords = texture(dudv_map, vec2(frag_tex_coords.x, frag_tex_coords.y - 0.5* displacement_speed)).rg * 0.2 ;
    dudv_distortion_coords = frag_tex_coords + vec2(dudv_distortion_coords.x + displacement_speed, dudv_distortion_coords.y + displacement_speed);
    vec2 dudv_distortion = (texture(dudv_map, dudv_distortion_coords).rg * 2.0 - 1.0) * DISTORSION_STRENGTH * computeDepth(water_depth,20) ;

    // compute the final coords of the fragment after the displacement 
    // we clamp to prevent sampling from the other side of the texture
    reflection_coords += dudv_distortion;
    reflection_coords = vec2(clamp(reflection_coords.x, 0.001, 0.999), clamp(reflection_coords.y, -0.999, -0.001));
    refraction_coords += dudv_distortion;
    refraction_coords = clamp(refraction_coords, 0.001, 0.999);

    vec4 reflection_color = texture(reflection_tex, reflection_coords);
    vec4 refraction_color = texture(refraction_tex, refraction_coords);

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

    //finalize the lighting, reflection/refraction and compute the final color of the frag 
    float refractivity_factor = dot(view_vector, normal); //fresnel effect

    vec4 final_reflection = mix(reflection_color, refraction_color, refractivity_factor);
    vec4 final_color = mix(final_reflection, vec4(0.0,0.4,0.7,1.0), 0.1); //we add a bit of blue to the final texture
    vec4 lighted_color = vec4(I,1.0) * final_color; 
    lighted_color.a = computeDepth(water_depth,1); // compute the transparency according to depth information
    out_color = mix(vec4(fog_color,1), lighted_color, computeFog(water_dist));

}