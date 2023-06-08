// -----------------------------------------------------------------------------
// Copyright (c) 2021 Pepe Eulzer. All rights reserved.
// Distributed under the (new) BSD License.
// -----------------------------------------------------------------------------

#version 400

layout (location=0) in vec3 position;
layout (location=1) in vec3 normal;
layout (location=2) in vec3 direction; // direction of glyph, length needs to be the default scale
layout (location=3) in vec3 color;
layout (location=4) in float phi;
layout (location=5) in float L;
layout (location=6) in float displ_base;
layout (location=7) in float displ_tar;

uniform mat4 VP;
uniform float len = 1.0;     // scales glyph length
uniform float offset = 0.0;  // translates glyph along axis
uniform int l_abs = 0;       // use |L|?
uniform int r0_loc = 0;      // 0 world, 1 base, 2 tar

out vec3 fnormal;
out vec3 fposition;
out vec3 fcolor;
flat out float fPhi;
flat out float fL;

void main()
{
    fnormal = normal;
    fposition = position;
    if(r0_loc == 1) fposition = position + displ_base * normalize(direction);
    else if(r0_loc == 2) fposition = position + displ_tar * normalize(direction);
    fcolor = color;
    fPhi = phi;
    if(l_abs == 1) fL = abs(L);
    else fL = L;

    if(gl_VertexID % 2 == 0) {
        // this is a glyph origin
        fposition += direction * offset;
    } else {
        // this is a glyph endpoint
        fposition += direction * offset;
        fposition += direction * (len-1.0);
    }
    gl_Position = VP * vec4(fposition, 1.0);
}