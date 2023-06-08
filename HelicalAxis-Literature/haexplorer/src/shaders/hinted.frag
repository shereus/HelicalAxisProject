// -----------------------------------------------------------------------------
// Copyright (c) 2021 Pepe Eulzer. All rights reserved.
// Distributed under the (new) BSD License.
// -----------------------------------------------------------------------------

#version 400

uniform vec3 cameraPos;

in vec3 fnormal;

out vec4 fragColor;

void main()
{
	vec3 normal = normalize(fnormal);
    vec3 viewVector = normalize(-cameraPos);

    float proj = dot(normal, viewVector);
    if(0.0 < proj && proj < 0.2)
        fragColor = vec4(0.7, 0.7, 0.7, 1.0);
    else
        discard;
}