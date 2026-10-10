#version 330
// Grouped clients meet the strip with square upper corners.
in vec2 texcoord;
uniform sampler2D tex;
uniform vec2 effective_size;
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
    float radius = min(16.0, min(effective_size.x, effective_size.y) * 0.5);
    float x = min(texcoord.x, effective_size.x - texcoord.x);
    float y = effective_size.y - texcoord.y;
    if (x < radius && y < radius) {
        float edge = radius - length(vec2(x, y) - vec2(radius));
        vec4 border = texture(tex, vec2(0.5, texsize.y * 0.5) / texsize);
        if (is_i3_border(border.rgb)) {
            color = mix(color, border, 1.0 - smoothstep(0.75, 1.75, edge));
        }
        color *= smoothstep(-0.5, 0.5, edge);
    }
    return default_post_processing(color);
}
