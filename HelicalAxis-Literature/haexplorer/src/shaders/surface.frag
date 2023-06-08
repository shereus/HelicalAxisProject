// -----------------------------------------------------------------------------
// Copyright (c) 2021 Pepe Eulzer. All rights reserved.
// Distributed under the (new) BSD License.
// -----------------------------------------------------------------------------

#version 400

uniform vec3 cameraPos;
uniform float opacity = 0.0;
uniform vec4 phiLBounds = vec4(-1000, 1000, -1000, 1000);

in vec3 fnormal;
in vec3 fposition;
in vec3 fcolor;
flat in float fPhi;
flat in float fL;

out vec4 fragColor;

const float ambient = 0.1;

void main()
{
    if(opacity < 0.01) discard;
    if(fPhi < phiLBounds[0] ||
       fPhi > phiLBounds[1] ||
         fL < phiLBounds[2] ||
         fL > phiLBounds[3])
    {
        // this part of the surface is not in the selected ROI
        discard;
    }


    // shading on
    //vec3 normal = normalize(fnormal);
    //vec3 lightDir = normalize(cameraPos - fposition); // camera = light
    //float diffuse = abs(dot(normal, lightDir));
    //fragColor = vec4((ambient + diffuse) * fcolor, opacity);

    // shading off
    fragColor = vec4(fcolor, opacity);
}