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
from warehouse.utils import to_color
import matplotlib.pyplot as plt
import matplotlib.path as mpath
import matplotlib.patches as mpatches
from matplotlib import animation, rc, cm
from IPython.display import HTML
from scipy.interpolate import splprep, splev, splrep
# from scipy.optimize import curve_fit, minimize_scalar
from mpl_toolkits import mplot3d
from itertools import product


hold = mplot3d


def d_spline():
    """
    lets try some 3d action...
    """
    def mesh_sorter(mesh):
        """
        Try to sort all these vertices...

        TODO: Remember this is for visual reprensentation ONLY!! We can add the extra vertex to the real loop.***
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

            def find_weights(trajectory):
                """
                This is a simple tool to locate the weighting anchor points of a given trajectory.

                TODO: In order to make this accurate we are going to have to calculate the diffs in relation to the grid boundaries...
                NOTE: To do the above we are going to have to dynamically evaluate the xyzlim values.

                :param trajectory: spline mesh array: (np.line_x, np.line_y)...
                :type trajectory: tuple
                :rtype: dict
                """
                tr = list(zip(*trajectory))
                diffa = list()
                diffb = list()
                for axis1, axis2 in tr:
                    # diff.append(abs(axis1 - axis2))
                    diffa.append(
                        sum(
                            [
                                abs(axis1 - -100) * -1,  # TODO: the 100/-100 value here will need to be dynamic...
                                abs(axis2 - -100)
                            ]
                        )
                    )
                    diffb.append(
                        sum(
                            [
                                abs(axis1 - -100),
                                abs(axis2 - -100)
                            ]
                        )
                    )

                minimum = diffa.index(max(diffa))
                maximum = diffb.index(max(diffb))
                result = (maximum, minimum)
                return result

            def find_implied_weights(trajectory):
                """
                This simple tool allows us to locate the implied weights (where the trajectory meets the ground).
                Note that this is estimated based on the resolution of the curve.
                """

                tr = list(zip(*trajectory))
                diffa = list()
                diffb = list()
                for axis1, axis2 in tr:
                    diffa.append(
                        abs(axis1 - -100) * -1 / axis2
                    )
                    diffb.append(
                        abs(axis1 - 100) / axis2
                    )
                maximum = diffa.index(max(diffa))
                minimum = diffb.index(min(diffb))
                result = (maximum, minimum)
                return result

            def process_weights(trajectory, weights, implied_weights):
                """
                Here we will attempt to calculate the various speeds we will have to use for each segment in the trajectory.

                Note: We have to process this per-axis set and then render the movements in x, y, z
                NOTE: For the coloring we will need xz, yz, xy, and xyz to get the movement correct on each diagram.
                        We can simply do this be adding the axes and taking an avarage.

                TODO: Don't forget these outputs are for coloring the diagram, the actual values are going to have to be measured in amount less than max velocity.*


                NOTE: ORDERING - I-MIN, I_MAX, MAX, MIN

                trajectory = [x], [y], [z]
                weights = [[xz_max],[xz_min]], [[yz_max], [yz_min]]
                implied_weights = ↑
                """
                def between(value, limits):
                    """
                    This tells us when a value is inbetween two limits.

                    :param value: the value to check.
                    :type value: int float
                    :param limits: Tuple of min and max limits.
                    :type limits: tuple
                    :rtype: bool
                    """
                    if limits[1] >= value > limits[0]:
                        return True
                    else:
                        return False

                def index_in_segment(index, min_pos):
                    """
                    This will tell us where we are in a segment.
                    """
                    result = index - min_pos
                    return result

                def solver(index_in_seg, current_speed, target_weight, target_weight_index, max_speed):
                    """
                    This solves a velocity based on out position, speed and the next weight value.
                    """
                    # position = target_weight_index - abs(index_in_seg - target_weight_index)  # Find how many steps before we hit the target weight.
                    position = abs(index_in_seg - target_weight_index)
                    div = abs(current_speed - target_weight)  # Find the difference between current and target speed.
                    if current_speed > target_weight:  # Discover if move is accel or decel.
                        div = div * -1
                    speed_increment = div / position  # See how many increments its going to take to get to target speed from current.
                    next_speed = current_speed + (index_in_seg * speed_increment)
                    if next_speed > max_speed:  # Clamp.
                        next_speed = max_speed
                    # print('index in seg', index_in_seg, 'position', position, 'divided', div, 'current_speed', current_speed, 'next_speed', next_speed, 'target_weight', target_weight, 'target_index', target_weight_index, 'speed_increment', speed_increment)
                    # next_speed = next_speed * -1  # Reverse output to match colors.
                    return next_speed

                # print(weights[1])
                # print(implied_weights[1])
                velocity = 10  # TODO: This is going to have to be a dynamic value in the future.
                movement_max = 100  # TODO: Dont's forget that this measurement is a percentage.
                colors = to_color(10, 100)

                # Define weighting values.
                xz_max_weight = 60
                xz_min_weight = 90

                yz_max_weight = 50
                yz_min_weight = 100

                tlen = len(trajectory[0])
                xz_max, xz_min = weights[0]  # Gather indexes.
                yz_max, yz_min = weights[1]
                ixz_max, ixz_min = implied_weights[0]
                iyz_max, iyz_min = implied_weights[1]

                ixz_seg_len = abs(ixz_min - ixz_max)  # Gather lengths.
                xz_total = ixz_seg_len
                iyz_seg_len = abs(iyz_min - iyz_max)
                yz_total = iyz_seg_len

                xz_seg1_len = abs(ixz_seg_len - xz_max)
                xz_total += xz_seg1_len
                yz_seg1_len = abs(yz_total - yz_max)
                yz_total += yz_seg1_len

                xz_seg2_len = abs(xz_seg1_len - xz_min)
                xz_total += xz_seg2_len
                yz_seg2_len = abs(yz_total - yz_min)
                yz_total += yz_seg2_len

                xz_seg3_len = abs(xz_total - tlen)
                yz_seg3_len = abs(yz_total - tlen)
                # print(tlen, iyz_seg_len, yz_seg1_len, yz_seg2_len, yz_seg3_len)
                # print('iyzmin', iyz_min, 'iyzmax', iyz_max, 'yzmax', yz_max, 'yz_min', yz_min)
                # print(iyz_seg_len, yz_seg1_len, yz_seg2_len, yz_seg3_len)

                # Now we solve the velocities.

                speeds_xz = list()
                colors_xz = list()
                speeds_yz = list()
                colors_yz = list()
                speeds_xyz = list()
                colors_xyz = list()

                speed = velocity
                for step in range(0, tlen):
                    # if between(step, (ixz_min, ixz_max)):  # Solve xz implied segment.
                    #     speeds_xz.append(velocity)
                    #
                    # elif between(step, (ixz_max, xz_max)):  # Solve xz segment 1.
                    #     seg_pos = index_in_segment(step, xz_max)  # Find position in segment.
                    #     speed = solver(seg_pos, speed, xz_max_weight, xz_max, movement_max)  # Solve speed for step.
                    #
                    # elif between(step, (xz_min, xz_max)):  # Solve xz segment 2.
                    #     seg_pos = index_in_segment(step, xz_min)  # Find position in segment.
                    #     speed = solver(seg_pos, speed, xz_min_weight, xz_min, movement_max)  # Solve speed for step.
                    #
                    # elif between(step, (xz_min, ixz_min)):  # Solve xz segment 3.
                    #     seg_pos = index_in_segment(step, ixz_min) # Find position in segment.
                    #     speed = solver(seg_pos, speed, velocity, ixz_min, movement_max)  # Solve speed for step.
                    # speeds_xz.append(speed)

                    if between(step, (iyz_min, iyz_max)):  # Solve yz implied segment.
                        # print('Iseg', step)
                        speed = velocity
                        speeds_xz.append(speed)

                    elif between(step, (iyz_max, yz_max)):  # Solve yz segment 1.
                        # print('seg1', step)
                        seg_pos = index_in_segment(step, iyz_max)  # Find position in segment.
                        speed = solver(seg_pos, speed, yz_max_weight, yz_max, movement_max)  # Solve speed for step.

                    elif between(step, (yz_max, yz_min)):  # Solve yz segment 2.
                        # print('seg2', step)
                        seg_pos = index_in_segment(step, yz_max)  # Find position in segment.
                        speed = solver(seg_pos, speed, yz_min_weight, yz_min, movement_max)  # Solve speed for step.

                    elif between(step, (yz_min, tlen)):  # Solve yz segment 3.
                        # print('seg3', step)
                        seg_pos = index_in_segment(step, yz_min)  # Find position in segment.
                        speed = solver(seg_pos, speed, velocity, iyz_min, movement_max)  # Solve speed for step.
                    colors_yz.append(colors[int(speed)])
                    speeds_yz.append(speed)  # Convert speed to HSV color.
                return speeds_xz, speeds_yz, speeds_xyz, colors_xz, colors_yz, colors_xyz


            # ===============
            #  First subplot
            # ===============
            fig = plt.figure(figsize=plt.figaspect(0.9))

            scattersize = 10  # This is the size of our color points.

            ax = fig.add_subplot(2, 2, 1, projection='3d')
            ax.title.set_text('3D')
            ax.set_xlabel('(front) x')
            ax.set_ylabel('y')
            ax.set_zlabel('z')
            ax.set_xlim(-100, 100)  # TODO: These will need to be set to leg_len*2 in the future.
            ax.set_ylim(-100, 100)
            ax.set_zlim(-100, 100)

            mesh = pymesh.load_mesh('warehouse/experiments/simplecurve.obj')

            cv = mesh_sorter(mesh.vertices)

            z_line = list()
            x_line = list()
            y_line = list()
            for x, y, z in cv:  # TODO: Prolly should use zip here...
                z_line.append(z)
                x_line.append(x)
                y_line.append(y)

            if z_line[1] > 0:  # TODO: We have to transform the order into a counter-clockwise sequence.
                z_line.reverse()
                x_line.reverse()
                y_line.reverse()

            weight_len = len(z_line)
            wyz = find_weights((y_line, z_line))
            # print('static weights, max/min', wyz)
            iyz = find_implied_weights((y_line, z_line))
            wxz = find_weights((x_line, z_line))
            ixz = find_implied_weights((x_line, z_line))

            speeds = process_weights(
                [
                    x_line,
                    y_line,
                    z_line
                ],
                [
                    wxz, wyz
                ],
                [
                    ixz, iyz
                ]
            )

            # print(speeds[1])
            # print(speeds[4])
            xz_speeds = speeds[0]
            yz_speeds = speeds[1]
            yz_colors = speeds[4]
            xyz_speeds = speeds[2]

            z_line = np.array(z_line)
            x_line = np.array(x_line)
            y_line = np.array(y_line)

            weight = list()
            for ct, it in enumerate(range(0, weight_len)):
                weight.append(ct)

            # TODO: Remember all the earth and reference measurements are going to need to be based on leg length and range of motion.
            ax.plot3D(x_line, y_line, z_line, color='grey', label='trajectory')  # Plot trajectory.
            implied_line_x = (
                [
                    x_line[ixz[0]],
                    x_line[ixz[1]],
                ],
                [
                    y_line[ixz[0]],
                    y_line[ixz[1]],
                ],
                [
                    z_line[ixz[0]],
                    z_line[ixz[1]],
                ],
            )
            ax.plot3D(*implied_line_x, color='pink')  # Print Implied line.
            implied_line_y = (
                [
                    x_line[iyz[0]],
                    x_line[iyz[1]],
                ],
                [
                    y_line[iyz[0]],
                    y_line[iyz[1]],
                ],
                [
                    z_line[iyz[0]],
                    z_line[iyz[1]],
                ],
            )
            ax.plot3D(*implied_line_y, color='pink')  # Print Implied line.
            ax.scatter3D(x_line, y_line, z_line, c=weight, cmap='hsv', s=scattersize)
            ax.plot3D([-100, -100, 100, 100, -100], [100, -100, -100, 100, 100], [0, 0, 0, 0, 0], label='surface')  # Plot ground.
            ax.plot3D([0, 0, 0], [0, 0, 0], [0, -50, 0], color='orange', label='start')  # Plot start point.
            ax.scatter3D([0], [0], [100], color="grey", s=10, label='pivot')  # Plot leg pivot.

            # ax.scatter3D(weightsxz[0][0], weightsxz[0][1], z_line[weightsxz[2][0]], edgecolors='green', facecolors='none', label='mxweightxz',
            #              s=100)  # Plot max weight xz.
            # ax.scatter3D(weightsxz[1][0], weightsxz[1][1], z_line[weightsxz[2][1]], edgecolors='black', facecolors='none', label='mnweightxz',
            #              s=100)  # Plot min weight xz.
            # ax.scatter3D(weightsyz[0][0], weightsyz[0][1], z_line[weightsyz[2][0]],edgecolors='red', facecolors='none', label='mxweightyz',
            #              s=100)  # Plot max weight yz.
            # ax.scatter3D(weightsyz[1][0], weightsyz[1][1], z_line[weightsyz[2][1]], edgecolors='blue', facecolors='none', label='mnweightyz',
            #              s=100)  # Plot min weight yz.

            # ===============
            # Second subplot x z
            # ===============
            ax = fig.add_subplot(2, 2, 2)
            ax.plot(x_line, z_line, color='grey', label='trajectory')  # Plot trajectory.
            ax.plot([-100, 100], [0, 0], label='surface')  # Plot ground
            ax.plot([0, 0], [-100, -50], color='orange', label='surface')  # Plot start.
            ax.scatter(0, 100, color='grey', label='pivot', s=100)  # Plot leg pivot.

            ax.scatter(x_line[wxz[0]], z_line[wxz[0]], edgecolors='green', facecolors='none', label='mxweight',
                       s=100)  # Plot max weight.
            ax.scatter(x_line[wxz[1]], z_line[wxz[1]], edgecolors='orange', facecolors='none', label='mnweight',
                       s=100)  # Plot min weight.
            ax.scatter(x_line[ixz[0]], z_line[ixz[0]], edgecolors='pink', facecolors='none', label='mxweight',
                       s=100)  # Plot max implied weight.
            ax.scatter(x_line[ixz[1]], z_line[ixz[1]], edgecolors='pink', facecolors='none', label='mnweight',
                       s=100)  # Plot min implied weight.

            anchor = plot_angle((0, 100), -30)
            plt.text(anchor[0], anchor[1], '. ' * 7 + 'minx', fontsize=8, rotation=anchor[2], rotation_mode='anchor', verticalalignment='center')  # Plot min.
            anchor = plot_angle((0, 100), 80)
            plt.text(anchor[0], anchor[1], '. ' * 7 + 'maxx', fontsize=8, rotation=anchor[2], rotation_mode='anchor', verticalalignment='center')  # Plot max.
            ax.add_artist(plt.Circle((0, 100), 50, fill=False, linestyle=':', color='gray'))  # Plot zmin.
            ax.annotate("minz", xy=(-12, 55), fontsize=7)
            ax.add_artist(plt.Circle((0, 100), 150, fill=False, linestyle=':', color='gray'))  # Plot zmax.
            ax.annotate("maxz", xy=(65, -50), fontsize=7)  # Plot zmax.
            ax.annotate("gnd", xy=(-99, 8), fontsize=7)
            ax.annotate("start", xy=(1, -94), fontsize=7)

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

            ax.scatter(y_line[wyz[0]], z_line[wyz[0]], edgecolors='magenta', facecolors='none', label='mxweight', s=100)  # Plot max weight.
            ax.scatter(y_line[wyz[1]], z_line[wyz[1]], edgecolors='cyan', facecolors='none', label='mnweight', s=100)  # Plot min weight.
            ax.scatter(y_line[iyz[0]], z_line[iyz[0]], edgecolors='pink', facecolors='none', label='mxweight',
                       s=100)  # Plot max implied weight.
            ax.scatter(y_line[iyz[1]], z_line[iyz[1]], edgecolors='pink', facecolors='none', label='mnweight',
                       s=100)  # Plot min implied weight.

            # yy, zz = np.meshgrid(y_line, z_line)
            # print(list(zip(yy, zz)))
            # ax.plot(yy, zz, color='grey', label='trajectory')  # experiment.


            anchor = plot_angle((0, 100), -45)
            plt.text(anchor[0], anchor[1], '. ' * 7 + 'maxy', fontsize=7, rotation=anchor[2],
                     rotation_mode='anchor', verticalalignment='center')  # Plot max.
            anchor = plot_angle((0, 100), 45)
            plt.text(anchor[0], anchor[1], '. ' * 7 + 'miny', fontsize=7, rotation=anchor[2],
                     rotation_mode='anchor', verticalalignment='center')  # Plot min.
            ax.add_artist(plt.Circle((0, 100), 50, fill=False, linestyle=':', color='gray'))  # Plot zmin.
            ax.annotate("minz", xy=(-12, 55), fontsize=7)
            ax.add_artist(plt.Circle((0, 100), 150, fill=False, linestyle=':', color='gray'))  # Plot zmax.
            ax.annotate("maxz", xy=(65, -50), fontsize=7)
            ax.annotate("gnd", xy=(-99, 8), fontsize=7)
            ax.annotate("start", xy=(1, -94), fontsize=7)
            ax.set_xlim(-100, 100)  # TODO: These will need to be set to leg_len*2 in the future.
            ax.set_ylim(-100, 100)
            ax.title.set_text('Side')
            ax.set_xlabel('y')
            ax.set_ylabel('(front) z')
            ax.scatter(y_line, z_line, c=yz_colors, cmap='hsv', s=scattersize)
            # ===============
            # Fourth subplot x y
            # ===============
            ax = fig.add_subplot(2, 2, 4)
            ax.plot(implied_line_x[0], implied_line_x[1], color='pink')  # Plot implied line.
            ax.plot(implied_line_y[0], implied_line_y[1], color='pink')  # plot implied line.
            ax.plot(x_line, y_line, color='grey', label='trajectory')  # Plot trajectory.
            # ax.plot([-100, 100], [0, 0], label='surface')  # Plot ground
            ax.plot([-100, -50], [0, 0], color='orange', label='surface')  # Plot start.
            # ax.scatter(0, 0, color='grey', label='pivot', s=1)  # Plot leg pivot.
            ax.set_xlim(-100, 100)  # TODO: These will need to be set to leg_len*2 in the future.
            ax.set_ylim(-100, 100)
            ax.title.set_text('Top')
            ax.set_xlabel('(front) x')
            ax.set_ylabel('y')
            ax.scatter(x_line, y_line, c=weight, cmap='hsv', s=scattersize)
            ax.annotate("start", xy=(-99, 8), fontsize=7)

            ax.scatter(x_line[wxz[0]], y_line[wxz[0]], edgecolors='green', facecolors='none', label='mxweight',
                       s=100)  # Plot max weight.
            ax.scatter(x_line[wxz[1]], y_line[wxz[1]], edgecolors='orange', facecolors='none', label='mnweight',
                       s=100)  # Plot min weight.
            ax.scatter(x_line[wyz[0]], y_line[wyz[0]], edgecolors='magenta', facecolors='none', label='mxweight',
                       s=100)  # Plot max weight.
            ax.scatter(x_line[wyz[1]], y_line[wyz[1]], edgecolors='cyan', facecolors='none', label='mnweight',
                       s=100)  # Plot min weight.

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
