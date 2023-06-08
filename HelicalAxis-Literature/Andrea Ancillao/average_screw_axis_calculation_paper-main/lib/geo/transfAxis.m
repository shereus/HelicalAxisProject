function out = transfAxis(in,T1_2)

n = in(:,1:3);
s = in(:,4:6);

R = T2RO(T1_2);

n1 = transfVect(n,R);
s1 = transfPoint(s,T1_2);

out = [n1,s1];
end
