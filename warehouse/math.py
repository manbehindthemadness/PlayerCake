"""
This is where we can store complex math code that we use in movement solvers and such

https://keisan.casio.com/exec/system/1359534351
https://www.reddit.com/r/askmath/comments/d5ka9y/finding_xyz_of_point_with_a_known_distance_from/
https://stackoverflow.com/questions/4116658/faster-numpy-cartesian-to-spherical-coordinate-conversion
https://stackoverflow.com/questions/48348953/spherical-polar-co-ordinate-to-cartesian-co-ordinate-conversion

"""

import math
from warehouse.utils import find_minmax as fmm
import numpy as np
import pprint


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

    def cartesian_to_spherical(self, coordinate):
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
        self.vector = (self.radius, self.theta, self.phi)
        return self

    def spherical_to_cartesian(self, vector):
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
        self.coordinate = (self.x, self.y, self.z)


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
    r/radial = distance - Z servo.
    θ/theta = yaw
    ϕ/phi = pitch


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
    return solved_xyz, solved_pwm


class GridSolver:
    """
    This is where we will build our local grid and pre-render the spherial vectors for each point to origin.

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
    def __init__(self, range_x, range_y, range_z, leg_conf):
        """
        NOTE: Ranges are lists of grid points to use per-axis: x: [-4, -3, -2, -1, 0 ,1 ,2 ,3, 4, 5, 6]
        NOTE: origin is the offset we will transform the grid to account for the location of the leg pivot.
        NOTE: Origin is caluculated from the values in leg_conf (length, travel, (min, nu, max))
        """
        # Find minimum and maximum ranges for each axis (this will be used to create our grid).
        self.tc = TranslateCoordinates()
        self.range_x = fmm(range_x)
        self.range_y = fmm(range_y)
        self.range_z = fmm(range_z)  # TODO: This is what we are going to use to measure our grid boundaries.
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

        for z_point in range_z:  # Create dictionary representing our grid.
            for y_point in range_y:
                for x_point in range_x:  # create the cartesian values.
                    self.xyz_grid['z'].append(z_point)
                    self.xyz_grid['y'].append(y_point)
                    self.xyz_grid['x'].append(x_point)
        """
        Here we rotate our grid on the yz (2, 3) axis so z_max is pointing to y_max was.
        The reason for this being 0x0x0 on our grid is leg neutral and 0x0x0 in polar coords is at our zenith.
        """
        self.xyz_grid = rotate_grid(self.xyz_grid, 'x', 1)  # Rotate grid 90 degrees clockwise on X.
        """
        Now we iterate through zipped X, Y, and Z coordinates and calculate the angles to origin (0x0x0 because we haven't shifted yet).
        It's important to note that we are keeping the X, Y, Z and polar coordinates in different lists. This will allow us to 
            transform axis before we render the final grid objects.
        """
        xyz = self.xyz_grid
        for x, y, z in zip(xyz['x'], xyz['y'], xyz['z']):
            polar = self.tc.cartesian_to_spherical((x, y, z))  # calculate the polar coordinates
            xyz['pol'].append(polar)

        print('x', len(self.xyz_grid['x']))
        print('y', len(self.xyz_grid['y']))
        print('z', len(self.xyz_grid['z']))
        print('polar', len(self.xyz_grid['pol']))
        # pprint.PrettyPrinter(indent=4).pprint(self.xyz_grid)
        # print(self.xyz_grid)
        # for axis, gridline in zip(['x', 'y', 'z'], self.xyz_grid):
        #     print(axis, list(gridline))


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
    origin_st = rom_max - (rom_max - rom_nu)  # Locate origin in steps.
    return origin_st, origin_mm, mm_per_step
