function [m,v]=mvarray(a)
% Norm and unitvector associated to a vector [nF x 3]
% Output: m [nFx1], v [nFx3]
% The output is in the form of an array: meaning that the norm is
% calculated for each frame of the input array


m = sqrt (sum (a.^2,2));
nD = size(a,2);
v = a./repmat(m,[1,nD]);
end