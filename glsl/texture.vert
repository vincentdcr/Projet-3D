#version 330 core

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
uniform vec4 clipping_plane;
in vec3 position;
in vec2 tex_coord;

out vec2 frag_tex_coords;

in vec3 normal;

// position and normal for the fragment shader, in WORLD coordinates
// (you can also compute in VIEW coordinates, your choice! rename variables)
out vec3 w_position, w_normal;   // in world coordinates

void main() {
    // TODO: compute the vertex position and normal in world or view coordinates
    w_normal = normalize(transpose(inverse(mat3(model))) * normal);
    vec4 w_position4 = (model * vec4(position, 1));
    gl_ClipDistance[0] = dot(w_position4, clipping_plane); // tell GLSL to cull every vertices above/below clipping plane
    w_position = w_position4.xyz / w_position4.w;
    gl_Position = projection * view * w_position4;
    frag_tex_coords = tex_coord;
}
