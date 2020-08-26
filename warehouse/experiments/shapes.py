"""
Just a place to toy with matplotlib.

interesting info here: http://paulbourke.net/geometry/circlesphere/

more: https://stackoverflow.com/questions/31464345/fitting-a-closed-curve-to-a-set-of-points

spline with color: https://stackoverflow.com/questions/28279060/splines-with-python-using-control-knots-and-endpoints
pymesh to graph: https://github.com/PyMesh/PyMesh/issues/155
3D subplots!!!: https://matplotlib.org/3.1.1/gallery/mplot3d/subplot3d.html

for pymesh: sudo apt-get install libgmp-dev libmpfr-dev libboost-dev cmake swig
"""
import pymesh
import pprint
from stl import mesh as mmesh
import numpy as np
import math
import matplotlib.pyplot as plt
import matplotlib.path as mpath
import matplotlib.patches as mpatches
from matplotlib import animation, rc, cm
from IPython.display import HTML
from scipy.interpolate import splprep, splev, splrep
from mpl_toolkits import mplot3d


hold = mplot3d


def d_spline():
    """
    lets try some 3d action...
    """
    def mesh_sorter(mesh):
        """
        Try to sort all these vertices...
        """
        mesh = mesh.tolist()
        mesh.append(mesh[0])

        return mesh

    def show_3d_spline():
        """
        This plots a 3d spline.

        NOTE: THis is the logic we are going to wind up using.
        """

        def stl_mesh():
            """
            Method using numpy-stl

            TODO: This fucker here works for full-mesh rendering.
            """
            fig = plt.figure()
            ax = plt.axes(projection="3d")
            tmesh = mmesh.Mesh.from_file('warehouse/experiments/simplecurve.STL')
            ax.add_collection3d(mplot3d.art3d.Line3DCollection(tmesh.vectors))
            # ax.add_collection3d(mplot3d.art3d.Poly3DCollection(tmesh.vectors))
            scale = tmesh.points.flatten('C')
            ax.auto_scale_xyz(scale, scale, scale)
            plt.show()

        def pymesh_stl():
            """
            Method using pymesh.

            TODO: This fucker right here works for line tracing.
            """

            def plot_angle(start, rotation):
                """
                plots a text angle from the starting anchor by degrees.
                """
                rotation -= 90
                start = np.array(start)
                trans_angle = plt.gca().transData.transform_angles(
                    np.array((rotation,)),
                    start.reshape((1, 2))
                )[0]
                return start[0], start[1], trans_angle


            # ===============
            #  First subplot
            # ===============
            # fig = plt.figure()
            # set up a figure twice as wide as it is tall
            # fig = plt.figure(figsize=plt.figaspect(0.5))
            # Set up figure for a 4 way split
            fig = plt.figure(figsize=plt.figaspect(0.9))

            scattersize = 10  # This is the size of our color points.
            # ax = plt.axes(projection="3d")

            ax = fig.add_subplot(2, 2, 1, projection='3d')
            ax.title.set_text('3D')
            ax.set_xlabel('x')
            ax.set_ylabel('y')
            ax.set_zlabel('z')
            # ax.set_xticks(np.arange(0, 100, 20))
            # ax.set_yticks(np.arange(0, 100, 20))
            # ax.set_zticks(np.arange(0, 100, 20))
            ax.set_xlim(-100, 100)  # TODO: These will need to be set to leg_len*2 in the future.
            ax.set_ylim(-100, 100)
            ax.set_zlim(-100, 100)

            mesh = pymesh.load_mesh('warehouse/experiments/simplecurve.obj')
            # mesh = pymesh.wires.WireNetwork.create_from_file('warehouse/experiments/simplecurve.obj')
            # Bscale = mesh.points.flatten('C')
            # ax.auto_scale_xyz(1, 1, 1)

            cv = mesh_sorter(mesh.vertices)
            # cv = mesh.vertices

            z_line = list()
            # z_names = list()
            x_line = list()
            # x_names = list()
            y_line = list()
            # y_names = list()
            # pprint.PrettyPrinter(indent=4).pprint(cv)
            for x, y, z in cv:  # TODO: Prolly should use zip here...
                z_line.append(z)
                # z_names.append('z' + str(z))
                x_line.append(x)
                # x_names.append('x' + str(x))
                y_line.append(y)
                # y_names.append('y' + str(y))
            weight_len = len(z_line)
            z_line = np.array(z_line)
            x_line = np.array(x_line)
            y_line = np.array(y_line)
            # print(z_line, x_line, y_line)
            weight = list()
            for ct, it in enumerate(range(0, weight_len)):
                weight.append(ct)
            # ax.set_xticklabels(x_names)
            # ax.set_yticklabels(y_names)
            # ax.set_zticklabels(z_names)
            # TODO: Remember all the earth and reference measurements are going to need to be based on leg length and range of motion.
            ax.plot3D(x_line, y_line, z_line, color='grey', label='trajectory')  # Plot trajectory.
            ax.scatter3D(x_line, y_line, z_line, c=weight, cmap='hsv', s=scattersize)
            ax.plot3D([-100, -100, 100, 100, -100], [100, -100, -100, 100, 100], [0, 0, 0, 0, 0], label='surface')  # Plot ground.
            ax.plot3D([0, 0, 0], [0, 0, 0], [0, -50, 0], color='orange', label='start')  # Plot start point.
            ax.scatter3D([0], [0], [100], color="grey", s=10, label='pivot')  # Plot leg pivot.
            # ===============
            # Second subplot x z
            # ===============
            ax = fig.add_subplot(2, 2, 2)
            ax.plot(x_line, z_line, color='grey', label='trajectory')  # Plot trajectory.
            ax.plot([-100, 100], [0, 0], label='surface')  # Plot ground
            ax.plot([0, 0], [-100, -50], color='orange', label='surface')  # Plot start.
            ax.scatter(0, 100, color='grey', label='pivot', s=100)  # Plot leg pivot.

            anchor = plot_angle((0, 100), -30)
            plt.text(anchor[0], anchor[1], '. '*12, fontsize=8, rotation=anchor[2], rotation_mode='anchor')  # Plot min.
            anchor = plot_angle((0, 100), 80)
            plt.text(anchor[0], anchor[1], '. ' * 12, fontsize=8, rotation=anchor[2], rotation_mode='anchor')  # Plot max.
            ax.add_artist(plt.Circle((0, 100), 50, fill=False, linestyle=':', color='gray'))  # Plot zmin.

            # print(limit)
            # ax.plot(*limit, color='grey', label='limit_min')

            ax.set_xlim(-100, 100)  # TODO: These will need to be set to leg_len*2 in the future.
            ax.set_ylim(-100, 100)
            ax.title.set_text('Front')
            ax.set_xlabel('x')
            ax.set_ylabel('z')
            ax.scatter(x_line, z_line, c=weight, cmap='hsv', s=scattersize)
            # ===============
            # Third subplot y z
            # ===============
            ax = fig.add_subplot(2, 2, 3)
            ax.plot(y_line, z_line, color='grey', label='trajectory')  # Plot trajectory.
            ax.plot([-100, 100], [0, 0], label='surface')  # Plot ground
            ax.plot([0, 0], [-100, -50], color='orange', label='surface')  # Plot start.
            ax.scatter(0, 100, color='grey', label='pivot', s=100)  # Plot leg pivot.

            anchor = plot_angle((0, 100), -45)
            plt.text(anchor[0], anchor[1], '. ' * 12, fontsize=8, rotation=anchor[2],
                     rotation_mode='anchor')  # Plot min.
            anchor = plot_angle((0, 100), 45)
            plt.text(anchor[0], anchor[1], '. ' * 12, fontsize=8, rotation=anchor[2],
                     rotation_mode='anchor')  # Plot max.
            ax.add_artist(plt.Circle((0, 100), 50, fill=False, linestyle=':', color='gray'))  # Plot zmin.

            ax.set_xlim(-100, 100)  # TODO: These will need to be set to leg_len*2 in the future.
            ax.set_ylim(-100, 100)
            ax.title.set_text('Side')
            ax.set_xlabel('y')
            ax.set_ylabel('z')
            ax.scatter(y_line, z_line, c=weight, cmap='hsv', s=scattersize)
            # ===============
            # Fourth subplot x y
            # ===============
            ax = fig.add_subplot(2, 2, 4)
            ax.plot(x_line, y_line, color='grey', label='trajectory')  # Plot trajectory.
            # ax.plot([-100, 100], [0, 0], label='surface')  # Plot ground
            ax.plot([-100, -50], [0, 0], color='orange', label='surface')  # Plot start.
            # ax.scatter(0, 0, color='grey', label='pivot', s=1)  # Plot leg pivot.
            ax.set_xlim(-100, 100)  # TODO: These will need to be set to leg_len*2 in the future.
            ax.set_ylim(-100, 100)
            ax.title.set_text('Top')
            ax.set_xlabel('x')
            ax.set_ylabel('y')
            ax.scatter(x_line, y_line, c=weight, cmap='hsv', s=scattersize)

            # plt.subplots_adjust(bottom=4, top=5, right=1, wspace=2, hspace=2)
            plt.subplots_adjust(left=0.1, right=0.9, bottom=0.1, top=0.9)
            plt.tight_layout()
            plt.show()

        pymesh_stl()

    # show_3d()
    show_3d_spline()


def bsp_spline():
    """
    Lets draw some bsp lines.
    """

    def bspline(_cv, n=100, degree=3):
        """ Calculate n samples on a bspline

            cv :      Array ov control vertices
            n  :      Number of samples to return
            degree:   Curve degree
        """
        _cv = np.asarray(_cv)
        count = _cv.shape[0]

        # Prevent degree from exceeding count-1, otherwise splev will crash
        degree = np.clip(degree, 1, count - 1)

        # Calculate knot vector
        kv = np.array([0] * degree + list(range(count - degree + 1)) + [count - degree] * degree, dtype='int')

        # Calculate query range
        u = np.linspace(0, (count - degree), n)

        # Calculate result
        return np.array(splev(u, (kv, _cv.T, degree))).T

    colors = ('b', 'g', 'r', 'c', 'm', 'y', 'k')

    cv = np.array([[50., 25.],
                   [59., 12.],
                   [50., 10.],
                   [57., 2.],
                   [40., 4.],
                   [40., 14.]])

    plt.plot(cv[:, 0], cv[:, 1], 'o-', label='Control Points')

    for d in range(1, 5):
        # noinspection PyArgumentEqualDefault
        p = bspline(cv, n=100, degree=d)
        x, y = p.T
        plt.plot(x, y, 'k-', label='Degree %s' % d, color=colors[d % len(colors)])

    plt.minorticks_on()
    plt.legend()
    plt.xlabel('x')
    plt.ylabel('y')
    plt.xlim(35, 70)
    plt.ylim(0, 30)
    plt.gca().set_aspect('equal', adjustable='box')
    plt.show()


# noinspection PyArgumentEqualDefault,PyArgumentEqualDefault
def points():
    """
    Lets draw points on a line.
    """
    pts = np.array([[6.55525, 3.05472],
                    [6.17284, 2.802609],
                    [5.53946, 2.649209],
                    [4.93053, 2.444444],
                    [4.32544, 2.318749],
                    [3.90982, 2.2875],
                    [3.51294, 2.221875],
                    [3.09107, 2.29375],
                    [2.64013, 2.4375],
                    [2.275444, 2.653124],
                    [2.137945, 3.26562],
                    [2.15982, 3.84375],
                    [2.20982, 4.31562],
                    [2.334704, 4.87873],
                    [2.314264, 5.5047],
                    [2.311709, 5.9135],
                    [2.29638, 6.42961],
                    [2.619374, 6.75021],
                    [3.32448, 6.66353],
                    [3.31582, 5.68866],
                    [3.35159, 5.17255],
                    [3.48482, 4.73125],
                    [3.70669, 4.51875],
                    [4.23639, 4.58968],
                    [4.39592, 4.94615],
                    [4.33527, 5.33862],
                    [3.95968, 5.61967],
                    [3.56366, 5.73976],
                    [3.78818, 6.55292],
                    [4.27712, 6.8283],
                    [4.89532, 6.78615],
                    [5.35334, 6.72433],
                    [5.71583, 6.54449],
                    [6.13452, 6.46019],
                    [6.54478, 6.26068],
                    [6.7873, 5.74615],
                    [6.64086, 5.25269],
                    [6.45649, 4.86206],
                    [6.41586, 4.46519],
                    [5.44711, 4.26519],
                    [5.04087, 4.10581],
                    [4.70013, 3.67405],
                    [4.83482, 3.4375],
                    [5.34086, 3.43394],
                    [5.76392, 3.55156],
                    [6.37056, 3.8778],
                    [6.53116, 3.47228]])
    # noinspection PyTupleAssignmentBalance
    tck, u = splprep(pts.T, u=None, s=0.0, per=1)
    u_new = np.linspace(u.min(), u.max(), 1000)
    x_new, y_new = splev(u_new, tck, der=0)

    plt.plot(pts[:, 0], pts[:, 1], 'ro')
    plt.plot(x_new, y_new, 'b--')
    plt.show()


def color_spline():
    """
    lets draw a spline with some colors...
    """
    # sampling
    x = np.linspace(0, 10, 10)
    y = np.sin(x)

    # spline trough all the sampled points
    tck = splrep(x, y)
    x2 = np.linspace(0, 10, 200)
    y2 = splev(x2, tck)

    # spline with all the middle points as knots (not working yet)
    # knots = x[1:-1]  # it should be something like this
    knots = np.array([x[1]])  # not working with above line and just seeing what this line does
    weights = np.concatenate(([1], np.ones(x.shape[0] - 2) * .01, [1]))
    tck = splrep(x, y, t=knots, w=weights)
    x3 = np.linspace(0, 10, 200)
    y3 = splev(x2, tck)

    # plot
    plt.plot(x, y, 'go', x2, y2, 'b', x3, y3, 'r')
    plt.show()


def spline():
    """
    Lets plot a curve...
    """
    Path = mpath.Path

    fig, ax = plt.subplots()
    pp1 = mpatches.PathPatch(
        # x, y start, <handle>, x, y end, <handle>
        Path([(0, 0.5), (0, 0), (0.5, 0), (0, 0)],
             [Path.MOVETO, Path.CURVE3, Path.CURVE3, Path.CLOSEPOLY]),
        fc="none", transform=ax.transData)
    pp2 = mpatches.PathPatch(
        # x, y start, <handle>, x, y end, <handle>
        Path([(0.5, 0), (0, 0), (0, 0.5), (0, 0)],
             [Path.MOVETO, Path.CURVE3, Path.CURVE3, Path.CLOSEPOLY]),
        fc="none", transform=ax.transData)
    ax.add_patch(pp1)
    ax.add_patch(pp2)
    # ax.plot([0.75], [0.25], "ro")
    ax.set_title('The red point should be on the path')

    plt.show()


def circles():
    """
    Draw some circles...
    """
    circle1 = plt.Circle((0, 0), 0.2, color='r')
    circle2 = plt.Circle((0.5, 0.5), 0.2, color='blue')
    circle3 = plt.Circle((1, 1), 0.2, color='g', clip_on=False)

    fig, ax = plt.subplots()  # note we must use plt.subplots, not plt.subplot
    # (or if you have an existing figure)
    # fig = plt.gcf()
    # ax = fig.gca()

    ax.add_artist(circle1)
    ax.add_artist(circle2)
    ax.add_artist(circle3)

    return fig


def circles2():
    """
    Show more circles...
    """
    fig = circles()
    circle1 = plt.Circle((0, 0), 2, color='r')
    # now make a circle with no fill, which is good for hi-lighting key results
    circle2 = plt.Circle((5, 5), 0.5, color='b', fill=False)
    circle3 = plt.Circle((10, 10), 2, color='g', clip_on=False)

    ax = plt.gca()
    ax.cla()  # clear things for fresh plot

    # change default range so that new circles will work
    ax.set_xlim((0, 10))
    ax.set_ylim((0, 10))
    # some data
    ax.plot(range(11), 'o', color='black')
    # key data point that we are encircling
    ax.plot(5, 5, 'o', color='y')

    ax.add_artist(circle1)
    ax.add_artist(circle2)
    ax.add_artist(circle3)
    fig.show()


def animation_test():
    """
    lets see something move...
    """
    # First set up the figure, the axis, and the plot element we want to animate
    fig, ax = plt.subplots()

    ax.set_xlim((0, 2))
    ax.set_ylim((-2, 2))

    line, = ax.plot([], [], lw=2)

    # initialization function: plot the background of each frame
    def init():
        """
        init
        """
        line.set_data([], [])
        return (line,)

    # animation function. This is called sequentially
    def animate(i):
        """
        animate
        """
        x = np.linspace(0, 2, 1000)
        y = np.sin(2 * np.pi * (x - 0.01 * i))
        line.set_data(x, y)
        return (line,)

    # call the animator. blit=True means only re-draw the parts that have changed.

    anim = animation.FuncAnimation(fig, animate, init_func=init, frames=100, interval=20, blit=True)

    # equivalent to rcParams['animation.html'] = 'html5'
    rc('animation', html='jshtml')
    # rc

    HTML(anim.to_jshtml())
