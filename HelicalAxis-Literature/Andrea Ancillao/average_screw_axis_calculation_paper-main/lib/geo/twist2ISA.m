function [n,s,T] = twist2ISA(tw)
% Calculate the ISA from the screw twist of body 2 with respect to body 1
% Uses procedure as described in (De Schutter 2010).

% [n,s] = twist2ISA(tw)
%
% Inputs:
%       tw = [nFx6] the screw twist of body 2 with respect to body 1
%
% Outputs:
%       n, s, [nFx3] and [nFx3]  direction and position of the ISA in the same CS as the twist
%       T [4x4xnF] the CS attached to each ISA

% Andrea Ancillao
% Leuven 10-2020
% andrea.ancillao@kuleuven.be
%
% Revision
% Andrea Ancillao
% Rome, 08/2021


w = tw(:,1:3);
v = tw(:,4:6);
[wmod, n] = mvarray(w);
s = (cross(w,v)./(wmod.^2));            
[~ , y] = mvarray( cross(n,s));
z = cross(n,y);

nF = size(tw,1);

% build matrix T
T = nan(4,4,nF);
for k=1:nF
    O = s(k,:)';
    e1 = n(k,:)';
    e2 = y(k,:)';
    e3 = z(k,:)';
    
    T(:,:,k) = [ [e1,e2,e3,O] ; [0,0,0,1] ];
end

end

