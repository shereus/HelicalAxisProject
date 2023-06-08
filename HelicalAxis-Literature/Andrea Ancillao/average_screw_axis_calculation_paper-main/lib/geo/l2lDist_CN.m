function [dist, dist1xyz] = l2lDist_CN(l1, l2)
% Calculate the distance between two lines along the common normal.
% New implementation - project s to s distance
%
% [dist] = l2lDist(l1, l2)
%
% l1 and l2 are the two lines defined as [n, s] (direction and position)
% size [1 x 6]
% 
% dist is the distance along the common normal
%
% Changed calculation of the distance as in the meeting of 18/11/2021
% difference s2-s1 projected onto the common normal.
% And handling of the singular cases.
%
% Andrea Ancillao,
% Leuven 18/11/2021

if size(l1,1) >1 || size(l2,1) >1 
    error('Error');
end

n1 = l1(:,1:3);
s1 = l1(:,4:6);
n2 = l2(:,1:3);
s2 = l2(:,4:6);

diff = s2 - s1; % this is the distance between the origins

n = cross(n1,n2,2); % this is the common normal.
nN = norm(n);
n = n./nN; % unitary vector

if nN < 1e-8 % e-8 as in eTASL
    % calculate distance in the singular case
    dist = norm( diff-n1 .* dot(n1,diff));
else
    % distance along common normal
    dist = abs( dot(n,diff));
end

dist1xyz = dist .* n; % project dist to the n

end


