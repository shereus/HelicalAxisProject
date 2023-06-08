// -----------------------------------------------------------------------------
// Copyright (c) 2021 Pepe Eulzer. All rights reserved.
// Distributed under the (new) BSD License.
// -----------------------------------------------------------------------------

#version 400

layout (location=0) in vec3 position;
layout (location=1) in vec3 normal;
layout (location=2) in vec3 instanceColor;
layout (location=3) in vec3 instanceNormal;
layout (location=4) in vec3 instanceR0;
layout (location=5) in float instanceR0DisplBase;
layout (location=6) in float instanceR0DisplTar;
layout (location=7) in float instancePhi;
layout (location=8) in float instanceL;

uniform mat4 VP;               // projection * view
uniform float scale = 1.0;     // overall scaling
uniform float thickness = 1.0; // scales only glyph thickness
uniform float len = 1.0;       // scales only glyph length
uniform float offset = 0.0;    // translates glyph along axis
uniform int type = 0;          // 0 shaft, 1 tip, 2 shaft preview, 3 tip preview
uniform vec3 tipColor;
uniform int l_abs = 0;         // use |L|?
uniform int r0_loc = 0;        // 0 world, 1 base, 2 tar

out vec3 fnormal;
out vec3 fposition;
flat out vec3 fcolor;
flat out float fPhi;
flat out float fL;

void main()
{
    fPhi = instancePhi;
    if(l_abs == 1) fL = abs(instanceL);
    else fL = instanceL;
    
    vec3 y = normalize(instanceNormal);
    vec3 x = normalize(cross(y, vec3(0.0, 0.0, 1.0)));
    vec3 z = cross(y, x);

    float ts_mod = 1.0;
    fcolor = instanceColor;
    if(type >= 2) ts_mod = 1.1;
    if(type >= 1) fcolor = tipColor;

    // create model matrix (glsl -> columns first)
    vec3 r0 = instanceR0;
    if(r0_loc == 1) r0 = instanceR0 + instanceR0DisplBase * instanceNormal;
    else if(r0_loc == 2) r0 = instanceR0 + instanceR0DisplTar * instanceNormal;
    mat4 model;
    if(type == 0 || type == 2) {
        // this is a shaft
        float ts = thickness * scale * ts_mod;
        model[0].xyz = ts * x;
        model[1].xyz = len * scale * y;
        model[2].xyz = ts * z;
        model[3].xyz = r0 + scale * offset * instanceNormal;
    } else {
        // this is a tip
        float ts = thickness * scale * ts_mod;
        model[0].xyz = ts * x;
        model[1].xyz = ts * y;
        model[2].xyz = ts * z;
        model[3].xyz = r0 + scale * (len + offset) * instanceNormal;
    }

    fnormal = mat3(model) * normal;
    fposition = vec3(model * vec4(position, 1.0));
    gl_Position = VP * vec4(fposition, 1.0);
}