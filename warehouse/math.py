"""
This is where we can store complex math code that we use in movement solvers and such

https://keisan.casio.com/exec/system/1359534351

einsteinpy:
https://einsteinpy-einsteinpy.readthedocs.io/en/latest/api/utils/coord_transforms.html
https://github.com/numba/numba/issues/3670
install numba using apt
"""
import numpy as np
# import pprint
from mpl_toolkits import mplot3d
import matplotlib.pyplot as plt
from matplotlib import cm
mp3 = mplot3d


class TranslateCoordinates:
    """
    This allows us to convert between different coordinates, transform grids...etc.

    ρ/rho = distance = Z
    θ/theta = yaw = Y
    ϕ/phi = pitch = X

    """
    def __init__(self, settings, leg, debug=False):
        self.debug = debug
        self.settings = settings.settings
        # Get leg settings.
        self.leg = self.settings.legs[leg]
        self.phiset = self.leg['x']
        self.thetaset = self.leg['y']
        self.rhoset = self.leg['z']
        # Get minimum, neutral, and maximum PWM values.
        self.phi_range = (self.phiset['min'], self.phiset['nu'], self.phiset['max'])
        self.theta_range = (self.thetaset['min'], self.thetaset['nu'], self.thetaset['max'])
        self.rho_range = (self.rhoset['min'], self.rhoset['nu'], self.rhoset['max'])
        self.neutral = (self.rhoset['nu'], self.thetaset['nu'], self.phiset['nu'])
        # Get radius range in mm so we can figure the offset for our pivot point.
        self.length = self.leg['len']
        self.travel = self.leg['trv']
        self.origin_steps = None
        self.origin_mm = None
        self.offset_steps = None
        self.mm_per_step = None
        # Create mapping arrays so the zero point on our output grid matches the PWM neutral point.
        self.phiarray = self.build_range(self.phi_range)
        self.thetaarray = self.build_range(self.theta_range)
        self.rhoarray = self.build_range(self.rho_range, origin=True)
        # Construct the polar grid map dictionary.
        # self.gridmap = self.build_gridmap()

        self.vector = None
        self.vector_raw = None
        self.coordinate = tuple()
        self.coordinate_raw = None
        self.rho = None
        self.theta = None
        self.phi = None
        self.x = None
        self.y = None
        self.z = None

    def refresh(self):
        """
        We are going to move all the jazz from init into here so we can reload settings after modification.
        """

    @staticmethod
    def range_scroller(axis, distance):
        """
        This takes an axis range array and scrolls it by distance
        """
        return np.add(axis, distance)

    def position_coordinate(self, grid, xm=0, ym=0, zm=0):
        """
        This repositions a coordinate or a grid.

        TODO: This guy still needs some work...
        """
        x, y, z = grid
        x = self.range_scroller(x, xm)
        y = self.range_scroller(y, ym)
        z = self.range_scroller(z, zm)
        return x, y, z

    def rotate_grid(self, axis, grid, count):
        """
        This will rotate a cartesian grid 90 degrees times count clockwise on the specified axis.
        axis:
        0 = X
        1 = Y
        2 = Z
        """
        x, y, z = grid
        # x, y = self.swap_axis(x, y)
        while count:  # TODO: This guy might need a little tuning.
            if axis == 0:  # X
                # z, y = self.swap_axis(z, y)
                y = self.reverse_axis(y)
                z, y = self.swap_axis(z, y)
            elif axis == 2:  # Z
                x = self.reverse_axis(x)
                x, y = self.swap_axis(x, y)
            else:  # Y
                x = self.reverse_axis(x)
                x, z = self.swap_axis(x, z)
            count -= 1
        return x, y, z

    @staticmethod
    def reverse_axis(axis):
        """
        This will reverse an axis on the cartesian grid.
        """
        if isinstance(axis, np.ndarray):
            np.flip(axis)
        else:
            axis = np.multiply(axis, -1)
        return axis

    @staticmethod
    def swap_axis(axis1, axis2):
        """
        This swaps two axis on the cartesian grid.
        """
        return axis2, axis1

    def figure_origin(self):
        """
        This takes the length and travel (in mm) and figures the distance of the neutral point by range of motion (min, nu, max).
        origin steps  - The number of steps in rho at the *neutral* point of motion of rho.
                            This point represents the distance between the zero point and pivot point of theta and phi.
        offset steps  - The number of steps in rho between the minimum range of motion add the axis pivot point of theta and phi.
        origin mm     - The same as origin steps except calculated in millimeters.
        mm per step  - The distance in millimeters per one step of rho.

        TODO: Math tested and passes tests, edit with care.
        :rtype: tuple
        """
        rom_min, rom_nu, rom_max = self.rho_range
        steps_in_rom = len(list(range(rom_min, rom_max)))  # find out total steps within the range of motion.
        mm_per_step = self.travel / steps_in_rom  # Calculate our movement in mm per step.
        origin_mm = self.length - ((rom_max - rom_nu) * mm_per_step)  # Locate origin in mm.
        origin_steps = (self.length / mm_per_step) - (rom_max - rom_nu)  # Locate origin in steps.
        offset_steps = rom_max / mm_per_step  # Locate offset in steps.
        self.origin_steps = int(origin_steps)
        self.offset_steps = int(offset_steps)
        self.origin_mm = origin_mm
        self.mm_per_step = mm_per_step
        return self

    def build_range(self, ax_minnumax, origin=None):
        """
        This will convert polar min/max to a set of lists accounting for the origin.
        One list will represent the pol

        TODO: We really need to change polar to spherical to avoid confusion.

        TODO: Math tested and passes tests, edit with care,
        """
        def prefix(array):
            """
            This adds one less to the beginning of an array
            """
            return [array[0] - 1] + array

        def suffix(array):
            """
            This adds one more to the end of an array.
            """
            array += [array[-1] + 1]
            return array

        mi, nu, ma = ax_minnumax  # Collect range of motion.
        org = 0
        if origin:
            self.figure_origin()  # Discover origin offsets.
            org = self.origin_steps  # TODO: We might need to subtract 1 from travel to account for the zero point on a list.
        if self.debug:
            print('min/nu/max', mi, nu, ma)
        sphericalarray = [org]  # Start spherical coordinate array at neutral accounting for origin offset is needed.
        pwmarray = [int(nu)]  # Start PWM array from neutral range of motion.
        minimum = False
        maximum = False
        while not minimum and not maximum:  # Build arrays out from the neutral points until the boundaries match range of motion.
            if pwmarray[0] != int(mi):  # Check to see if minimum range has been reached.
                sphericalarray = prefix(sphericalarray)
                pwmarray = prefix(pwmarray)
            else:
                minimum = True
            if pwmarray[-1] != int(ma):  # Check to see if maximum has been reached.
                sphericalarray = suffix(sphericalarray)
                pwmarray = suffix(pwmarray)
            else:
                maximum = True
        if self.debug:
            print('pol / pwm')
            for pol, pwm in zip(sphericalarray, pwmarray):
                print(pol, pwm)
        return sphericalarray, pwmarray

    def normalize(self):
        """
        This re-maps the cartesian coordinates to match our physical axis.

        TODO: Remember we are going to have to reverse all this when we are reading trajectories.
        """
        self.coordinate = self.rotate_grid(0, self.coordinate, 1)  # Rotate grid 90 degrees.
        self.coordinate = self.position_coordinate(grid=self.coordinate, zm=self.origin_steps)  # Adjust for offset.
        x = self.reverse_axis(self.coordinate[0])  # Mirror X.
        y = self.reverse_axis(self.coordinate[1])  # Mirror Y.
        x, y = self.swap_axis(x, y)  # Swap x and y.
        z = self.coordinate[2]
        self.coordinate = (x, y, z)

    @staticmethod
    def rads2degs(vector):
        """
        Utility for converting radians into degrees.
        Vector is an array.
        """
        return np.rad2deg(vector)

    @staticmethod
    def degs2rads(coordinate):
        """
        Utility for converting degrees into radians.
        Coordinate is an array.
        """
        return np.deg2rad(coordinate)

    def cartesian_to_spherical(self, coordinate, ints=False):
        """
        This takes a tuple of XYZ coordinates and converts them to a spherical vector.

        NOTE on ints: Due to floating decimal variations when we round to ints we may see up to 1 degree
                of inaccuracy in our output PER round operation (eg converting in and converting out would drift max 2)

        """

        def cart2sp(x, y, z):
            """
            Cart to sphere converter.

            This math has been tested working:
                https://keisan.casio.com/exec/system/1359533867

            ρ/rho = distance = Z
            θ/theta = yaw = Y
            ϕ/phi = pitch = X

            """
            xy_squared = np.square(x) + np.square(y)
            rho = np.sqrt(xy_squared + np.square(z))  # Calculate rho.
            phi = np.arctan2(np.sqrt(xy_squared), z)  # Calculate phi.
            theta = np.arctan2(y, x)  # Calculate theta.
            return rho, theta, phi

        self.coordinate = coordinate
        self.x, self.y, self.z = self.coordinate
        self.rho, self.theta, self.phi = cart2sp(x=self.x, y=self.y, z=self.z)  # Convert cartesian ticks to spherical vector.
        self.theta, self.phi = self.rads2degs([self.theta, self.phi])  # convert theta and phi from radians into degrees.
        self.vector_raw = self.rho, self.theta, self.phi  # Store raw vector.
        self.vector = its(self.vector_raw, ints)  # Store rounded vector.
        return self

    def spherical_to_cartesian(self, vector, ints=False):
        """
        This takes a spherical vector and converts it to a cartesian coordinate.

        NOTE on ints: Due to floating decimal variations when we round to ints we may see up to 1 degree
                of inaccuracy in our output PER round operation (eg converting in and converting out would drift max 2)
        """

        def sp2cart(rho, theta, phi):
            """
            sphere to cart converter.

            This math has been tested working:
                https://keisan.casio.com/exec/system/1359534351

            ρ/rho = distance = Z
            θ/theta = yaw = Y
            ϕ/phi = pitch = X
            """
            return [
                np.multiply(np.multiply(rho, np.sin(phi)), np.cos(theta)),  # Calculate X.
                np.multiply(np.multiply(rho, np.sin(phi)), np.sin(theta)),  # Calculate Y.
                np.multiply(rho, np.cos(phi))  # Calculate Z.
            ]
        self.vector = vector
        self.rho, self.theta, self.phi = self.vector
        self.theta, self.phi = self.degs2rads([self.theta, self.phi])  # Convert theta and phi from degrees into radians.
        self.x, self.y, self.z = sp2cart(rho=self.rho, theta=self.theta, phi=self.phi)  # Convert spherical vector into cartesian ticks.
        self.coordinate_raw = self.x, self.y, self.z  # Store raw coordinate.
        self.coordinate = its(self.coordinate_raw, ints)  # Store rounded coordinate.
        return self

    def test(self, vector):
        """
        This will draw a test coordinate.
        """
        print('steps/offset/originmm/mmperstep', self.origin_steps, self.offset_steps, self.origin_mm, self.mm_per_step)
        self.spherical_to_cartesian(vector, True)
        print('raw cartesian ticks', self.coordinate_raw)
        print('cartesian ticks', self.coordinate)
        print('spherical degrees input', self.vector)
        self.cartesian_to_spherical(self.coordinate, True)
        print('raw spherical degrees output', self.vector_raw)
        print('spherical degrees output', self.vector)
        print('\n')
        print('cartesian ticks', self.coordinate)
        self.normalize()
        print('normalized cartesian coordinate', self.coordinate)
        self.draw(self.coordinate, (0, 0, self.origin_steps))
        # print('grimap:')
        # pprint.PrettyPrinter(indent=4).pprint(self.gridmap)

    def draw(self, coordinate, origin):
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
        x, y, z = coordinate
        xo, yo, zo = origin
        print('origin', origin)
        offset = zo  # figure_origin(*origin)[0]
        plotrange = offset
        neg_plotrange = plotrange * -1
        points = [
            [x, xo],
            [y, yo],
            # shift_axis([z, 0], plotrange)
            [z, zo]
        ]
        # print(points)
        r = zo
        u, v = np.mgrid[0:2 * np.pi:20j, 0:np.pi:10j]
        xx = np.multiply(r, np.multiply(np.cos(u), np.sin(v)))
        yy = np.multiply(r, np.multiply(np.sin(u), np.sin(v)))
        zz = np.multiply(r, np.cos(v))
        zz = self.range_scroller(zz, zo)
        # TODO: Add range of motion clamp here.
        # Draw output.
        # fig = plt.figure()
        ax = plt.axes(projection="3d")
        ax.plot3D(*points, color='blue', linewidth=1)  # servo angle.
        ax.plot3D([0, x], [0, y], [0, z], color='blue', linewidth=1)  # Zero point angle for reference.
        ax.plot3D(  # plot ground.
            [plotrange, plotrange, neg_plotrange, neg_plotrange, plotrange],
            [plotrange, neg_plotrange, neg_plotrange, plotrange, plotrange],
            [0, 0, 0, 0, 0],
            color='green'
        )
        ax.set_zlim(neg_plotrange / 2, plotrange + plotrange / 6)
        # noinspection PyUnresolvedReferences
        ax.scatter3D(*points, c=[1, 10], cmap=cm.jet, s=150)
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        ax.set_zlabel('z')
        # ax.plot_wireframe(xx, yy, zz, color="r")
        ax.scatter3D(xx, yy, zz, c='r', s=1)

        plt.show()


def its(it, go=True):
    """
    This is for clamping floats to ints to save memory.
    """
    if go:
        if isinstance(it, float):
            it = np.round(it)
        else:
            it = np.around(it)
    return it
