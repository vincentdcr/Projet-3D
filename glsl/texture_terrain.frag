#version 330 core

uniform sampler2D diffuse_map;
uniform sampler2D normal_map;
uniform sampler2D diffuse_map2;
uniform sampler2D normal_map2;
uniform sampler2D noise_map;
in vec2 frag_tex_coords;
out vec4 out_color;

// material properties
uniform vec3 k_a;
uniform vec3 k_d;
uniform vec3 k_s;
uniform float s;

in vec3 w_position, w_normal;

uniform vec3 w_camera_position, light_dir;

//Fog specified color
uniform vec3 fog_color;

const float OFFSET_STRENGTH = 0.5;
const vec3 BLEND_SHARPNESS = vec3(16.0,16.0,16.0);
const float TILE_SCALE = 4.0;


float computeFog(float d)
{
    const float density = 0.0015;
    return clamp( exp(-density*density * d*d), 0.5, 1.0);
}

float sum( vec3 v ) { return v.x+v.y+v.z; }

// Pulled from https://www.shadertoy.com/view/Xtl3zf
// Add variety to terrain
vec3 textureNoTile(sampler2D map, vec2 x)
{
    float k = texture( noise_map, 0.005*x ).x; // cheap (cache friendly) lookup
    
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

    vec3 cola = textureGrad( map, x + OFFSET_STRENGTH*offa, duvdx, duvdy ).xyz;
    vec3 colb = textureGrad( map, x + OFFSET_STRENGTH*offb, duvdx, duvdy ).xyz;
    
    return mix( cola, colb, smoothstep(0.2,0.8,f-0.1*sum(cola-colb)) );
}



void main() {
    // compute blendWeights according to the world normal of the fragment
    vec3 blend_weights = pow (abs(w_normal), BLEND_SHARPNESS);
    // compute the normalize sum (x+y+z=1) of our blend mask
    blend_weights /= dot(blend_weights, vec3(1.0,1.0,1.0));

    // UVs for axis based on world position of frag
    vec2 y_UV = w_position.xz / TILE_SCALE;
    vec2 x_UV = w_position.zy / TILE_SCALE;
    vec2 z_UV = w_position.xy / TILE_SCALE;
    // texture from the sampled UVs
    vec3 tangent_normal_y = textureNoTile(normal_map2, y_UV).rgb;
    vec3 tangent_normal_x = textureNoTile (normal_map, x_UV).rgb;
    vec3 tangent_normal_z = textureNoTile(normal_map, z_UV).rgb;

    // swizzle tangent normal map to match world normals
    vec3 normalX = vec3(0.0, tangent_normal_x.yx);
    vec3 normalY = vec3(tangent_normal_y.x, 0.0, tangent_normal_y.y);
    vec3 normalZ = vec3(tangent_normal_z.xy, 0.0);

        // blend normals and add to world normal
    vec3 normal = normalize( normalX.xyz * blend_weights.x + normalY.xyz * blend_weights.y + 
                             normalZ.xyz * blend_weights.z + w_normal
                            );
    vec3 color_y = textureNoTile(diffuse_map2, y_UV).rgb + vec3(0.0,0.02,0.0);
    vec3 color_x = textureNoTile (diffuse_map, x_UV).rgb;
    vec3 color_z = textureNoTile(diffuse_map, z_UV).rgb;

    vec3 texture = color_x * blend_weights.x + color_y * blend_weights.y + color_z * blend_weights.z;
   
    //Phong illumination using normal from normal map
    vec3 lightDir = normalize(light_dir - w_position);
    vec3 r = reflect(-lightDir, normal);
    vec3 view_vector = normalize(w_camera_position - w_position);
    vec3 I = k_a + k_d*max(dot(normal, lightDir ),0)+k_s*pow(max(dot(r, view_vector),0), s);
    vec3 light_texture = I * texture;
    out_color = mix(vec4(fog_color,1), vec4(light_texture,1), computeFog(distance(w_camera_position, w_position)));
}

