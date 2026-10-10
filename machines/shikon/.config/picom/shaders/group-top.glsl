#version 330
// The tab strip supplies only the upper corners of the combined group.
in vec2 texcoord;
uniform sampler2D tex;
uniform vec2 effective_size;
vec4 default_post_processing(vec4 color);

vec4 window_shader() {
    vec2 texsize = vec2(textureSize(tex, 0));
    vec4 color = texture(tex, texcoord / texsize);
    float radius = min(16.0, min(effective_size.x * 0.5, effective_size.y));
    float x = min(texcoord.x, effective_size.x - texcoord.x);
    if (x < radius && texcoord.y < radius) {
        float distance_to_corner = length(vec2(x, texcoord.y) - vec2(radius));
        color *= 1.0 - smoothstep(radius - 0.5, radius + 0.5, distance_to_corner);
    }
    return default_post_processing(color);
}
