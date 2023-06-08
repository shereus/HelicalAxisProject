function h = plotUncertainty(T,an,scale)
% Plots the ellipsoid
% Andrea Ancillao
% Leuven 5-2021

N = 50;

if nargin <3 
    scale = 1;
end

ma = scale * an.ma;
mb = scale * an.mb;
mc = scale * an.mc;

if scale ==0
    mb = mb/ma;
    mc = mc/ma;
    ma = 1; 
end
    

[X,Y,Z] = ellipsoid(0,0,0,ma,mb,mc,N);

% Rotate and translate to the ASA T
nF = size(X,1);
for k=1:nF
    for j=1:nF
        P = [X(k,j) , Y(k,j) , Z(k,j)];
        P2 = transfPoint(P,T);
        X2(k,j) = P2(1);
        Y2(k,j) = P2(2);
        Z2(k,j) = P2(3);
    end
end

CO(:,:,1) = ones(N+1).*linspace(0,1,N+1); % red
CO(:,:,2) = zeros(N+1).*linspace(0.5,0.6,N+1); % green
CO(:,:,3) = zeros(N+1).*linspace(0,1,N+1); % blue

h = mesh(gca,X2,Y2,Z2);

end

