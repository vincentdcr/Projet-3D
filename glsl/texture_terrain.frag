#version 330 core

uniform sampler2D lava_map;
uniform sampler2DArray terrain;
uniform sampler2DArray terrain_normal;
uniform sampler2D noise_map;
uniform sampler2D dudv_map;
uniform sampler2D lava_normal_map;
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

uniform float lava_speed;
uniform float displacement_speed;

const float OFFSET_STRENGTH = 0.8;
const vec3 BLEND_SHARPNESS = vec3(8.0,8.0,8.0);
const float TILE_SCALE = 1.0;
const float DISTORSION_STRENGTH = 0.55;

float computeFog(float d)
{
    const float density = 0.001;
    return clamp( exp(-density*density * d*d), 0.75, 1.0);
}

float shadow_calculation(vec4 frag_tex_light_space_coords, vec3 normal, vec3 lightDir)
{
    float bias = max(0.015 * (1.0 - dot(normal, lightDir)), 0.001);

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

float sum( vec3 v ) { return v.x+v.y+v.z; }

float noise_map_lookup(vec2 x, float factor) {
    return texture( noise_map, factor*x ).x;
}

// Pulled from https://www.shadertoy.com/view/Xtl3zf
// Add variety to terrain
vec3 textureNoTile(sampler2DArray map, vec2 x, float tex_index)
{
    float k = noise_map_lookup(x, 0.005); // cheap (cache friendly) lookup
    
    vec2 duvdx = dFdx( x );
    vec2 duvdy = dFdy( x );
    
    // rotate, if l big = very rotated
    float l = k*8.0;
    float f = fract(l);
    
    // smooth the transition between generated tiles
    float ia = floor(l+0.5); // suslik's method (see comments)
    float ib = floor(l);
    f = min(f, 1.0-f)*2.0;
    
    vec2 offa = sin(vec2(1.0,3.0)*ia); // can replace with any other hash
    vec2 offb = sin(vec2(1.0,3.0)*ib); // can replace with any other hash

    vec3 cola = textureGrad( map, vec3(x + OFFSET_STRENGTH*offa,tex_index), duvdx, duvdy ).xyz;
    vec3 colb = textureGrad( map, vec3(x + OFFSET_STRENGTH*offb,tex_index), duvdx, duvdy ).xyz;
    
    return mix( cola, colb, smoothstep(0.2,0.8,f-0.1*sum(cola-colb)) );
}

// returns a value between 0 and 1 for blending purposes (lower ABS bound between the two)
float compute_gradient(float lower_bound, float upper_bound, vec2 x, float factor, bool is_dissolve) {
    float base = min(lower_bound, upper_bound);
    float span = abs(upper_bound - lower_bound);
    float lookup_value = is_dissolve ?  noise_map_lookup( x, factor) : -noise_map_lookup(x, factor); 
    return clamp((w_position.y-base)/span - lookup_value, 0.0, 1.0) ;
}

vec3 lava_apparition(vec3 tex) {
    vec4 lava = texture(lava_map, w_position.xz/513+256.5); 

    if (lava.x == 0.0){
        return tex;
    } 
    else {
        float bilin_val = clamp((lava_speed*(-lava.x)+lava.x+lava_speed)-0.1*(1/lava_speed),0.0,1.0);


        //compute the dudv map distorsion value for the rippling effect
        vec2 dudv_distortion_coords = texture(dudv_map, vec2(frag_tex_coords.x, frag_tex_coords.y + 5.0* displacement_speed)).rg * 0.5 ;
        dudv_distortion_coords = frag_tex_coords + vec2(dudv_distortion_coords.x + 1.0*displacement_speed, dudv_distortion_coords.y + 5.0*displacement_speed);
        vec2 dudv_distortion = (texture(dudv_map, dudv_distortion_coords).rg * 2.0 - 1.0) * DISTORSION_STRENGTH;


        //normal calculation from normal map
        vec4 normal_map_color = texture(lava_normal_map, dudv_distortion_coords);
        // we extract the normal of the distorted fragment by taking the value pointing up and clamping the others to (-1;1)
        vec3 normal = vec3(normal_map_color.r *2.0 - 1.0 , normal_map_color.b * 2.5, normal_map_color.g * 2.0 - 1.0);
        normal = normalize(normal);

        vec3 color_offset = texture(noise_map, dudv_distortion_coords*0.08).rgb ;
   
        vec3 final_color = vec3(0.8,0.01,0.0)+ vec3(0.2,0.2,0.0)*color_offset.x;
        return mix(tex, final_color, bilin_val);
    }
}

void main() { //with GPU Gem 3 UDN blend implementation 
    // compute blendWeights according to the world normal of the fragment
    vec3 blend_weights = pow (abs(w_normal), BLEND_SHARPNESS);
    // compute the normalized sum (x+y+z=1) of our blend mask
    blend_weights /= dot(blend_weights, vec3(1.0,1.0,1.0));

    // UVs for axis based on world position of frag
    vec2 y_UV = w_position.xz / TILE_SCALE;
    vec2 x_UV = w_position.zy / TILE_SCALE;
    vec2 z_UV = w_position.xy / TILE_SCALE;
    // texture from the sampled UVs
    vec3 tangent_normal_x, tangent_normal_y, tangent_normal_z, color_x, color_y, color_z;

    vec3 tangent_normal_rock_x = textureNoTile (terrain_normal, x_UV, 0.0).rgb;
    vec3 tangent_normal_rock_z = textureNoTile(terrain_normal, z_UV, 0.0).rgb;
    vec3 color_rock_x = textureNoTile (terrain, x_UV,0.0).rgb;
    vec3 color_rock_z = textureNoTile(terrain, z_UV,0.0).rgb;
    vec3 tangent_normal_sand_x = textureNoTile(terrain_normal, x_UV,3.0).rgb;
    vec3 tangent_normal_sand_z = textureNoTile(terrain_normal, z_UV,3.0).rgb;
    vec3 color_sand_x = textureNoTile(terrain, x_UV,3.0).rgb;
    vec3 color_sand_z = textureNoTile(terrain, z_UV,3.0).rgb;
    vec3 tangent_normal_rock_snow_x = textureNoTile(terrain_normal, x_UV,4.0).rgb;
    vec3 tangent_normal_rock_snow_z = textureNoTile(terrain_normal, z_UV,4.0).rgb;
    vec3 color_rock_snow_x = textureNoTile(terrain, x_UV,4.0).rgb;
    vec3 color_rock_snow_z = textureNoTile(terrain, z_UV,4.0).rgb;
    if ( w_position.y <= -45) {
        color_x = color_sand_x;
        color_z = color_sand_z;
        tangent_normal_x = tangent_normal_sand_x;
        tangent_normal_z = tangent_normal_sand_z;
        tangent_normal_y = textureNoTile(terrain_normal, y_UV, 2.0).rgb;
        color_y = textureNoTile(terrain, y_UV, 2.0).rgb;    
    } if (w_position.y > -45 && w_position.y <= -35) {
        color_x = mix(color_sand_x, color_rock_x, compute_gradient(-40, -35, x_UV, 0.5, false));
        color_z = mix(color_sand_z, color_rock_z, compute_gradient(-40, -35, z_UV, 0.5, false));
        tangent_normal_x = mix(tangent_normal_sand_x, tangent_normal_rock_x, compute_gradient(-40, -35, x_UV, 0.5, false));
        tangent_normal_z = mix(tangent_normal_sand_z, tangent_normal_rock_z, compute_gradient(-40, -35, z_UV, 0.5, false));
    } if (w_position.y > -35 && w_position.y <= 20) {
        color_x = color_rock_x;
        color_z = color_rock_z;
        tangent_normal_x = tangent_normal_rock_x;
        tangent_normal_z = tangent_normal_rock_z;
    } if (w_position.y > 20) {
        color_x = mix(color_rock_x, color_rock_snow_x, compute_gradient(20, 64, x_UV, 0.1, true));
        color_z = mix(color_rock_z, color_rock_snow_z, compute_gradient(20, 64, z_UV, 0.1, true));
        tangent_normal_x = mix(tangent_normal_rock_x, tangent_normal_rock_snow_x, compute_gradient(20, 64, x_UV, 0.1, true));
        tangent_normal_z = mix(tangent_normal_rock_z, tangent_normal_rock_snow_z, compute_gradient(20, 64, z_UV, 0.1, true));
    }

    vec3 tangent_normal_sand_y = textureNoTile(terrain_normal, y_UV,3.0).rgb;
    vec3 color_sand_y = textureNoTile(terrain, y_UV,3.0).rgb;
    vec3 tangent_normal_meadow_y = textureNoTile(terrain_normal, y_UV,1.0).rgb;
    vec3 color_meadow_y = textureNoTile(terrain, y_UV,1.0).rgb;
    vec3 tangent_normal_rock_snow_y = textureNoTile(terrain_normal, y_UV,4.0).rgb;
    vec3 color_rock_snow_y = textureNoTile(terrain, y_UV,4.0).rgb;

    if (w_position.y > -45 && w_position.y <= -40) {
        tangent_normal_y = tangent_normal_sand_y;
        color_y = color_sand_y;
    } if (w_position.y > -40 && w_position.y <= -30) {
        color_y = mix(color_sand_y, color_meadow_y, compute_gradient(-35, -30, y_UV, 0.5, false));
        tangent_normal_y = mix(tangent_normal_sand_y, tangent_normal_meadow_y, compute_gradient(-35, -30, y_UV, 0.5, false));
    } if (w_position.y > -30 && w_position.y <= 15) {
        tangent_normal_y = tangent_normal_meadow_y;
        color_y = color_meadow_y;
    } if (w_position.y > 15 && w_position.y <= 25) {
        color_y = mix(color_meadow_y, color_rock_snow_y, compute_gradient(20, 25, y_UV, 0.5, false));
        tangent_normal_y = mix(tangent_normal_meadow_y, color_rock_snow_y, compute_gradient(20, 25, y_UV, 0.5, false));
    } if (w_position.y > 25) {
        tangent_normal_y = tangent_normal_rock_snow_y;
        color_y = color_rock_snow_y;
    }

    // swizzle tangent normal map to match world normals
    vec3 normalX = vec3(0.0, tangent_normal_x.yx);
    vec3 normalY = vec3(tangent_normal_y.x, 0.0, tangent_normal_y.y);
    vec3 normalZ = vec3(tangent_normal_z.xy, 0.0);

    // blend normals and add to world normal
    vec3 normal = normalize( normalX.xyz * blend_weights.x + normalY.xyz * blend_weights.y + 
                             normalZ.xyz * blend_weights.z + w_normal
                            );

    vec3 final_texture = color_x * blend_weights.x + color_y * blend_weights.y + color_z * blend_weights.z;
    final_texture = lava_apparition(final_texture);
   
    //Phong illumination using normal from normal map
    vec3 lightDir = normalize(light_dir - w_position);
    vec3 r = reflect(-lightDir, normal);
    vec3 view_vector = normalize(w_camera_position - w_position);
    float shadow = (1 - shadow_calculation(frag_tex_light_space_coords, w_normal, lightDir));
    vec3 diffuse = k_d*max(dot(normal, lightDir ),0) * shadow;
    vec3 specular = k_s*pow(max(dot(r, view_vector),0), s) * shadow;
    vec3 I = k_a + diffuse + specular;
    vec3 light_texture = I * final_texture;

    // add the fog to the final fragment color
    out_color = mix(vec4(fog_color,1), vec4(light_texture,1), computeFog(distance(w_camera_position, w_position)));
}


