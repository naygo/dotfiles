#version 330
// Complete the curved outline using the native i3 border color.
in vec2 texcoord;
uniform sampler2D tex;
uniform vec2 effective_size;
uniform float corner_radius;
vec4 default_post_processing(vec4 color);

bool is_i3_border(vec3 color) {
    const float tolerance = 3.0 / 255.0;
    return distance(color, vec3(215.0, 153.0, 33.0) / 255.0) < tolerance
        || distance(color, vec3(80.0, 73.0, 69.0) / 255.0) < tolerance
        || distance(color, vec3(60.0, 56.0, 54.0) / 255.0) < tolerance
        || distance(color, vec3(204.0, 36.0, 29.0) / 255.0) < tolerance;
}

vec4 window_shader() {
    vec2 texsize = vec2(textureSize(tex, 0));
    vec4 color = texture(tex, texcoord / texsize);
    if (corner_radius <= 0.0) {
        return default_post_processing(color);
    }
    vec2 size = effective_size;
    vec4 border = texture(tex, vec2(0.5, texsize.y * 0.5) / texsize);
    if (is_i3_border(border.rgb)) {
        float radius = min(corner_radius, min(size.x, size.y) * 0.5);
        vec2 q = abs(texcoord - size * 0.5) - size * 0.5 + radius;
        float edge_distance = length(max(q, vec2(0.0)))
                            + min(max(q.x, q.y), 0.0) - radius;
        // One-pixel outline with a soft inner edge. Picom clips its outer edge.
        float coverage = 1.0 - smoothstep(0.75, 1.75, -edge_distance);
        color = mix(color, border, coverage);
    }
    return default_post_processing(color);
}
