"""
Experiment
"""
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import proj3d
from mpl_toolkits.mplot3d.axes3d import Axes3D

# Make sure these are floating point values:
scale_x = 1.0
scale_y = 2.0
scale_z = 3.0

# Axes are scaled down to fit in scene
max_scale = max(scale_x, scale_y, scale_z)

scale_x = scale_x / max_scale
scale_y = scale_y / max_scale
scale_z = scale_z / max_scale

# Create scaling matrix
scale = np.array([[scale_x, 0, 0, 0],
                  [0, scale_y, 0, 0],
                  [0, 0, scale_z, 0],
                  [0, 0, 0, 1]])


def get_proj_scale(self):
    """                                                                                                                                                                                                                                    
    Create the projection matrix from the current viewing position.                                                                                                                                                                        

    elev stores the elevation angle in the z plane                                                                                                                                                                                         
    azim stores the azimuth angle in the x,y plane                                                                                                                                                                                         

    dist is the distance of the eye viewing point from the object                                                                                                                                                                          
    point.                                                                                                                                                                                                                                 

    """
    relev, razim = np.pi * self.elev / 180, np.pi * self.azim / 180

    xmin, xmax = self.get_xlim3d()
    ymin, ymax = self.get_ylim3d()
    zmin, zmax = self.get_zlim3d()

    # transform to uniform world coordinates 0-1.0,0-1.0,0-1.0                                                                                                                                                                             
    worldM = proj3d.world_transformation(
        xmin, xmax,
        ymin, ymax,
        zmin, zmax)

    # look into the middle of the new coordinates                                                                                                                                                                                          
    R = np.array([0.5, 0.5, 0.5])

    xp = R[0] + np.cos(razim) * np.cos(relev) * self.dist
    yp = R[1] + np.sin(razim) * np.cos(relev) * self.dist
    zp = R[2] + np.sin(relev) * self.dist
    E = np.array((xp, yp, zp))

    self.eye = E
    self.vvec = R - E
    self.vvec = self.vvec / proj3d.mod(self.vvec)

    if abs(relev) > np.pi / 2:
        # upside down
        V = np.array((0, 0, -1))
    else:
        V = np.array((0, 0, 1))
    zfront, zback = -self.dist, self.dist

    viewM = proj3d.view_transformation(E, R, V)
    perspM = proj3d.persp_transformation(zfront, zback)
    M0 = np.dot(viewM, worldM)
    M = np.dot(perspM, M0)

    return np.dot(M, scale)


Axes3D.get_proj = get_proj_scale

"""
You need to include all the code above.
From here on you should be able to plot as usual.
"""

mpl.rcParams['legend.fontsize'] = 10

fig = plt.figure(figsize=(5, 5))
ax = fig.gca(projection='3d')
theta = np.linspace(-4 * np.pi, 4 * np.pi, 100)
z = np.linspace(-2, 2, 100)
r = z ** 2 + 1
x = r * np.sin(theta)
y = r * np.cos(theta)
ax.plot(x, y, z, label='parametric curve')
ax.legend()

plt.show()
