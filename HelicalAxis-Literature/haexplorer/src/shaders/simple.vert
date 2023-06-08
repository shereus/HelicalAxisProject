// -----------------------------------------------------------------------------
// Copyright (c) 2021 Pepe Eulzer. All rights reserved.
// Distributed under the (new) BSD License.
// -----------------------------------------------------------------------------

#version 400

layout (location=0) in vec3 position;
layout (location=1) in vec3 normal;

uniform mat4 MVP;

smooth out vec3 fnormal;

void main()
{
    fnormal = normal;
    gl_Position = MVP * vec4(position, 1.0);
}