"""
Here we have our matplotlib code for the writer app.

TODO: NOTE: This is in example format and will need to be largely refactored.
"""
import pymesh
# import pprint
# from stl import mesh as mmesh
import numpy as np
# mport math
from warehouse.utils import to_color, percent_of
import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits import mplot3d


def mesh_sorter(mesh):
    """
    Try to sort all these vertices...

    TODO: Remember this is for visual reprensentation ONLY!! We can add the extra vertex to the real loop.***
    """
    mesh = mesh.tolist()
    mesh.append(mesh[0])

    return mesh


def pymesh_stl(obj_file, parent, theme, config, target, rt_data):
    """
    Method using pymesh.

    :param obj_file: This is the file we will operate on.
    :param parent: This is the passed frame instance in the UX.
    :param theme: This is the theme passed from the UX.
    :param config: This is the calibration data we will use to frame the plot.
    :param target: This is the specific leg (1-4) that we will run against.
    :param rt_data: This is the passed real-time model so we can populate data to the UX app.
    """
    target = str(target)
    leglength = config['zlength' + target]
    contact = config['contact']
    travel = config['ztravel' + target]
    rt_data['plot'] = dict()
    rt_data = rt_data['plot']

    maxx = leglength - percent_of(contact, travel)
    minn = maxx * -1

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
                        abs(axis1 - -maxx) * -1,  # TODO: the 100/-100 value here will need to be dynamic...
                        abs(axis2 - -maxx)
                    ]
                )
            )
            diffb.append(
                sum(
                    [
                        abs(axis1 - -maxx),
                        abs(axis2 - -maxx)
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

        TODO: We can use this to determine the order of points so we can normalize the start point.

        """

        tr = list(zip(*trajectory))
        diffa = list()
        diffb = list()
        for axis1, axis2 in tr:
            diffa.append(
                abs(axis1 - -maxx) * -1 / axis2
            )
            diffb.append(
                abs(axis1 - maxx) / axis2
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

        def solvexy(a_speed, length, inc_min, inc_max, a_min, a_max, min_weight, max_weight):
            """
            This figures out our velocity by-step, over increment.
            # TODO: It looks like we might have a problem solving scenarios where the implied weights are in the same location...

            :param a_speed: Velocity.
            :param length: Length of trajectory.
            :param inc_min: Increment minimum.
            :param inc_max: Increment maximum.
            :param a_min: Axis minimum.
            :param a_max: Axis maximum.
            :param max_weight: Maximum axis weight.
            :param min_weight: Minimum axis weight.
            """
            a_colors = list()
            a_speeds = list()
            speed = a_speed
            for stp in range(0, length):
                if between(stp, (inc_min, inc_max)):  # Solve implied segment.
                    speed = a_speed
                    # a_speeds.append(speed)

                elif between(stp, (inc_max, a_max)):  # Solve segment 1.
                    seg_pos = index_in_segment(stp, inc_max)  # Find position in segment.
                    speed = solver(seg_pos, speed, max_weight, a_max, movement_max)  # Solve speed for step.

                elif between(stp, (a_max, a_min)):  # Solve segment 2.
                    seg_pos = index_in_segment(stp, a_max)  # Find position in segment.
                    speed = solver(seg_pos, speed, min_weight, a_min, movement_max)  # Solve speed for step.

                elif between(stp, (a_min, length)):  # Solve segment 3.
                    speed = min_weight

                a_colors.append(colors[int(speed)])
                a_speeds.append(speed)

            return a_colors, a_speeds

        # print(weights[1])
        # print(implied_weights[1])
        velocity = config['velocity']  # TODO: This is going to have to be a dynamic value in the future.
        movement_max = 100  # TODO: Dont's forget that this measurement is a percentage.
        colors = to_color(0, 100)

        # Define weighting values.
        xz_max_weight = config['weightxmax']
        xz_min_weight = config['weightxmin']

        yz_max_weight = config['weightymax']
        yz_min_weight = config['weightymin']

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

        # Now we solve the velocities.

        speeds_xyz = list()
        colors_xyz = list()

        colors_xz, speeds_xz = solvexy(
            velocity,
            tlen,
            ixz_min,
            ixz_max,
            xz_min,
            xz_max,
            xz_min_weight,
            xz_max_weight,
        )

        colors_yz, speeds_yz = solvexy(
            velocity,
            tlen,
            iyz_min,
            iyz_max,
            yz_min,
            yz_max,
            yz_min_weight,
            yz_max_weight,
        )

        # SOLV XYZ
        for speedxz, speedyz in zip(speeds_xz, speeds_yz):
            xyz_sp = (speedxz + speedyz) / 2
            colors_xyz.append(colors[int(xyz_sp)])
            speeds_xyz.append(xyz_sp)

        return speeds_xz, speeds_yz, speeds_xyz, colors_xz, colors_yz, colors_xyz

    def min_max(_ax, _plt, _axis):
        """
        This plots the minimum and maximum movement guides.
        """
        if _axis == 'x':
            _ax.plot(
                [minn, maxx],
                [0, 0],
                label='surface',
                linewidth=theme['linewidth']
            )  # Plot ground
            _ax.plot(
                [0, 0],
                [minn, (int(maxx / -2))],
                color='orange',
                label='surface',
                linewidth=theme['linewidth']
            )  # Plot start.
            _ax.scatter(0, maxx, color='grey', label='pivot', s=theme['pivotsize'])  # Plot leg pivot.
            anchormin = plot_angle((0, maxx), config['xmin' + target])
            anchormax = plot_angle((0, maxx), config['xmax' + target])
            _ax.annotate("start", xy=(1, minn + 6), fontsize=theme['fontsize'])
        elif _axis == 'y':
            ax.plot(
                [minn, maxx],
                [0, 0],
                label='surface',
                linewidth=theme['linewidth']
            )  # Plot ground
            ax.plot(
                [0, 0],
                [minn, (int(maxx / -2))],
                color='orange',
                label='surface',
                linewidth=theme['linewidth']
            )  # Plot start.
            ax.scatter(
                0, maxx,
                color='grey',
                label='pivot',
                s=theme['pivotsize']
            )  # Plot leg pivot.
            anchormin = plot_angle((0, maxx), config['ymin' + target])
            anchormax = plot_angle((0, maxx), config['ymax' + target])
            _ax.annotate("start", xy=(1, minn + 6), fontsize=theme['fontsize'])
        else:
            raise ValueError
        _plt.text(
            anchormin[0],
            anchormin[1],
            '. ' * 7 + 'min' + _axis,
            fontsize=theme['fontsize'],
            rotation=anchormin[2],
            rotation_mode='anchor',
            verticalalignment='center'
        )  # Plot min.
        _plt.text(
            anchormax[0],
            anchormax[1],
            '. ' * 7 + 'max' + _axis,
            fontsize=theme['fontsize'],
            rotation=anchormax[2],
            rotation_mode='anchor',
            verticalalignment='center'
        )  # Plot max.
        z_min_pos = (int(leglength - config['ztravel' + target]))
        _ax.add_artist(
            plt.Circle(
                (0, maxx),
                z_min_pos,
                fill=False,
                linestyle=':',
                color=theme['text'],
                linewidth=theme['linewidth']
            )
        )  # Plot zmin.
        _ax.annotate("minz", xy=(-12, z_min_pos + 5), fontsize=theme['fontsize'])  # Label zmin.
        _ax.add_artist(
            plt.Circle(
                (0, maxx),
                leglength,
                fill=False,
                linestyle=':',
                color=theme['text'],
                linewidth=theme['linewidth']
            )
        )  # Plot zmax.
        _ax.annotate("maxz", xy=(65, maxx - leglength), fontsize=theme['fontsize'])  # Label zmax.
        _ax.annotate("gnd", xy=(minn + 1, 8), fontsize=theme['fontsize'])  # Label ground.

    mesh = pymesh.load_mesh(obj_file)  # load trajectory file.
    mesh = pymesh.subdivide(mesh, order=3)  # Split mesh.
    cv = mesh_sorter(mesh.vertices)  # Convert mesh to array.

    fig = plt.figure(figsize=plt.figaspect(1), dpi=200, tight_layout=True)  # Configure layout.
    facecolor = theme['main']
    textcolor = theme['text']
    fig.patch.set_facecolor(facecolor)
    rcParams['text.color'] = textcolor
    plt.rcParams.update({'font.size': theme['fontsize']})
    xyzticks = np.arange(minn, maxx, percent_of(50, maxx))
    xyticks = np.arange(minn, maxx, percent_of(25, maxx))
    scattersize = theme['scattersize']  # This is the size of our color points.
    weight_alpha = theme['plotalpha']

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
    ax.set_xlim(minn, maxx)  # TODO: These will need to be set to leg_len*2 in the future.
    ax.set_ylim(minn, maxx)
    ax.set_zlim(minn, maxx)
    ax.set_zticks(xyzticks)
    plt.xticks(xyzticks)
    plt.yticks(xyzticks)

    z_line = list()
    x_line = list()
    y_line = list()
    for x, y, z in cv:  # TODO: Prolly should use zip here...
        z_line.append(z)
        x_line.append(x)
        y_line.append(y)

    # TODO: We are probably going to have to create a normalizer to translate the trajectory with a predictable start.
    if z_line[1] > 0:  # TODO: We have to transform the order into a counter-clockwise sequence.
        z_line.reverse()
        x_line.reverse()
        y_line.reverse()

    weight_len = len(z_line)
    wyz = find_weights((y_line, z_line))
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

    rt_data['xz_speeds'] = speeds[0]
    xz_colors = speeds[3]
    rt_data['yz_speeds'] = speeds[1]
    yz_colors = speeds[4]
    rt_data['xyz_speeds'] = speeds[2]
    xyz_colors = speeds[5]

    rt_data['z_line'] = z_line = np.array(z_line)
    rt_data['x_line'] = x_line = np.array(x_line)
    rt_data['y_line'] = y_line = np.array(y_line)

    weight = list()
    for ct, it in enumerate(range(0, weight_len)):
        weight.append(ct)

    # TODO: Remember all the earth and reference measurements are going to need to be based on leg length and range of motion.
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
    ax.plot3D(*implied_line_x, color='pink', linewidth=theme['linewidth'])  # Print Implied line.
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
    ax.plot3D(*implied_line_y, color='pink', linewidth=theme['linewidth'])  # Print Implied line.
    ax.scatter3D(x_line, y_line, z_line, c=xyz_colors, cmap='hsv', s=scattersize)
    ax.plot3D([minn, minn, maxx, maxx, -minn], [maxx, minn, minn, maxx, maxx], [0, 0, 0, 0, 0],
              label='surface', linewidth=theme['linewidth'], color='black')  # Plot ground.
    ax.plot3D([0, 0, 0], [0, 0, 0], [0, (int(maxx) / -2), 0], color='orange', label='start', linewidth=theme['linewidth'])  # Plot start point.
    ax.scatter3D([0], [0], [maxx], color="grey", s=scattersize, label='pivot')  # Plot leg pivot.

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

    min_max(ax, plt, 'x')

    ax.set_xlim(minn, maxx)  # TODO: These will need to be set to leg_len*2 in the future.
    ax.set_ylim(minn, maxx)
    ax.title.set_text('Front')
    ax.set_xlabel('x')
    ax.set_ylabel('z')
    ax.scatter(x_line, z_line, c=xz_colors, cmap='hsv', s=scattersize)

    ax.scatter(x_line[wxz[0]], z_line[wxz[0]], edgecolors='green', facecolors='none', label='mxweight',
               s=theme['weightsize'], alpha=weight_alpha)  # Plot max weight.
    ax.scatter(x_line[wxz[1]], z_line[wxz[1]], edgecolors='orange', facecolors='none', label='mnweight',
               s=theme['weightsize'], alpha=weight_alpha)  # Plot min weight.
    ax.scatter(x_line[ixz[0]], z_line[ixz[0]], edgecolors='pink', facecolors='none', label='mxweight',
               s=theme['weightsize'], alpha=weight_alpha)  # Plot max implied weight.
    ax.scatter(x_line[ixz[1]], z_line[ixz[1]], edgecolors='pink', facecolors='none', label='mnweight',
               s=theme['weightsize'], alpha=weight_alpha)  # Plot min implied weight.

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

    min_max(ax, plt, 'y')

    ax.set_xlim(minn, maxx)  # TODO: These will need to be set to leg_len*2 in the future.
    ax.set_ylim(minn, maxx)
    ax.title.set_text('Side')
    ax.set_xlabel('y')
    ax.set_ylabel('(front) z')
    ax.scatter(y_line, z_line, c=yz_colors, cmap='hsv', s=scattersize)

    ax.scatter(y_line[wyz[0]], z_line[wyz[0]], edgecolors='magenta', facecolors='none', label='mxweight', s=theme['weightsize'],
               alpha=weight_alpha)  # Plot max weight.
    ax.scatter(y_line[wyz[1]], z_line[wyz[1]], edgecolors='cyan', facecolors='none', label='mnweight', s=theme['weightsize'],
               alpha=weight_alpha)  # Plot min weight.
    ax.scatter(y_line[iyz[0]], z_line[iyz[0]], edgecolors='pink', facecolors='none', label='mxweight',
               s=theme['weightsize'], alpha=weight_alpha)  # Plot max implied weight.
    ax.scatter(y_line[iyz[1]], z_line[iyz[1]], edgecolors='pink', facecolors='none', label='mnweight',
               s=theme['weightsize'], alpha=weight_alpha)  # Plot min implied weight.

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

    ax.plot([minn, minn / 2], [0, 0], color='orange', label='surface', linewidth=theme['linewidth'])  # Plot start.
    ax.set_xlim(minn, maxx)  # TODO: These will need to be set to leg_len*2 in the future.
    ax.set_ylim(minn, maxx)
    ax.title.set_text('Top')
    ax.set_xlabel('(front) x')
    ax.set_ylabel('y')
    ax.scatter(x_line, y_line, c=xyz_colors, cmap='hsv', s=scattersize)
    ax.annotate("start", xy=(minn + 1, 8), fontsize=theme['fontsize'])

    ax.scatter(x_line[wxz[0]], y_line[wxz[0]], edgecolors='green', facecolors='none', label='mxweight',
               s=theme['weightsize'], alpha=weight_alpha)  # Plot max weight.
    ax.scatter(x_line[wxz[1]], y_line[wxz[1]], edgecolors='orange', facecolors='none', label='mnweight',
               s=theme['weightsize'], alpha=weight_alpha)  # Plot min weight.
    ax.scatter(x_line[wyz[0]], y_line[wyz[0]], edgecolors='magenta', facecolors='none', label='mxweight',
               s=theme['weightsize'], alpha=weight_alpha)  # Plot max weight.
    ax.scatter(x_line[wyz[1]], y_line[wyz[1]], edgecolors='cyan', facecolors='none', label='mnweight',
               s=theme['weightsize'], alpha=weight_alpha)  # Plot min weight.

    ax.scatter(implied_line_x[0], implied_line_x[1], edgecolors='pink', facecolors='none', label='mnweight',
               s=theme['weightsize'], alpha=weight_alpha)  # Plot Implied weight.

    plt.tight_layout()
    return FigureCanvasTkAgg(fig, parent)
