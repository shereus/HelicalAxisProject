# -----------------------------------------------------------------------------
# Copyright (c) 2021 Pepe Eulzer. All rights reserved.
# Distributed under the (new) BSD License.
# -----------------------------------------------------------------------------

from PyQt5.QtGui import QMatrix4x4, QVector3D, QQuaternion

class TrackballCamera():
    """
    Maintains view and projection matrices of a trackball camera.
    """
    def __init__(self, w, h, near=0.01, far=50.0, fov=45.0):
        self.__view_needs_update = True        # does the view matrix need to be updated?
        self.center = QVector3D(0.0, 0.0, 0.0) # focus point of camera
        self.pos = QVector3D(1.0, 0.0, 0.0)    # position of camera

        # normalized camera axes and radius
        self.up = QVector3D(0.0, 0.0, 1.0)
        look = self.center - self.pos
        self.radius = look.length()
        self.front = QVector3D.normalized(look)
        self.right = QVector3D.normalized(QVector3D.crossProduct(self.front, self.up))

        # setup initial view and projection matrices
        self.view = QMatrix4x4()
        self.projection = QMatrix4x4()
        self.projection.perspective(fov, w / float(h), near, far)
    
    def rotate(self, d_horizontal, d_vertical):
        v = QQuaternion.fromAxisAndAngle(self.right, -d_vertical)
        h = QQuaternion.fromAxisAndAngle(self.up, -d_horizontal)
        q = h * v
        self.front = q.rotatedVector(self.front)
        self.right = q.rotatedVector(self.right)
        self.up = QVector3D.crossProduct(self.right, self.front)
        self.pos = self.center - self.front * self.radius
        self.__view_needs_update = True

    def zoom(self, distance):
        if distance < self.radius:
            self.pos += self.front * distance
            self.radius = (self.center - self.pos).length()
            self.__view_needs_update = True

    def pan(self, dx, dy):
        move = -dx * self.right + dy * self.up
        self.center += move
        self.pos += move
        self.__view_needs_update = True

    def getView(self):
        if self.__view_needs_update:
            self.view.setToIdentity()
            self.view.lookAt(self.pos, self.center, self.up)
            self.__view_needs_update = False
        return self.view

    def getProjection(self):
        return self.projection

    def getPosition(self):
        return [self.pos.x(), self.pos.y(), self.pos.z()]

    def setProjection(self, w, h, near=0.01, far=50.0, fov=45.0):
        self.projection.setToIdentity()
        self.projection.perspective(fov, w / float(h), near, far)