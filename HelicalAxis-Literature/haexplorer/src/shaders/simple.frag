// -----------------------------------------------------------------------------
// Copyright (c) 2021 Pepe Eulzer. All rights reserved.
// Distributed under the (new) BSD License.
// -----------------------------------------------------------------------------

#version 400

smooth in vec3 fnormal;
out vec4 fragColor;

void main()
{
    fragColor = vec4(fnormal, 1.0);
}