#version 330 core

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
uniform vec4 clipping_plane;
uniform vec3 light_dir;
uniform vec3 w_camera_position;

in vec3 position;
in vec2 tex_coord;
in vec3 normal;
in vec3 tangent;

out vec2 frag_tex_coords;
out vec3 tangent_light_pos;
out vec3 tangent_view_pos;
out vec3 tangent_frag_pos;

out vec3 w_position;

void main() {
    // Transform the position into world coordinates
    vec4 w_position4 = model * vec4(position, 1.0);
    w_position = w_position4.xyz / w_position4.w;

    // Transform the normal and tangent vectors into world coordinates
    mat3 normal_matrix = transpose(inverse(mat3(model)));
    vec3 w_normal = normalize(normal_matrix * normal);
    vec3 w_tangent = normalize(normal_matrix * tangent);
    w_tangent = normalize(w_tangent - dot(w_tangent, w_normal) * w_normal);  // Gramm-Schmidt process to orthonormalize the tangent vec with the normal vec

    // Orthonormalize the tangent vector with the normal vector
    vec3 w_bitangent = cross(w_tangent, w_normal);  //depending on the uv mapping, may need to be inverted

    // Transform the light and camera positions into tangent space
    mat3 TBN = transpose(mat3(w_tangent, w_bitangent, w_normal));    // transpose of ortho matrix = inverse matrix
    tangent_light_pos = TBN * light_dir;
    tangent_view_pos = TBN * w_camera_position;
    tangent_frag_pos = TBN * w_position;

    // Calculate the final position of the vertex
    gl_Position = projection * view * w_position4;

    // Set the clipping plane
    gl_ClipDistance[0] = dot(w_position4, clipping_plane);  // tell GLSL to cull every vertices above/below clipping plane
    gl_Position = projection * view * w_position4;
    frag_tex_coords = tex_coord;

}