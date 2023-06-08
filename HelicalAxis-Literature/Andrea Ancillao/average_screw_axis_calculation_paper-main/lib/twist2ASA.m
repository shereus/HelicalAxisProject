function [n,s,T,analysis,analysis2] = twist2ASA(tw, regul_pos, prior_origin, regul_omega)
% Calculates the ASA axis, the CoR and the full ASA CS based on a set of screw twists.
% The ASA direction corresponds to the x-axis of the ASA CS
% No constraints on the direction of the x-axis are applied within this script. 
% (If the axis is needed to point a specific direction with respect to the subject, apply the correction after running this script.
% Remember to correct both n and T).
%
%
% [n,s,T,analysis,analysis2] = twist2ASA(tw, regul_pos, prior_origin, regul_omega)
% Input: tw = [nF x 6] screw twist of body 2 with respect to body 1
%        regul_pos    = (optional) scalar regularization weight on the prior origin, 0 by default
%        prior_origin = (optional) [3x1] position vector used in regularization to indicate initial guess for origin, [0;0;0] by default
%		 regul_omega  = (optional) [3x3] regularisation matrix added to covariance matrix of rotation, 3x3 zeros by default
%    
% Output: n = [1x3] ASA direction
%         s = [1x3] ASA position == CoR  
%		  T = [4x4] full ASA frame
% 
% Dispersion analysis of the direction
%           analysis.va --> directions of the principal components
%           analysis.vb 
%           analysis.vc
%           analysis.ma --> magnitudes of the semi-axes of the ellipsoid
%           analysis.mb 
%           analysis.mc 
%           analysis.alpha1 --> ratio of eigenvalues. sqrt of (2nd + 3rd) over 1st
%           analysis.alpha2 --> sqrt of 3rd over 2nd
%
% Dispersion analysis of the position
%           analysis2.va --> directions of the principal components
%           analysis2.vb 
%           analysis2.vc
%           analysis2.ma --> magnitudes of the semi-axes of the ellipsoid
%           analysis2.mb 
%           analysis2.mc 
%           analysis2.alpha1 --> ratio of eigenvalues. sqrt of (2nd + 3rd) over 1st
%           analysis2.alpha2 --> sqrt of 3rd over 2nd
%
%
% Notes on the calculation:
% The CoR is the point that is closest to all of the instantaneous screw axes of the input twists.  
% The distances are weighted with the amplitude of the rotational velocity, such that noisy screw axes corresponding to low rotational velocities do not skew the results.
% For the average frame the following holds:
% - The X-axis corresponds to the (weighted) mean orientation of the rotational velocities
% - The X-Z plane is the plane that best fits the rotational velocity vectors.  The Y-axis is the normal of this plane
% - The Z-axis is the remaining direction of the frame: cross(X,Y)
% - The sign of the X-axis is determined by the mean of the rotational velocity projected on the X-axis of the frame
% By construction, the RMS value of the screw twists expressed in this new frame have the following properties: 
% for the rotational component, RMS of omega_x is largest, RMS of omega_y is smallest.
%
% Robotics Research Group 
% Dept. of Mechanical Engineering
% KU Leuven
%
% Last revision: 02/2022


if nargin < 2
    regul_pos = 0;
    prior_origin = [0,0,0];
    regul_omega = zeros(3,3);
elseif nargin < 3
    prior_origin = [0,0,0];
    regul_omega = zeros(3,3);
elseif nargin < 4
    regul_omega = zeros(3,3);
end


% remove NaN
if sum(isnan(tw(:,1))) >0
    nanindex = isnan(tw(:,1));
    nF = size(tw,1);
    tw2 = [];
    for k=1:nF
        if ~nanindex(k)
            tw2 = [tw2 ; tw(k,:) ];
        end
    end
            
   tw = tw2;
end
nF = size(tw,1);
w = tw(:,1:3);
v = tw(:,4:6);

% Initialization
omega_sum = zeros(3,1);
outerprod_sum = zeros(3,3);
innerprod_sum = 0;
rhs_sum = zeros(3,1);
w_sum = zeros(3,3);
crossprod_sum = zeros(3,1);
skewomegaprod_sum = zeros(3,3);
for i=1:nF
    crs = cross( w(i,:) , v(i,:) ); %[1 x 3]
    inner = w(i,:) * w(i,:)'; 
    outer = w(i,:)' * w(i,:);  % [3 x 3]
	omega_sum = omega_sum + w(i,:)';
	innerprod_sum = innerprod_sum + inner; 
	outerprod_sum = outerprod_sum + outer; 
    rhs_sum = rhs_sum + crs';  
    
    omega = tw(i,1:3)';
    v0 = tw(i,4:6)';
    crossprod_sum = crossprod_sum + cross(omega,v0); %cross(omega,v0)
    skewomegaprod_sum = skewomegaprod_sum + skew(omega)*skew(omega);% [omega][omega]
end

% Calculate average intersection point of all screw axes
%s = inv((innerprod_sum./nF+regul_pos)*eye(3) - outerprod_sum./nF) * (crossprod_sum./nF + regul_pos*prior_origin'); % regularized approach
s = ((innerprod_sum./nF+regul_pos)*eye(3) - outerprod_sum./nF) \ (crossprod_sum./nF + regul_pos*prior_origin');   
s = s';

% Singular value decomposition
[U,S,~] = svd(outerprod_sum./nF + regul_omega);

% e1 of ASA as the main direction of w
d = U(:,1);
sx = sign(dot(d,omega_sum)); % determine sign 
n = (sx*d)' ; 

% e2 of ASA is the third direction (normal to average plane in which omega moves) 
e2 = U(:,3)';

% e3
e3 = cross(n,e2);

% build matrix T
% ASA along x axis
O = s';
e1 = n';
e2 = e2';
e3 = e3';
T = [ [e1,e2,e3,O] ; [0,0,0,1] ];



%% Dispersion on orientation: Estimating the uncertainty / variations
va = U(:,1);    % directions of the ellipsoid        
vb = U(:,2);  
vc = U(:,3); 

sigma_a = sqrt(S(1,1));  
sigma_b = sqrt(S(2,2)); 
sigma_c = sqrt(S(3,3)); 


% ellipsoid 
beta = 0.95;
z_beta = chi2inv(beta,3);  
ma = sqrt(z_beta)*sigma_a; % units is rad/s
mb = sqrt(z_beta)*sigma_b;
mc = sqrt(z_beta)*sigma_c;

% Ratio of eigenvalues
alpha1 = sqrt( (S(2,2) + S(3,3)) / S(1,1) ); % sum of second and third divided by 1st
alpha2 = sqrt( ( S(3,3)) / S(2,2) ); % third eig div by the 2nd

analysis.s = s;
analysis.va = va;
analysis.vb = vb;
analysis.vc = vc;
analysis.ma = ma;
analysis.mb = mb;
analysis.mc = mc;
analysis.alpha1 = alpha1;
analysis.alpha2 = alpha2;
analysis.sigma_a = sigma_a;
analysis.sigma_b = sigma_b;
analysis.sigma_c = sigma_c;




%% Dispersion analysis on the position 

obj_p_asa   = 0;
for i = 1 : nF
    obj_p_asa = obj_p_asa + norm(v(i,:)'-cross(O,w(i,:)'))^2; % [m/s]^2
end
obj_p_asa           = obj_p_asa/(nF*(3*nF-3)); 
A                   = (innerprod_sum*eye(3) - outerprod_sum)./nF; % [rad/s]^2
[U_orig,S_orig,~]   = svd(A);
r_orig              = [sqrt(obj_p_asa/S_orig(1,1)) sqrt(obj_p_asa/S_orig(2,2)) sqrt(obj_p_asa/S_orig(3,3))]; % ([m/s]^2/[rad/s]^2)^0.5 = [m]


% Ratio of eigenvalues
zeta1_orig = (r_orig(2) + r_orig(1)) / r_orig(3) ; % []
zeta2_orig = r_orig(1) / r_orig(2);

% Ellipsoid 
beta = 0.95;
z_beta = chi2inv(beta,3);  
ma_orig = sqrt(z_beta)*r_orig(3); % [m]
mb_orig = sqrt(z_beta)*r_orig(2);
mc_orig = sqrt(z_beta)*r_orig(1);
va_orig = U_orig(:,1);    % directions of the ellipsoid        
vb_orig = U_orig(:,2);  
vc_orig = U_orig(:,3); 


% Output 2
analysis2.va = va_orig;
analysis2.vb = vb_orig;
analysis2.vc = vc_orig;
analysis2.ma = ma_orig;
analysis2.mb = mb_orig;
analysis2.mc = mc_orig;
analysis2.alpha1 = zeta1_orig;
analysis2.alpha2 = zeta2_orig;
analysis2.sigma_a = r_orig(3);
analysis2.sigma_b = r_orig(2);
analysis2.sigma_c = r_orig(1);



end
