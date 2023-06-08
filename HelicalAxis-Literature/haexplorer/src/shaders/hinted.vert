// -----------------------------------------------------------------------------
// Copyright (c) 2021 Pepe Eulzer. All rights reserved.
// Distributed under the (new) BSD License.
// -----------------------------------------------------------------------------

#version 400

layout (location=0) in vec3 position;
layout (location=1) in vec3 normal;

uniform mat4 VP;
uniform mat4 M;

out vec3 fnormal;

void main()
{
    fnormal = mat3(M) * normal;
    gl_Position = VP * M * vec4(position, 1.0);
}