"""
This is where we can store complex math code that we use in movement solvers and such

https://keisan.casio.com/exec/system/1359534351
https://www.reddit.com/r/askmath/comments/d5ka9y/finding_xyz_of_point_with_a_known_distance_from/
https://stackoverflow.com/questions/4116658/faster-numpy-cartesian-to-spherical-coordinate-conversion
https://stackoverflow.com/questions/48348953/spherical-polar-co-ordinate-to-cartesian-co-ordinate-conversion


TODO: Yup, we are going to have to rewrite this bitch a 3rd time...
"""
import gc
import math
from warehouse.utils import find_minmax as fmm, get_size
import numpy as np

from mpl_toolkits import mplot3d
import matplotlib.pyplot as plt
from matplotlib import cm
mp3 = mplot3d


class TranslateCoordinates:
    """
    This allows us to convert between different coordinates, transform grids...etc.
    """
    def __init__(self):
        self.grid = None
        self.vector = None
        self.coordinate = None
        self.radius = None
        self.theta = None
        self.phi = None
        self.x = None
        self.y = None
        self.z = None

    def cartesian_to_spherical(self, coordinate, ints=False):
        """
        This takes a tuple of XYZ coordinates and converts them to a spherical vector.

        """

        def cart2sp(x, y, z):
            """
            cart to sphere converter.
            """
            XsqPlusYsq = x ** 2 + y ** 2
            r = math.sqrt(XsqPlusYsq + z ** 2)  # r
            elev = math.atan2(z, math.sqrt(XsqPlusYsq))  # theta
            az = math.atan2(y, x)  # phi
            return r, elev, az

        self.coordinate = coordinate
        self.x, self.y, self.z = self.coordinate
        self.radius, self.theta, self.phi = cart2sp(x=self.x, y=self.y, z=self.z)
        self.vector = [
            its(self.radius, ints),
            its(self.theta, ints),
            its(self.phi, ints)
        ]
        return self

    def spherical_to_cartesian(self, vector, ints=False):
        """
        This takes a spherical vector and converts it to a cartesian coordinate.
        """

        def sp2cart(r, theta, phi):
            """
            sphere to cart converter.
            """
            return [
                r * math.sin(theta) * math.cos(phi),
                r * math.sin(theta) * math.sin(phi),
                r * math.cos(theta)
            ]
        self.vector = vector
        self.radius, self.theta, self.phi = self.vector
        self.x, self.y, self.z = sp2cart(r=self.radius, theta=self.theta, phi=self.phi)
        self.coordinate = bts((
            its(self.x, ints),
            its(self.y, ints),
            its(self.z, ints)
        ))

    def test_s2c(self, vector):
        """
        This will draw a test coordinate.
        """
        self.spherical_to_cartesian(vector, True)
        draw([0, self.x], [0, self.y], [0, self.z], 1)


def grid_solver_ax_z(axis_origin, z_origin, angle, distance):
    """
    This converts an angle starting at XY origin moving to distance into an XY coordinate.
    This is the 2d version
    # 0 degrees = North, 90 = East, 180 = South, 270 = West.
    """
    # 0 degrees = North, 90 = East, 180 = South, 270 = West
    dZ = distance*math.cos(math.radians(angle))   # change in y
    dAxis = distance*math.sin(math.radians(angle))   # change in x
    Xfinal = axis_origin + dAxis
    Zfinal = z_origin + dZ
    print(Zfinal)
    return Xfinal, Zfinal


def grid_solver_xyz(x_origin, y_origin, z_origin, angle_xz, angle_yz, distance, return_ints=False):
    """
    This converts an angle starting at XY origin moving to distance into an XY coordinate.
    This is the 3d version
    # 0 degrees = North, 90 = East, 180 = South, 270 = West.

    NOTE: Z axis is not calculated as an angle as it's not a radial value, rather its a value of elevation in steps.
    r/radial = distance = Z
    θ/theta = yaw = Y
    ϕ/phi = pitch = X


    x = r* sinϕ * cosθ

    y = r * sinϕ * sinθ

    z = r * cosϕ

    """
    def int_ret(val, switch):
        """
        This returns ints or floats based on switch.
        """
        if switch:
            val = int(val)
        return val

    # dY = distance * math.cos(math.radians(angle_yz))   # change in y.
    # dX = distance * math.sin(math.radians(angle_xz))   # change in x.
    # dZ = distance * math.cos(math.radians(angle_yz))  # Change in z.
    # Xfinal = int_ret(x_origin + dX, return_ints)
    # Yfinal = int_ret(y_origin + dY, return_ints)
    # Zfinal = int_ret(z_origin + dZ, return_ints)

    Xfinal, Zfinal = grid_solver_ax_z(x_origin, z_origin, angle_xz, distance)
    Yfinal, Zfinal = grid_solver_ax_z(y_origin, z_origin, angle_yz, distance)

    return int_ret(Xfinal, return_ints), int_ret(Yfinal, return_ints), int_ret(Zfinal, return_ints)


def grid_constructor(angles, pwm_angles, origin):
    """
    This will construct a grid based on the angles and axis supplied.
    NOTE: The accuracy of the grid is based on the passed resolution (in degrees.) - Future enhancement.
    NOTE: Origin is the XYZ coordinate of XYZ pivot.
    NOTE: Angles is the range of PWM steps that we need to evaluate (derived from min/max in settings).
    NOTE: PWM angles are the same as above just with PWM keying.

    TODO: We are going about this backwards, we need to create the grid, and then calculate the angles and distance for each point.
    TODO: We will have to establish a resolution and then clamp the points to the closest angular value we can attain with the servos.

    TODO: We might also have to come up with some way to smooth out the motion in the event we get violent shaking.

    Operations:
        This class will need to perform the following operations in order:
        1. create an xyz grid in reference to the min/max movement ranges.
            NOTE: We may have to transform the grid if we can't account for origin in the math.
        2. Discover our origin offset (pivot point of the leg).
        3. Convert the Cartesian grid coordinates into Euler spherical vector coordinates (excluding roll)
            for all points on the grid pointing to the origin.
        4. Each of these result sets will need to be recorded in separate lists as we will need to transform them.
        5, We will need to remap the axis to rotate the results positive 90 degrees.
            NOTE: This is because spherical coordinates start with a zero point at 12:00.
        6, We will then need to mirror the X and Y axis spherical mappings (keeping the Carttesian ones intact.)
            NOTE: This is because when mapping our servos they increase in value is counterclockwise.
    """
    def translate_origin(values):
        """
        When we pass the origin from settings it is in radial degrees that need to be converted to XYZ coordinates.
        To do this we will solve the XYZ grid position based on the configured
        axis neutrals from the point 0, 0, 0.
        """
        x, y, z = grid_solver_xyz(0, 0, 0, *values)
        return x, y, z

    def iterator(angle_set, solved_dict):
        """
        This iterates through our dicts and creates the coordinate to angle mapping
        """
        ori = translate_origin(origin)  # Find origin.
        x, y, z = angle_set
        for _x in x:
            for _y in y:
                for _z in z:
                    mapping = str(  # Disover the XYZ coordinate of the XYZ angle by distance.
                        grid_solver_xyz(
                            *ori,
                            angle_xz=int(_x),
                            angle_yz=int(_y),
                            distance=int(_z),
                            return_ints=True
                        )
                    )
                    if mapping not in solved_dict.keys():  # Update grid dictionary.
                        solved_dict[mapping] = _x, _y, _z
        return solved_dict

    solved_xyz = dict()
    solved_pwm = dict()
    solved_xyz = iterator(angles, solved_xyz)
    solved_pwm = iterator(pwm_angles, solved_pwm)
    draw(*solved_xyz, 1)
    return solved_xyz, solved_pwm


class GridSolver:
    """
    This is where we will build our local grid and pre-render the spherial vectors for each point to origin.

    TODO: It's becoming clear that we are going to have to build a spherical coordinate transform system.\
        We are chewing up waaaaaay too much memory with this technique :-/

    NOTE: The accuracy of the grid is based on the passed resolution (in degrees.) - Future enhancement.
    NOTE: Origin is the XYZ coordinate of XYZ pivot.
    NOTE: Angles is the range of PWM steps that we need to evaluate (derived from min/max in settings).
    NOTE: PWM angles are the same as above just with PWM keying.

    TODO: We are going about this backwards, we need to create the grid, and then calculate the angles and distance for each point.
    TODO: We will have to establish a resolution and then clamp the points to the closest angular value we can attain with the servos.

    TODO: We might also have to come up with some way to smooth out the motion in the event we get violent shaking.

    TODO: If we change the bytestrings into CSV instead of tuples we can further optimize memory consumption.

    Operations:
        This class will need to perform the following operations in order:
        1. create an xyz grid in reference to the min/max movement ranges.
            NOTE: We may have to transform the grid if we can't account for origin in the math.
        2. Discover our origin offset (pivot point of the leg).
        3. Convert the Cartesian grid coordinates into Euler spherical vector coordinates (excluding roll)
            for all points on the grid pointing to the origin.
        4. Each of these result sets will need to be recorded in separate lists as we will need to transform them.
        5, We will need to remap the axis to rotate the results positive 90 degrees.
            NOTE: This is because spherical coordinates start with a zero point at 12:00.
        6, We will then need to mirror the X and Y axis spherical mappings (keeping the Carttesian ones intact.)
            NOTE: This is because when mapping our servos they increase in value is counterclockwise.

        IMPORTANT NOTES:
            1. We will have to drop spherical coordinates that are outside the range of motion to conserve memory.
                to do this we insert an empty bytestring and if we happen to call on that coordinate during movement,
                we will look up the out of range spherical coordinate from the trajectory model and clamp to max.
                A. We might also just remove the impossible XYZ coordinates as well, as we can always fall back on
                    the trajectory model to fill in out of bounds coordinates and clamp them to spherical min and max.
            2. We will have to replace duplicates (overlaps in the coordinate systems) with -1 to conserve memory.
                if we come across a -1 during movement we will simply use the last value for that axis until a valid
                new value is encountered.
    """
    def __init__(self, range_x, range_y, range_z, leg_conf):
        """
        NOTE: Ranges are lists of grid points to use per-axis: x: [-4, -3, -2, -1, 0 ,1 ,2 ,3, 4, 5, 6]
        NOTE: origin is the offset we will transform the grid to account for the location of the leg pivot.
        NOTE: Origin is caluculated from the values in leg_conf (length, travel, (min, nu, max))
        """
        gc.collect()
        self.dummy = None
        self.calculations = None
        self.return_step = None
        self.percentage = None
        self.progress = None
        # print(range_x)
        # print(range_y)
        # print(range_z)
        # print(leg_conf)
        # Create arrays of spherical limits for clamp and constrain.
        # NOTE: radius = z, phi = y, theta = x ########################## IMPORTANT ###############################
        self.limits = list()
        for limit in ['z', 'x', 'y']:
            self.limits.append(
                list(
                    range(
                        leg_conf[limit]['min'],
                        leg_conf[limit]['max']
                    )
                )
            )
        z_ax = leg_conf['z']  # Find Z (radius) range of motion.
        self.r_o_m = (
            leg_conf['len'],
            leg_conf['trv'],
            (
                z_ax['min'],
                z_ax['nu'],
                z_ax['max']
            )
        )
        # Find minimum and maximum ranges for each axis (this will be used to create our grid).
        self.tc = TranslateCoordinates()
        self.range_x = range_x
        self.range_y = range_y
        self.range_z = range_z  # TODO: This is what we are going to use to measure our grid boundaries.
        # NOTE: This basically creates a cartesian bounding box around our spherical boundaries.
        # NOTE: It is hemispherical so the Z range is half of X and Y.
        self.xy_boundary = list(range(  # Calculate the size of our grid XY plane.
            max(range_z) * -1,
            max(range_z) + 1  # Account for zero.
        ))
        # TODO: In order to properly calculate origin we are going to need to calculate travel per step Z contrasted with leg length in mm.
        self.z_boundary = range_z  # TODO: We need to add the offset value of the figured origin to this.
        self.xyz_grid = {  # Init cartesian coordinates grid.
            'x': list(),
            'y': list(),
            'z': list(),  # TODO: We need to create all this using lists for easy transform, then render the results into a final set of grids.
            'pol': list()
        }
        self.pol_grid = dict()  # Init spherical coordinates grid.

        # TODO: Unsure at what stage we need to calculate the offset here.
        """
        origin_steps: the amount we will have to shift the zero point on the final grid.
        offset_steps: the amount we will have to add to the Z axis to account for overall leg length.
        origin_mm: This is the actual distance that our neutral point sits above the implied zero.
        mm_per_step: This is the actual travel in mm per step on the spherical radius. 
        """

        self.reset_counters()

        self.origin_steps, self.offset_steps, self.origin_mm, self.mm_per_step = figure_origin(*self.r_o_m)  # Calculate origin.
        starter = max(range_z) + 1
        scope = max(range_z) + self.origin_steps
        print('calculating offsets')
        while starter <= scope:
            range_z.append(starter)
            starter += 1
        print('constructing grid')
        for z_point in range_z:  # Create dictionary representing our grid.
            for y_point in range_y:
                for x_point in range_x:  # create the cartesian values.
                    self.xyz_grid['z'].append(z_point)
                    self.xyz_grid['y'].append(y_point)
                    self.xyz_grid['x'].append(x_point)
            self.progress += 1
            if self.progress == self.return_step:  # Return progress marker.
                self.percentage += 1
                self.progress = 0
                print(str(self.percentage) + '%')

        self.reset_counters()
        """
        Here we rotate our grid on the yz (2, 3) axis so z_max is pointing to y_max was.
        The reason for this being 0x0x0 on our grid is leg neutral and 0x0x0 in spherical coords is at our zenith.
        """
        print('rotating grid X 90 degrees.')
        self.xyz_grid = rotate_grid(self.xyz_grid, 'x', 1)  # Rotate grid 90 degrees clockwise on X.
        """
        Now we iterate through zipped X, Y, and Z coordinates and calculate the angles to origin (0x0x0 because we haven't shifted yet).
        It's important to note that we are keeping the X, Y, Z and polar coordinates in different lists. This will allow us to 
            transform axis before we render the final grid objects.
        """
        print('performing polar calculations')
        last_polar = [-1, -1, -1]  # record dummy last value to prevent name errors.
        xyz = self.xyz_grid
        for x, y, z in zip(xyz['x'], xyz['y'], xyz['z']):  # TODO: We need to figure a way to clean up all the positions outside the ROM
            polar = self.tc.cartesian_to_spherical((x, y, z), ints=True).vector  # calculate the polar coordinates
            if constrain(polar, self.limits):  # Discover if the spherical coordinate is within our range of movement.
                xyz['pol'].append(
                    bts(clamp(polar, last_polar))  # Append coordinate (in bytes) to grid excluding duplicates (coordinate overlaps).
                )
            else:
                xyz['pol'].append(b'')  # If outside range of motion add empty bytestring.
            last_polar = polar  # Set the last value so we can pass to clamp.
            self.progress += 1
            if self.progress == self.return_step:  # Return progress marker.
                self.percentage += 1
                self.progress = 0
                print(str(self.percentage) + '%')
        """
        Next we will clean  up the grid by removing all points that are outside the range of spherical motion.
        We will make up for this void of grid references by including them in the rehersal trajectory model.
        NOTE: This is done to ensure we don't overflow the physical memory with null references.
        """
        print('cleaning up')
        self.reset_counters()
        grid_len = len(self.xyz_grid['pol'])
        counter = 0  # We have to use this outside the loop as the size of the arrays will be changing as we iterate.
        for polar in range(grid_len):
            self.dummy = polar
            if self.xyz_grid['pol'][counter] == b'':  # We have to use counter as the range may change
                for ax in ['pol', 'x', 'y', 'z']:
                    del self.xyz_grid[ax][counter]
            else:
                counter += 1  # Only increment count if we DON'T delete.
            self.progress += 1
            # print(progress, '\t', return_step)
            if self.progress == self.return_step:  # Return progress marker.
                self.percentage += 1
                self.progress = 0
                print(str(self.percentage) + '%')
        cleaned = grid_len - len(self.xyz_grid['pol'])
        print('cleaned', cleaned, 'out of range coordinates')

        """
        Now we perform our final transform, we will rotate the grid another 90 degrees clockwise so Z+ is facing down.
        Then we will mirror the X and Y axis to reach a normalized position matching the radial movement of the servos.
        NOTE: The final axis mirroring will depend on weather or not the motor is configured to be reversed.
        """
        print('performing final transform')  # TODO: account for servo reversals here.
        self.xyz_grid = rotate_grid(self.xyz_grid, 'x', 1)  # Rotate grid 90 degrees clockwise on X.
        self.xyz_grid = reverse_axis(self.xyz_grid, 'x')
        self.xyz_grid = reverse_axis(self.xyz_grid, 'y')
        """
        Finally we will transpose the grid on the Z axis separate of the poler corrdinates so 0x0x0 is at XYZ nautral.
        """

        print('rendering complete, total size:', str(get_size(self.xyz_grid)) + ' MB')

        print(self.origin_steps, self.offset_steps, self.origin_mm, self.mm_per_step)
        print('x', len(self.xyz_grid['x']))
        print('y', len(self.xyz_grid['y']))
        print('z', len(self.xyz_grid['z']))
        print('polar', len(self.xyz_grid['pol']))
        print('total records', self.calculations)

        print('cleaned up', gc.collect(), ' MB')

    def reset_counters(self):
        """
        This resets the progress counters between events.
        """
        self.calculations = len(self.range_x) * len(self.range_y) * len(self.range_z)  # Discover number of calculations.
        self.return_step = self.calculations / 100  # Find 1% of the calculations
        self.progress = 0  # Set progress counter.
        self.percentage = 0  # Set percentage counter.


def clamp(new, last):
    """
    This will look at the last set of polar coordinates and compare them with the first, if one of the axis is a duplicate
    value it will replace it with b'-1' so when we iterate over the coordinates we can just use the last value when this condition.
    TODO: This *SHOULD* work if we effectively clamp minimum values when we render the rehearsal trajectory model.
    """
    # for idx, (lst, nw) in enumerate(zip(last, new)):
    #     if lst == nw:
    #         new[idx] = -1
    return new


def constrain(coordinates, limits):
    """
    This checks to see if the polar coordinates supplied are within the range of movement.
    """
    result = True
    try:
        for coord, limit in zip(coordinates, limits):
            if coord not in limit:
                result = False
    except ValueError as err:
        print(coordinates, limits, err)
        raise ValueError
    return result


def its(it, go=True):
    """
    This is for clamping floats to ints to save memory.
    """
    if go:
        it = int(it)
    return it


def bts(bt, go=True):
    """
    This just encodes stuff into bytes.
    """
    if not isinstance(bt, str):
        bt = str(bt).strip()
    if go:
        bt = bytes(bt, 'utf-8')
    return bt


def f_bts(f_b):
    """
    This is just a handy deal for converting bytes back into a usable format.
    """
    f_b = f_b.decode('utf-8')
    return eval(f_b)


def swap_axis(grid, axis1, axis2):
    """
    This swaps two axis on the cartesian grid.
    """
    ax_1 = grid[axis1]
    ax_2 = grid[axis2]
    del grid[axis1]
    del grid[axis2]
    grid[axis1] = ax_2
    grid[axis2] = ax_1
    return grid


def reverse_axis(grid, axis):
    """
    This reverses the cartesian coordinates on one grid axis.
    """
    grid[axis].reverse()
    return grid


def rotate_grid(grid, axis, count):
    """
    This will rotate a grid 90 degrees times count clockwise on the specified axis.
    """
    while count:  # TODO: This guy might need a little tuning.
        if axis == 'x':
            reverse_axis(grid, 'y')
            swap_axis(grid, 'z', 'y')
        elif axis == 'z':
            reverse_axis(grid, 'x')
            swap_axis(grid, 'x', 'y')
        else:
            reverse_axis(grid, 'x')
            swap_axis(grid, 'x', 'z')
        count -= 1
    return grid


def ls(boundary):
    """
    This converts a list of grid points into a numpy linspace.
    """
    start, stop = fmm(boundary)
    count = len(boundary)
    print(start, stop, count)
    return np.linspace(start, stop, count)


def figure_origin(length, travel, r_o_m):
    """
    This takes the length and travel (in mm) and figures the distance of the neutral point by range of motion (min, nu, max).
    """
    rom_min, rom_nu, rom_max = r_o_m
    steps_in_rom = len(list(range(rom_min, rom_max)))  # find out total steps within the range of motion.
    mm_per_step = travel / steps_in_rom  # Calculate our movement in mm per step.
    origin_mm = length - ((rom_max - rom_nu) * mm_per_step)  # Locate origin in mm.  # WRONG! we need to properly define the origin
    origin_steps = (rom_max - (rom_max - rom_nu)) / mm_per_step  # Locate origin in steps.
    offset_steps = rom_max / mm_per_step
    return origin_steps, offset_steps, origin_mm, mm_per_step


def thin(array, increment):
    """
    This thins out an array of points by returning one per increment.
    """
    result = list()
    skipper = 0
    for idx, point in enumerate(array):
        if not skipper:
            result.append(point)
        skipper += 1
        if skipper == increment:
            skipper = 0
    return result


def test(range_1, range_2, range_3, report=False):
    """
    This is just for experimenting
    """
    # def show(grid):
    #     """just prints"""
    #     for x, y, z, pol in zip(grid['x'], grid['y'], grid['z'], grid['pol']):
    #         print('x', x, '\ty', y, '\tz', z, '\tpol', pol)

    from stage import settings
    s = settings.settings
    result = GridSolver(list(range(*range_1)), list(range(*range_2)), list(range(*range_3)), s.legs['LEG1'])
    if report:
        draw(
            result.xyz_grid['x'],
            result.xyz_grid['y'],
            result.xyz_grid['z'],
            1,
        )
    return result


def draw(x, y, z, inc):
    """
    This is a simple matplotlib test for our output
    datad = {
    'Blues': _Blues_data,
    'BrBG': _BrBG_data,
    'BuGn': _BuGn_data,
    'BuPu': _BuPu_data,
    'CMRmap': _CMRmap_data,
    'GnBu': _GnBu_data,
    'Greens': _Greens_data,
    'Greys': _Greys_data,
    'OrRd': _OrRd_data,
    'Oranges': _Oranges_data,
    'PRGn': _PRGn_data,
    'PiYG': _PiYG_data,
    'PuBu': _PuBu_data,
    'PuBuGn': _PuBuGn_data,
    'PuOr': _PuOr_data,
    'PuRd': _PuRd_data,
    'Purples': _Purples_data,
    'RdBu': _RdBu_data,
    'RdGy': _RdGy_data,
    'RdPu': _RdPu_data,
    'RdYlBu': _RdYlBu_data,
    'RdYlGn': _RdYlGn_data,
    'Reds': _Reds_data,
    'Spectral': _Spectral_data,
    'Wistia': _wistia_data,
    'YlGn': _YlGn_data,
    'YlGnBu': _YlGnBu_data,
    'YlOrBr': _YlOrBr_data,
    'YlOrRd': _YlOrRd_data,
    'afmhot': _afmhot_data,
    'autumn': _autumn_data,
    'binary': _binary_data,
    'bone': _bone_data,
    'brg': _brg_data,
    'bwr': _bwr_data,
    'cool': _cool_data,
    'coolwarm': _coolwarm_data,
    'copper': _copper_data,
    'cubehelix': _cubehelix_data,
    'flag': _flag_data,
    'gist_earth': _gist_earth_data,
    'gist_gray': _gist_gray_data,
    'gist_heat': _gist_heat_data,
    'gist_ncar': _gist_ncar_data,
    'gist_rainbow': _gist_rainbow_data,
    'gist_stern': _gist_stern_data,
    'gist_yarg': _gist_yarg_data,
    'gnuplot': _gnuplot_data,
    'gnuplot2': _gnuplot2_data,
    'gray': _gray_data,
    'hot': _hot_data,
    'hsv': _hsv_data,
    'jet': _jet_data,
    'nipy_spectral': _nipy_spectral_data,
    'ocean': _ocean_data,
    'pink': _pink_data,
    'prism': _prism_data,
    'rainbow': _rainbow_data,
    'seismic': _seismic_data,
    'spring': _spring_data,
    'summer': _summer_data,
    'terrain': _terrain_data,
    'winter': _winter_data,
    # Qualitative
    'Accent': {'listed': _Accent_data},
    'Dark2': {'listed': _Dark2_data},
    'Paired': {'listed': _Paired_data},
    'Pastel1': {'listed': _Pastel1_data},
    'Pastel2': {'listed': _Pastel2_data},
    'Set1': {'listed': _Set1_data},
    'Set2': {'listed': _Set2_data},
    'Set3': {'listed': _Set3_data},
    'tab10': {'listed': _tab10_data},
    'tab20': {'listed': _tab20_data},
    'tab20b': {'listed': _tab20b_data},
    'tab20c': {'listed': _tab20c_data},
    }
    https://matplotlib.org/3.1.3/gallery/mplot3d/voxels_rgb.html#sphx-glr-gallery-mplot3d-voxels-rgb-py
    """
    def fix(axx):
        """
        This will turn a single point into a list of one.
        """
        if not isinstance(axx, list):
            axx = [axx]

        return axx
    # Draw output.
    fig = plt.figure()
    ax = plt.axes(projection="3d")

    z_points = fix(z)
    x_points = fix(x)
    y_points = fix(y)
    ax.scatter3D(x_points[::inc], y_points[::inc], z_points[::inc], c=z_points[::inc], cmap=cm.jet)

    plt.show()
