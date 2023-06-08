import numpy as np
import matplotlib.pyplot as plt
import csv
import pandas as pd

##############################################################################################################
#### enter file path and name:

#path = './test_data/IMU_test_data/'
#filename = '90deg_x.csv'
path = './test_data/Polhemus_test_data/'
filename = 'Polhemus_90degX(clean)_data.csv'

##############################################################################################################

data = pd.read_csv(path + filename)  # Skip the first row containing column names

def quaternion_to_rotation_matrix(q):
    """Converts a quaternion to a 3x3 rotation matrix."""
    q0, q1, q2, q3 = q
    return np.array([[1 - 2*q2*q2 - 2*q3*q3, 2*q1*q2 - 2*q0*q3, 2*q1*q3 + 2*q0*q2],
                     [2*q1*q2 + 2*q0*q3, 1 - 2*q1*q1 - 2*q3*q3, 2*q2*q3 - 2*q0*q1],
                     [2*q1*q3 - 2*q0*q2, 2*q2*q3 + 2*q0*q1, 1 - 2*q1*q1 - 2*q2*q2]])

def calculate_fha(femur_quat, tibia_quat):
    """Calculates the finite helical axis (FHA) of a knee motion from two quaternions."""
    R_femur = quaternion_to_rotation_matrix(femur_quat)
    R_tibia = quaternion_to_rotation_matrix(tibia_quat)

    R_relative = np.dot(R_tibia, np.transpose(R_femur))
    R_relative_trace = np.trace(R_relative)
    R_relative_trace_minus_1 = R_relative_trace - 1

    fha = np.array([R_relative[2, 1] - R_relative[1, 2],
                    R_relative[0, 2] - R_relative[2, 0],
                    R_relative[1, 0] - R_relative[0, 1]])

    if R_relative_trace_minus_1 > 1e-8:
        fha /= 2 * np.sqrt(R_relative_trace * R_relative_trace_minus_1)

    return fha

femur_quat = data[['w1','x1','y1','z1']].values.tolist()
tibia_quat = data[['w2','x2','y2','z2']].values.tolist()

fha_list = []
fha_norm_list = []

for i in range(len(femur_quat)):
    femur = femur_quat[i]
    tibia = tibia_quat[i]
    fha = calculate_fha(femur, tibia)
    fha_norm = fha / np.linalg.norm(fha)
    fha_list.append(fha)
    fha_norm_list.append(fha_norm)

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')

for i in range(len(fha_list)):
    ax.plot([0, fha_list[i][0]], [0, fha_list[i][1]], [0, fha_list[i][2]], color='b')

plt.show()
