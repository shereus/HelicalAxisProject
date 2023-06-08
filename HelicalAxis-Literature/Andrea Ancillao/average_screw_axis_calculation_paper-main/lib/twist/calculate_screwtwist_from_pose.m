function twists = calculate_screwtwist_from_pose(T,dt)
% This function calculates the screw twist from a discrete sequence of poses
% using a central difference scheme.
%
% Input:
%   T: (4x4xN) sequence of N pose matrices T_a_b containing pose of {b} wrt {a}
%   dt: (1x1) time between samples in pose sequence
% Output:
%   twists: (Nx6) screw twist of {b} wrt {a} expressed in frame {a}
%
% Author: Maxim Vochten

% Initialization
N = size(T,3);
twists = zeros(N,6);

% First sample
DeltaT = T(:,:,2)*inverse_pose(T(:,:,1));
dtwist = logm_pose(DeltaT)/(dt);
twists(1,:) = [-dtwist(2,3) dtwist(1,3) -dtwist(1,2) dtwist(1:3,4)'];

% Middle samples (central difference)
for i = 2 : N-1
    DeltaT = T(:,:,i+1)*inverse_pose(T(:,:,i-1));
    dtwist = logm_pose(DeltaT)/(2*dt);
    twists(i,:) = [-dtwist(2,3) dtwist(1,3) -dtwist(1,2) dtwist(1:3,4)'];
end

% Last sample
DeltaT = T(:,:,N)*inverse_pose(T(:,:,N-1));
dtwist = logm_pose(DeltaT)/(dt);
twists(N,:) = [-dtwist(2,3) dtwist(1,3) -dtwist(1,2) dtwist(1:3,4)'];