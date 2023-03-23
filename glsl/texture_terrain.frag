#version 330 core

uniform sampler2D diffuse_map;
uniform sampler2D normal_map;
uniform sampler2D noise_map;
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

float sum( vec3 v ) { return v.x+v.y+v.z; }

// Pulled from https://www.shadertoy.com/view/Xtl3zf
// Add variety to terrain
vec3 textureNoTile(sampler2D map, vec2 x, float v )
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

    vec3 cola = textureGrad( map, x + v*offa, duvdx, duvdy ).xyz;
    vec3 colb = textureGrad( map, x + v*offb, duvdx, duvdy ).xyz;
    
    return mix( cola, colb, smoothstep(0.2,0.8,f-0.1*sum(cola-colb)) );
}


void main() {
    vec3 normal = textureNoTile(normal_map, frag_tex_coords, 0.6);
    // transform normal vector to range [-1,1]
    normal = normalize(normal * 2.0 - 1.0);  // this normal is in tangent space
   
    // compute Lambert illumination (all in tangent space)
    vec3 lightDir = normalize(tangent_light_pos - tangent_frag_pos);
    vec3 r = reflect(-lightDir, normal);
    vec3 view_vector =normalize(tangent_view_pos - tangent_frag_pos);
    vec3 I = k_a + k_d*max(dot(normal, lightDir ),0)+k_s*pow(max(dot(r, view_vector),0), s);
    vec3 texture = textureNoTile(diffuse_map, frag_tex_coords, 0.6);
    vec3 light_texture = I * texture;
    out_color = mix(vec4(fog_color,1), vec4(light_texture,1), computeFog(distance(w_camera_position, w_position)));
}

