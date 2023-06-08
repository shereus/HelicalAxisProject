# -----------------------------------------------------------------------------
# Copyright (c) 2021 Pepe Eulzer. All rights reserved.
# Distributed under the (new) BSD License.
# -----------------------------------------------------------------------------

import os
import numpy as np

def markerToRv(marker_path):
    """
    Converts a list of marker positions to a list of model transformations R, v.
    Caches the _rot.txt and _pos.txt files.
    The first row in the list of marker positions describe the locations
    in object coordinates. All further rows are interpreted as timesteps (world coordinates).
    Note that |markers| >= 3.
    """
    markers = np.loadtxt(marker_path, dtype=np.float32, comments="#")

    # get number of markers, reshape
    n_markers = int(markers.shape[1] / 3)
    n_timesteps = int(markers.shape[0] - 1)
    if n_markers*3 != markers.shape[1]:
        print("markerToRv: Columns not divisible by 3. Each marker must be given as x y z.")
    markers = markers.reshape(-1, n_markers, 3)
    
    # first row is reference frame
    M0 = markers[0]
    M0_centroid = np.mean(M0, axis=0)
    markers = markers[1:]

    rot = np.zeros((n_timesteps, 9), dtype=np.float32)
    pos = np.zeros((n_timesteps, 3), dtype=np.float32)
    for i in range(n_timesteps):
        # transformation of M0 -> M1 using the Kabsch algorithm
        M1 = markers[i]
        M1_centroid = np.mean(M1, axis=0)

        # covariance matrix -> svd -> least squares rotation
        H = (M0 - M0_centroid).T @ (M1 - M1_centroid)
        U,_,V = np.linalg.svd(H)
        V = V.T # numpy nonsense (seriously, why?)
        S = np.eye(3) # check to ensure a right-hand system
        S[2,2] = np.sign(np.linalg.det(V@U.T))
        R = V @ S @ U.T

        # translation
        v = M1_centroid - R @ M0_centroid

        rot[i] = R.reshape(9)
        pos[i] = v

    head, tail = os.path.split(marker_path)
    object_name = tail.split('_')[0]
    rot_path = head + "/" + object_name + "_rot.txt"
    pos_path = head + "/" + object_name + "_pos.txt"
    np.savetxt(rot_path, rot)
    np.savetxt(pos_path, pos)

def computeFHAworld(R, v):
    """
    Computes the finite helical axes from a list of model transformations R, v.
    The result is relative to the world ("traditional" FHA)

    Returns four np.arrays with one element per time step:
      - n: normal vector (direction) of helical axis
      - r0: helical axis support vector closest to origin
      - phi: rotation around axis in [0,pi]
      - l: displacement length along axis (can be negative)
    """
    # shift entries
    R_pre = R[:-1,:,:]
    v_pre = v[:-1,:]
    R_post = R[1:,:,:]
    v_post = v[1:,:]

    # result arrays containing every timestep
    n =   np.zeros(v_pre.shape)
    r0 =  np.zeros(v_pre.shape)
    r0_displ_base = np.zeros(v_pre.shape[0])
    r0_displ_tar =  np.zeros(v_pre.shape[0])
    phi = np.zeros(v_pre.shape[0])
    l =   np.zeros(v_pre.shape[0])

    for i in range(v_pre.shape[0]):
        # calculate pre->post matrices
        R = R_post[i] @ R_pre[i].T
        v = v_post[i] - (R @ v_pre[i])

        # calculate this timestep
        n[i], r0[i], phi[i], l[i] = matrixVectorToHA(R, v)

        # compute alternative locations for r0
        r0_displ_tar[i]  = np.dot(n[i], v_pre[i])

    return n, r0, r0_displ_base, r0_displ_tar, phi, l


def computeFHAref(R_ref, v_ref, R, v):
    """
    Computes the finite helical axes from a list of model transformations R, v.
    The result is relative to the transformations of a reference system R_ref, v_ref.

    Returns four np.arrays with one element per time step:
      - n: normal vector (direction) of helical axis
      - r0: helical axis support vector closest to origin
      - phi: rotation around axis in [0,pi]
      - l: displacement length along axis (can be negative)
    """
    # shift entries
    R_pre = R[:-1,:,:]
    v_pre = v[:-1,:]
    R_post = R[1:,:,:]
    v_post = v[1:,:]

    R_ref_pre = R_ref[:-1,:,:]
    v_ref_pre = v_ref[:-1,:]
    R_ref_post = R_ref[1:,:,:]
    v_ref_post = v_ref[1:,:]

    # result arrays containing every timestep
    n =             np.zeros(v_pre.shape)
    r0 =            np.zeros(v_pre.shape)
    r0_displ_base = np.zeros(v_pre.shape[0])
    r0_displ_tar =  np.zeros(v_pre.shape[0])
    phi =           np.zeros(v_pre.shape[0])
    l =             np.zeros(v_pre.shape[0])

    for i in range(v_pre.shape[0]):
        # calculate pre->post matrices
        R = R_post[i] @ R_pre[i].T
        v = v_post[i] - (R @ v_pre[i])
        R_ref = R_ref_post[i] @ R_ref_pre[i].T
        v_ref = v_ref_post[i] - (R_ref @ v_ref_pre[i])

        # rotation/translation relative to the reference system
        R = R_ref.T @ R
        v = R_ref.T @ (v - v_ref)

        # calculate this timestep
        n[i], r0[i], phi[i], l[i] = matrixVectorToHA(R, v)

        # compute alternative locations for r0
        r0_displ_base[i] = np.dot(n[i], v_ref_pre[i])
        r0_displ_tar[i]  = np.dot(n[i], v_pre[i])

    return n, r0, r0_displ_base, r0_displ_tar, phi, l


def computeFHAref_projectFirst(R_ref, v_ref, R, v):
    """
    First projects R,v into the reference system, then computes the traditional
    FHA, then re-projects the system back into the world.
    Results are exactly the same as computeFHAref, except r0 is closest to the center of
    the reference instead of the world origin.
    """
    # rotation/translation relative to the reference system
    R = R_ref.transpose(0,2,1) @ R
    v -= v_ref
    v = R_ref.transpose(0,2,1) @ v[:,:,None]
    v = v.reshape(-1,3)

    # compute traditional FHA
    n, r0, phi, l = computeFHAworld(R, v)

    # re-project into world
    n  = R_ref[:-1,:,:] @ n[:,:,None]
    r0 = R_ref[:-1,:,:] @ r0[:,:,None] + v_ref[:-1,:,None]

    return n.reshape(-1,3), r0.reshape(-1,3), phi, l


def computeRHA(R_ref, v_ref, R_tar, v_tar):
    """
    Computes the relational helical axes from a list of reference transformations
    to target transformations.

    Returns four np.arrays with one element per time step:
      - n: normal vector (direction) of helical axis
      - r0: helical axis support vector closest to origin
      - phi: rotation around axis in [0,pi]
      - l: displacement length along axis (can be negative)
    """
    # result arrays containing every timestep
    n =   np.zeros(v_tar.shape)
    r0 =  np.zeros(v_tar.shape)
    phi = np.zeros(v_tar.shape[0])
    l =   np.zeros(v_tar.shape[0])

    for i in range(v_tar.shape[0]):
        # rotation/translation from reference to target
        R = R_tar[i] @ R_ref[i].T
        v = v_tar[i] - (R @ v_ref[i])

        # calculate this timestep
        n[i], r0[i], phi[i], l[i] = matrixVectorToHA(R, v)

    return n, r0, phi, l


def matrixVectorToHA(R, v):
    """
    Computes a single helical axis that describes the screwing
    of the rotation/translation given by R,v.
    """
    # sine, cosine of rotation angle
    sin_phi = 0.5 * np.sqrt((R[2,1]-R[1,2])**2 + (R[0,2]-R[2,0])**2 + (R[1,0]-R[0,1])**2)
    cos_phi = 0.5 * (np.trace(R) - 1)
    #sin_phi = 0.5 * np.sqrt((3-np.trace(R))*(1+np.trace(R))) # same error as cos_phi

    # use sine approximation, if sinphi <= (1/2)*sqrt(2), else use cosphi
    phi = 0.0
    if sin_phi <= 0.5*np.sqrt(2.0):
        phi = np.arcsin(sin_phi)
        if cos_phi < 0:
            phi = np.pi - phi
        cos_phi = np.cos(phi) # re-compute for numerical precision
    else:
        phi = np.arccos(cos_phi)
        sin_phi = np.sin(phi) # re-compute for numerical precision

    # helical axis
    nbar = (R - R.T) / (2*sin_phi)
    n = np.array([nbar[2,1], nbar[0,2], nbar[1,0]])

    # absolute translation along axis
    l = np.dot(n,v)

    # axis support vector
    n_cross_v = np.cross(n,v)
    r0 = -0.5*np.cross(n, n_cross_v) + sin_phi / (2.0*(1.0-cos_phi)) * n_cross_v

    return n, r0, phi, l
