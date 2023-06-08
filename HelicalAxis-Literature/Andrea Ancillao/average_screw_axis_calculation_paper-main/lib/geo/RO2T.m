function T = RO2T(R,O)
% Assemble pose matrix T from R [3x3xnF]and O [nFx3] 
%   $Date: 2019/01/29
%   $Author: A. Ancillao, 2019%

nF = size(R,3);
T = nan(4,4,nF);
if size(O,1) ~= nF
    disp('Length error');
else
T(1:3,1:3,:) = R;
T(1:3,4,:) = O';
T(4,1:4,:) = repmat([0, 0, 0, 1], [1,1,nF]);
    
end

end

