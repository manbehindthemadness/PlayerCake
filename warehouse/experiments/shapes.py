import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy.random as rnd
import numpy as np


def arc_patch(xy, width, height, theta1=0., theta2=180., resolution=50, **kwargs):

    # generate the points
    theta = np.linspace(np.radians(theta1), np.radians(theta2), resolution)
    points = np.vstack((width*np.cos(theta) + xy[0],
                        height*np.sin(theta) + xy[1]))
    # build the polygon and add it to the axes
    poly = mpatches.Polygon(points.T, closed=False, **kwargs)

    return poly
#
# NUM = 1
# arcs = []
# for i in range(NUM):
#     r = rnd.rand()*360.
#     arcs.append(arc_patch(xy=rnd.rand(2)*10, width=1.,
#                 height=1., theta1=r, theta2=r+180.))
#
# # axis settings
fig, ax = plt.subplots(1, 1)
# for a in arcs:
#     ax.add_artist(a)
#     a.set_clip_box(ax.bbox)
#     a.set_alpha(0.5)
#     a.set_facecolor(rnd.rand(3))

ax.set_xlim(0, 10)
ax.set_ylim(0, 10)

a = arc_patch(xy=np.array((5, 5)), width=1., height=1., theta1=0, theta2=90.)  # This is our guy right here
ax.add_artist(a)

b = arc_patch(xy=np.array((5, 5)), width=1., height=1., theta1=90, theta2=180.)  # This is our guy right here
ax.add_artist(b)

c = arc_patch(xy=np.array((5, 5)), width=2., height=1., theta1=180, theta2=270.)  # This is our guy right here
ax.add_artist(c)

d = arc_patch(xy=np.array((5, 5)), width=1., height=2., theta1=270, theta2=360.)  # This is our guy right here
ax.add_artist(a)

plt.show()


