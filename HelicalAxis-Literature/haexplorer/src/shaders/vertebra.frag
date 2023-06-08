// -----------------------------------------------------------------------------
// Copyright (c) 2021 Pepe Eulzer. All rights reserved.
// Distributed under the (new) BSD License.
// -----------------------------------------------------------------------------

#version 400

uniform vec3 cameraPos;
uniform vec3 color;
uniform float ambient = 0.1;

// if this is 0 -> render as normal surface
// otherwise enlarge the object and render flat
// (used for colored outlines)
uniform float render_flat = 0.0;
uniform vec3 outline_color = vec3(0.0, 0.0, 0.0);

in vec3 fnormal;
in vec3 fposition;

out vec4 fragColor;

void main()
{
    if (render_flat == 0.0) {
        // render as a diffuse surface
	    vec3 normal = normalize(fnormal);
	    vec3 lightDir = normalize(cameraPos - fposition); // camera = light position
        float diffuse = max(dot(normal, lightDir), 0.0);
        fragColor = vec4((ambient + diffuse) * color, 1.0);
    } else {
        // render a solid color for the outline
        fragColor = vec4(outline_color, 1.0);
    }
}