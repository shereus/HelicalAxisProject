% In this script is meant to demonstrate the ASA calculation routines for representing the motion of joints.
% The purpose of this analysis is to demonstrate the following procedures:
%   Calculation of the ASA
%   Calculation of the coordinate system attached to the ASA
%   Analysis of the uncertainty in the ASA calculation
%   Test the regularization term: epsilon
%
%  The calculation of the ASA is implemented in the function twist2ASA.m
%
% It is recommended to run the code section-by-section
% 
%
% Datasets explored:
%   1: Free swing of an artificial hinge
%   2: Ideal numerically-generated cyclindrical motion
%
% Robotics Research Group 
% Dept. of Mechanical Engineering
% KU Leuven
%
% Last revision: 02/2022


clear
close all
clc
addpath(genpath('lib'));



%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Hinge
load('/Users/nicolas/Library/CloudStorage/OneDrive-VrijeUniversiteitBrussel/Onderzoek/Helical axis/Andrea Ancillao/average_screw_axis_calculation_paper-main/DATA/SampleHinge.mat');
hinge = HingeCycle;
% Get the poses and calculate the screw twist
T1 = hinge.T1_0;
T2 = hinge.T2_0;
T2_1 = Tcat(Hinv(T1) , T2);
t21_1 = calculate_screwtwist_from_pose(T2_1,1/hinge.fs);
GA_1 = hinge.GA_1;

% Calculate the ISA, the ASA
[n, s, T] = twist2ISA(t21_1);
ISA = [n,s];

prior = GA_1(1,4:6); % use as prior the S point of the GA axis.
epsilon = 0.001;
[n,s,T,an,an2] = twist2ASA(t21_1,epsilon,prior);
ASA = [n,s];
ASA_T = T;
ASA_0 = transfAxis(ASA,T1);
ASA_T_0 = Tcat(T1,ASA_T);

% dispersion analysis on orientation
Magnitude_ellipsoid_rad_s = [ an.ma ; an.mb; an.mc ]
rho1 = an.alpha1
rho2 = an.alpha2

% dispersion analysis on S
Magnitude_ellipsoid_rad_s_S = [ an2.ma ; an2.mb; an2.mc ].*1000
rho1_S = an2.alpha1
rho2_S = an2.alpha2

% Plot the ellipsoids
figure;
subplot 121
hold on; grid on; box on; grid minor;
% Transform data to ASA CS
T1_asa = Hinv(ASA_T);
R1_asa = T2RO(T1_asa);
an.va = transfVect(an.va',R1_asa)';
an.vb = transfVect(an.vb',R1_asa)';
an.vc = transfVect(an.vc',R1_asa)';
sc1 = 1.5 * an.ma;
sc2 = 0.25 * an.ma;
ASA_asa = [1,0,0,0,0,0];
h2 = plotSA(ASA_asa,sc1,'g','lineWidth',3);
h4 = plotUncertainty(eye(4),an);
h3 = plotH(sc2,eye(4),'g');
axis equal;
view([100 , 10]);
legend([h2, h3, h4],{'ASA','ASA CS','Confidence Ellipsoid'},'Location','southeast');
title('ASA confidence - Orientation');
xlabel('x [rad/s]');
ylabel('y [rad/s]');
zlabel('z [rad/s]');

subplot 122
hold on; grid on; box on; grid minor;
% Transform data to ASA CS
an2.va = transfVect(an2.va',R1_asa)';
an2.vb = transfVect(an2.vb',R1_asa)';
an2.vc = transfVect(an2.vc',R1_asa)';
% convert in mm
an2.ma = an2.ma * 1000;
an2.mb = an2.mb * 1000;
an2.mc = an2.mc * 1000;
sc1 = 1.5 * an2.ma; % scale factor for plot
sc2 = 0.25 * an2.ma;
ASA_asa = [1,0,0,0,0,0];
h2 = plotSA(ASA_asa,sc1,'g','lineWidth',3);
h4 = plotUncertainty(eye(4),an2);
h3 = plotH(sc2,eye(4),'g');
axis equal;
view([100 , 10]);
legend([h2, h3, h4],{'ASA','ASA CS','Confidence Ellipsoid'},'Location','southeast');
title('ASA confidence - Position');
xlabel('x [mm]');
ylabel('y [mm]');
zlabel('z [mm]');

sgtitle('ASA confidence analysis - Hinge');



%% Test the effect of the regularization

% Case no regularization (generate reference)
[n,s,~,~] = twist2ASA(t21_1,0,prior);
ASA_ref = [n,s];

% Cases with regularization
epsilon = 0.0001
[n,s,T,an,an2] = twist2ASA(t21_1,epsilon,prior);
ASA = [n,s];
ASA_T = T;
[ang, dist1, dist2] = compareAxes_CN(ASA,ASA_ref);
Dist_common_normal_mm = dist1 *1000
Dist_GA_center_to_CoR_mm = dist2 * 1000


epsilon = 0.001
[n,s,T,an,an2] = twist2ASA(t21_1,epsilon,prior);
ASA = [n,s];
ASA_T = T;
[ang, dist1, dist2] = compareAxes_CN(ASA,ASA_ref);
Dist_common_normal_mm = dist1 *1000
Dist_GA_center_to_CoR_mm = dist2 * 1000

epsilon = 0.01
[n,s,T,an,an2] = twist2ASA(t21_1,epsilon,prior);
ASA = [n,s];
ASA_T = T;
[ang, dist1, dist2] = compareAxes_CN(ASA,ASA_ref);
Dist_common_normal_mm = dist1 *1000
Dist_GA_center_to_CoR_mm = dist2 * 1000

epsilon = 0.1
[n,s,T,an,an2] = twist2ASA(t21_1,epsilon,prior);
ASA = [n,s];
ASA_T = T;
[ang, dist1, dist2] = compareAxes_CN(ASA,ASA_ref);
Dist_common_normal_mm = dist1 *1000
Dist_GA_center_to_CoR_mm = dist2 * 1000


clear;
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Cylindrical motion
load('/Users/nicolas/Library/CloudStorage/OneDrive-VrijeUniversiteitBrussel/Onderzoek/Helical axis/Andrea Ancillao/average_screw_axis_calculation_paper-main/DATA/IdealCylMotData.mat');
CylMot = CylMotCycle;
%T1 = repmat(CylMot.T1_0 , [1,1,size(CylMot.T2_0,3)]);
T1 = CylMot.T1_0;
T2 = CylMot.T2_0;
T2_1 = Tcat(Hinv(T1) , T2);
fs = CylMot.fs;
t21_1 = calculate_screwtwist_from_pose(T2_1,1/fs);
GA_1 = CylMot.GA_1;


% Calculate the ISA, the ASA
[n, s, T] = twist2ISA(t21_1);
ISA = [n,s];

prior = GA_1(1,4:6); % use as prior the S point of the GA axis.
epsilon = 0.001;
[n,s,T,an,an2] = twist2ASA(t21_1,epsilon,prior);
ASA = [n,s];
ASA_T = T;
ASA_0 = transfAxis(ASA,T1);
ASA_T_0 = Tcat(T1,ASA_T);

% dispersion analysis on orientation
Magnitude_ellipsoid_rad_s = [ an.ma ; an.mb; an.mc ]
rho1 = an.alpha1
rho2 = an.alpha2

% dispersion analysis on S
Magnitude_ellipsoid_rad_s_S = [ an2.ma ; an2.mb; an2.mc ].*1000
rho1_S = an2.alpha1
rho2_S = an2.alpha2

% Plot the ellipsoids
figure;
subplot 121
hold on; grid on; box on; grid minor;
% Transform data to ASA CS
T1_asa = Hinv(ASA_T);
R1_asa = T2RO(T1_asa);
an.va = transfVect(an.va',R1_asa)';
an.vb = transfVect(an.vb',R1_asa)';
an.vc = transfVect(an.vc',R1_asa)';
sc1 = 1.5 * an.ma;
sc2 = 0.25 * an.ma;
ASA_asa = [1,0,0,0,0,0];
h2 = plotSA(ASA_asa,sc1,'g','lineWidth',3);
h4 = plotUncertainty(eye(4),an);
h3 = plotH(sc2,eye(4),'g');
axis equal;
view([100 , 10]);
legend([h2, h3, h4],{'ASA','ASA CS','Confidence Ellipsoid'},'Location','southeast');
title('ASA confidence - Orientation');
xlabel('x [rad/s]');
ylabel('y [rad/s]');
zlabel('z [rad/s]');

subplot 122
hold on; grid on; box on; grid minor;
% Transform data to ASA CS
an2.va = transfVect(an2.va',R1_asa)';
an2.vb = transfVect(an2.vb',R1_asa)';
an2.vc = transfVect(an2.vc',R1_asa)';
% convert in mm
an2.ma = an2.ma * 1000;
an2.mb = an2.mb * 1000;
an2.mc = an2.mc * 1000;
sc1 = 1.5 * an2.ma; % scale factor for plot
sc2 = 0.25 * an2.ma;
ASA_asa = [1,0,0,0,0,0];
h2 = plotSA(ASA_asa,sc1,'g','lineWidth',3);
h4 = plotUncertainty(eye(4),an2);
h3 = plotH(sc2,eye(4),'g');
axis equal;
view([100 , 10]);
legend([h2, h3, h4],{'ASA','ASA CS','Confidence Ellipsoid'},'Location','southeast');
title('ASA confidence - Position');
xlabel('x [mm]');
ylabel('y [mm]');
zlabel('z [mm]');

sgtitle('ASA confidence analysis - Ideal Motion');



%% Test the effect of the regularization

% Case no regularization (generate reference)
[n,s,~,~] = twist2ASA(t21_1,0,prior);
ASA_ref = [n,s];

% Cases with regularization
epsilon = 0.0001
[n,s,T,an,an2] = twist2ASA(t21_1,epsilon,prior);
ASA = [n,s];
ASA_T = T;
[ang, dist1, dist2] = compareAxes_CN(ASA,ASA_ref);
Dist_common_normal_mm = dist1 *1000
Dist_GA_center_to_CoR_mm = dist2 * 1000


epsilon = 0.001
[n,s,T,an,an2] = twist2ASA(t21_1,epsilon,prior);
ASA = [n,s];
ASA_T = T;
[ang, dist1, dist2] = compareAxes_CN(ASA,ASA_ref);
Dist_common_normal_mm = dist1 *1000
Dist_GA_center_to_CoR_mm = dist2 * 1000

epsilon = 0.01
[n,s,T,an,an2] = twist2ASA(t21_1,epsilon,prior);
ASA = [n,s];
ASA_T = T;
[ang, dist1, dist2] = compareAxes_CN(ASA,ASA_ref);
Dist_common_normal_mm = dist1 *1000
Dist_GA_center_to_CoR_mm = dist2 * 1000

epsilon = 0.1
[n,s,T,an,an2] = twist2ASA(t21_1,epsilon,prior);
ASA = [n,s];
ASA_T = T;
[ang, dist1, dist2] = compareAxes_CN(ASA,ASA_ref);
Dist_common_normal_mm = dist1 *1000
Dist_GA_center_to_CoR_mm = dist2 * 1000



