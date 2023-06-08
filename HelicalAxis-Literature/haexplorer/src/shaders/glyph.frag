// -----------------------------------------------------------------------------
// Copyright (c) 2021 Pepe Eulzer. All rights reserved.
// Distributed under the (new) BSD License.
// -----------------------------------------------------------------------------

#version 400

uniform vec3 cameraPos;
// [phi_min, phi_max, L_min, L_max]
uniform vec4 phiLBounds = vec4(-1000, 1000, -1000, 1000);
uniform int type;

in vec3 fnormal;
in vec3 fposition;
flat in vec3 fcolor;
flat in float fPhi;
flat in float fL;

out vec4 fragColor;

const float ambient = 0.4;

void main()
{
    if(type <= 1 &&
       (fPhi < phiLBounds[0] ||
        fPhi > phiLBounds[1] ||
        fL < phiLBounds[2]   ||
        fL > phiLBounds[3]))
    {
        // this glyph is not in the selected ROI
        discard;
    }

	vec3 normal = normalize(fnormal);
	vec3 lightDir = normalize(cameraPos - fposition); // camera = light position
    float diffuse = max(dot(normal, lightDir), 0.0);

    float scale = min((ambient + diffuse), 1.0);
    fragColor = vec4(scale * fcolor, 1.0);
}