// -----------------------------------------------------------------------------
// Copyright (c) 2021 Pepe Eulzer. All rights reserved.
// Distributed under the (new) BSD License.
// -----------------------------------------------------------------------------

#version 400

layout (location=0) in vec3 position;
layout (location=1) in vec3 normal;

uniform mat4 VP;
uniform mat4 M;

// if this is 0 -> render as normal surface
// otherwise enlarge the object and render flat
// (used for colored outlines)
uniform float render_flat = 0.0;

out vec3 fnormal;
out vec3 fposition;

void main()
{
    fnormal = mat3(M) * normal;

    if(render_flat == 0.0)
        // pass the transformed surface
        fposition = vec3(M * vec4(position, 1.0));
    else
        // enlarge for outline rendering
        fposition = vec3(M * vec4(position, 1.0)) + vec3(fnormal * render_flat);

    gl_Position = VP * vec4(fposition, 1.0);
}