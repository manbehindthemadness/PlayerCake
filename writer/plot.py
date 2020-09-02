"""
Here we have our matplotlib code for the writer app.

TODO: NOTE: This is in example format and will need to be largely refactored.
"""
import pymesh
# import pprint
# from stl import mesh as mmesh
import numpy as np
# mport math
from warehouse.utils import to_color
import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# import matplotlib.path as mpath
# import matplotlib.patches as mpatches
# from matplotlib import animation, rc, cm
# from IPython.display import HTML
# from scipy.interpolate import splprep, splev, splrep
# # from scipy.optimize import curve_fit, minimize_scalar
from mpl_toolkits import mplot3d
# from itertools import product


def mesh_sorter(mesh):
    """
    Try to sort all these vertices...

    TODO: Remember this is for visual reprensentation ONLY!! We can add the extra vertex to the real loop.***
    """
    mesh = mesh.tolist()
    mesh.append(mesh[0])

    return mesh


def pymesh_stl(obj_file, parent):
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
            if position > 0:
                speed_increment = div / position  # See how many increments its going to take to get to target speed from current.
            else:
                speed_increment = div
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
        colors = to_color(0, 100)
        print(len(colors))

        # Define weighting values.
        xz_max_weight = 10
        xz_min_weight = 100

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

        # TODO: It looks like we might have a problem solving scenarios where the implied weights are in the same location...

        speedxz = speedyz = velocity
        for step in range(0, tlen):
            # SOLVE XZ
            if between(step, (ixz_min, ixz_max)):  # Solve xz implied segment.
                # print('Iseg', step)
                speedxz = velocity
                speeds_xz.append(speedxz)

            elif between(step, (ixz_max, xz_max)):  # Solve xz segment 1.
                # print('seg1', step)
                seg_pos = index_in_segment(step, ixz_max)  # Find position in segment.
                speedxz = solver(seg_pos, speedxz, xz_max_weight, xz_max, movement_max)  # Solve speed for step.

            elif between(step, (xz_max, xz_min)):  # Solve xz segment 2.
                # print('seg2', step)
                seg_pos = index_in_segment(step, xz_max)  # Find position in segment.
                speedxz = solver(seg_pos, speedxz, xz_min_weight, xz_min, movement_max)  # Solve speed for step.

            elif between(step, (xz_min, tlen)):  # Solve xz segment 3.
                # print('seg3', step)
                # seg_pos = index_in_segment(step, xz_min)  # Find position in segment.
                # speedxz = solver(seg_pos, speedxz, velocity, ixz_min, movement_max)  # Solve speed for step.
                speedxz = xz_min_weight

            colors_xz.append(colors[int(speedxz)])
            speeds_xz.append(speedxz)

            # SOLVE YZ
            if between(step, (iyz_min, iyz_max)):  # Solve yz implied segment.
                # print('Iseg', step)
                speedyz = velocity
                speeds_yz.append(speedyz)

            elif between(step, (iyz_max, yz_max)):  # Solve yz segment 1.
                # print('seg1', step)
                seg_pos = index_in_segment(step, iyz_max)  # Find position in segment.
                speedyz = solver(seg_pos, speedyz, yz_max_weight, yz_max, movement_max)  # Solve speed for step.

            elif between(step, (yz_max, yz_min)):  # Solve yz segment 2.
                # print('seg2', step)
                seg_pos = index_in_segment(step, yz_max)  # Find position in segment.
                speedyz = solver(seg_pos, speedyz, yz_min_weight, yz_min, movement_max)  # Solve speed for step.

            elif between(step, (yz_min, tlen)):  # Solve yz segment 3.
                # print('seg3', step)
                # seg_pos = index_in_segment(step, yz_min)  # Find position in segment.
                # speedyz = solver(seg_pos, speedyz, velocity, iyz_min, movement_max)  # Solve speed for step.
                speedyz = yz_min_weight
            colors_yz.append(colors[int(speedyz)])
            speeds_yz.append(speedyz)

            # SOLV XYZ
            xyz_sp = (speedxz + speedyz) / 2
            colors_xyz.append(colors[int(xyz_sp)])
            speeds_xyz.append(xyz_sp)
        return speeds_xz, speeds_yz, speeds_xyz, colors_xz, colors_yz, colors_xyz

    mesh = pymesh.load_mesh(obj_file)
    mesh = pymesh.subdivide(mesh, order=3)
    cv = mesh_sorter(mesh.vertices)

    fig = plt.figure(figsize=plt.figaspect(0.9), dpi=200, )
    facecolor = 'black'
    textcolor = 'white'
    fig.patch.set_facecolor(facecolor)
    rcParams['text.color'] = textcolor
    plt.rcParams.update({'font.size': 4})
    xyzticks = np.arange(-100, 100 + 50, 25)
    xyticks = np.arange(-100, 100 + 50, 25)
    scattersize = 4  # This is the size of our color points.
    weight_alpha = 6 / 10

    # ===============
    #  First subplot
    # ===============
    ax = fig.add_subplot(2, 2, 1, projection='3d')
    ax.set_facecolor(facecolor)
    ax.spines['bottom'].set_color(textcolor)
    ax.spines['top'].set_color(textcolor)
    ax.xaxis.label.set_color(textcolor)
    ax.yaxis.label.set_color(textcolor)
    ax.zaxis.label.set_color(textcolor)
    ax.tick_params(axis='x', colors=textcolor)
    ax.tick_params(axis='y', colors=textcolor)
    ax.tick_params(axis='z', colors=textcolor)
    ax.title.set_text('3D')
    ax.set_xlabel('(front) x')
    ax.set_ylabel('y')
    ax.set_zlabel('z')
    ax.set_xlim(-100, 100)  # TODO: These will need to be set to leg_len*2 in the future.
    ax.set_ylim(-100, 100)
    ax.set_zlim(-100, 100)
    plt.xticks(xyzticks)
    plt.yticks(xyzticks)
    # plt.zticks(xyzticks)

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

    print('xz', speeds[0])
    print('yz', speeds[1])
    xz_speeds = speeds[0]
    xz_colors = speeds[3]
    yz_speeds = speeds[1]
    yz_colors = speeds[4]
    xyz_speeds = speeds[2]
    xyz_colors = speeds[5]

    z_line = np.array(z_line)
    x_line = np.array(x_line)
    y_line = np.array(y_line)

    weight = list()
    for ct, it in enumerate(range(0, weight_len)):
        weight.append(ct)

    # TODO: Remember all the earth and reference measurements are going to need to be based on leg length and range of motion.
    # ax.plot3D(x_line, y_line, z_line, color='grey', label='trajectory')  # Plot trajectory.
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
    ax.scatter3D(x_line, y_line, z_line, c=xyz_colors, cmap='hsv', s=scattersize)
    ax.plot3D([-100, -100, 100, 100, -100], [100, -100, -100, 100, 100], [0, 0, 0, 0, 0],
              label='surface')  # Plot ground.
    ax.plot3D([0, 0, 0], [0, 0, 0], [0, -50, 0], color='orange', label='start')  # Plot start point.
    ax.scatter3D([0], [0], [100], color="grey", s=10, label='pivot')  # Plot leg pivot.

    # ax.scatter3D(wxz[0][0], wxz[0][1], z_line[wxz[2][0]], edgecolors='green', facecolors='none', label='mxweightxz',
    #              s=100, alpha=weight_alpha)  # Plot max weight xz.
    # ax.scatter3D(wxz[1][0], wxz[1][1], z_line[wxz[2][1]], edgecolors='black', facecolors='none', label='mnweightxz',
    #              s=100)  # Plot min weight xz.
    # ax.scatter3D(wyz[0][0], wyz[0][1], z_line[wyz[2][0]],edgecolors='red', facecolors='none', label='mxweightyz',
    #              s=100)  # Plot max weight yz.
    # ax.scatter3D(wyz[1][0], wyz[1][1], z_line[wyz[2][1]], edgecolors='blue', facecolors='none', label='mnweightyz',
    #              s=100)  # Plot min weight yz.

    # ===============
    # Second subplot x z
    # ===============
    ax = fig.add_subplot(2, 2, 2)
    ax.set_facecolor(facecolor)
    ax.spines['bottom'].set_color(textcolor)
    ax.spines['top'].set_color(textcolor)

    ax.xaxis.label.set_color(textcolor)
    ax.yaxis.label.set_color(textcolor)
    ax.tick_params(axis='x', colors=textcolor)
    ax.tick_params(axis='y', colors=textcolor)
    plt.xticks(xyticks)
    plt.yticks(xyticks)

    # ax.plot(x_line, z_line, color='grey', label='trajectory')  # Plot trajectory.
    ax.plot([-100, 100], [0, 0], label='surface')  # Plot ground
    ax.plot([0, 0], [-100, -50], color='orange', label='surface')  # Plot start.
    ax.scatter(0, 100, color='grey', label='pivot', s=100)  # Plot leg pivot.

    anchor = plot_angle((0, 100), -30)
    plt.text(anchor[0], anchor[1], '. ' * 7 + 'minx', fontsize=8, rotation=anchor[2], rotation_mode='anchor',
             verticalalignment='center')  # Plot min.
    anchor = plot_angle((0, 100), 80)
    plt.text(anchor[0], anchor[1], '. ' * 7 + 'maxx', fontsize=8, rotation=anchor[2], rotation_mode='anchor',
             verticalalignment='center')  # Plot max.
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
    ax.scatter(x_line, z_line, c=xz_colors, cmap='hsv', s=scattersize)

    ax.scatter(x_line[wxz[0]], z_line[wxz[0]], edgecolors='green', facecolors='none', label='mxweight',
               s=100, alpha=weight_alpha)  # Plot max weight.
    ax.scatter(x_line[wxz[1]], z_line[wxz[1]], edgecolors='orange', facecolors='none', label='mnweight',
               s=100, alpha=weight_alpha)  # Plot min weight.
    ax.scatter(x_line[ixz[0]], z_line[ixz[0]], edgecolors='pink', facecolors='none', label='mxweight',
               s=100, alpha=weight_alpha)  # Plot max implied weight.
    ax.scatter(x_line[ixz[1]], z_line[ixz[1]], edgecolors='pink', facecolors='none', label='mnweight',
               s=100, alpha=weight_alpha)  # Plot min implied weight.

    # ===============
    # Third subplot y z
    # ===============
    ax = fig.add_subplot(2, 2, 3)
    ax.set_facecolor(facecolor)
    ax.spines['bottom'].set_color(textcolor)
    ax.spines['top'].set_color(textcolor)

    ax.xaxis.label.set_color(textcolor)
    ax.yaxis.label.set_color(textcolor)
    ax.tick_params(axis='x', colors=textcolor)
    ax.tick_params(axis='y', colors=textcolor)
    plt.xticks(xyticks)
    plt.yticks(xyticks)
    # ax.plot(y_line, z_line, color='grey', label='trajectory')  # Plot trajectory.
    ax.plot([-100, 100], [0, 0], label='surface')  # Plot ground
    ax.plot([0, 0], [-100, -50], color='orange', label='surface')  # Plot start.
    ax.scatter(0, 100, color='grey', label='pivot', s=100)  # Plot leg pivot.

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

    ax.scatter(y_line[wyz[0]], z_line[wyz[0]], edgecolors='magenta', facecolors='none', label='mxweight', s=100,
               alpha=weight_alpha)  # Plot max weight.
    ax.scatter(y_line[wyz[1]], z_line[wyz[1]], edgecolors='cyan', facecolors='none', label='mnweight', s=100,
               alpha=weight_alpha)  # Plot min weight.
    ax.scatter(y_line[iyz[0]], z_line[iyz[0]], edgecolors='pink', facecolors='none', label='mxweight',
               s=100, alpha=weight_alpha)  # Plot max implied weight.
    ax.scatter(y_line[iyz[1]], z_line[iyz[1]], edgecolors='pink', facecolors='none', label='mnweight',
               s=100, alpha=weight_alpha)  # Plot min implied weight.
    # ===============
    # Fourth subplot x y
    # ===============
    ax = fig.add_subplot(2, 2, 4)
    ax.set_facecolor(facecolor)
    ax.spines['bottom'].set_color(textcolor)
    ax.spines['top'].set_color(textcolor)

    ax.xaxis.label.set_color(textcolor)
    ax.yaxis.label.set_color(textcolor)
    ax.tick_params(axis='x', colors=textcolor)
    ax.tick_params(axis='y', colors=textcolor)
    plt.xticks(xyticks)
    plt.yticks(xyticks)

    ax.plot(implied_line_x[0], implied_line_x[1], '.', color='pink')  # Plot implied line.
    ax.plot(implied_line_y[0], implied_line_y[1], '.', color='pink')  # plot implied line.
    # ax.plot(x_line, y_line, color='grey', label='trajectory')  # Plot trajectory.
    # ax.plot([-100, 100], [0, 0], label='surface')  # Plot ground
    ax.plot([-100, -50], [0, 0], color='orange', label='surface')  # Plot start.
    # ax.scatter(0, 0, color='grey', label='pivot', s=1)  # Plot leg pivot.
    ax.set_xlim(-100, 100)  # TODO: These will need to be set to leg_len*2 in the future.
    ax.set_ylim(-100, 100)
    ax.title.set_text('Top')
    ax.set_xlabel('(front) x')
    ax.set_ylabel('y')
    ax.scatter(x_line, y_line, c=xyz_colors, cmap='hsv', s=scattersize)
    ax.annotate("start", xy=(-99, 8), fontsize=7)

    ax.scatter(x_line[wxz[0]], y_line[wxz[0]], edgecolors='green', facecolors='none', label='mxweight',
               s=100, alpha=weight_alpha)  # Plot max weight.
    ax.scatter(x_line[wxz[1]], y_line[wxz[1]], edgecolors='orange', facecolors='none', label='mnweight',
               s=100, alpha=weight_alpha)  # Plot min weight.
    ax.scatter(x_line[wyz[0]], y_line[wyz[0]], edgecolors='magenta', facecolors='none', label='mxweight',
               s=100, alpha=weight_alpha)  # Plot max weight.
    ax.scatter(x_line[wyz[1]], y_line[wyz[1]], edgecolors='cyan', facecolors='none', label='mnweight',
               s=100, alpha=weight_alpha)  # Plot min weight.

    plt.subplots_adjust(left=0.1, right=0.9, bottom=0.1, top=0.9)
    plt.tight_layout()
    # plt.show()
    return FigureCanvasTkAgg(fig, parent)
