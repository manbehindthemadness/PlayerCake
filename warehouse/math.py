"""
This is where we can store complex math code that we use in movement solvers and such
"""

import math
# import numpy


def grid_solver_xy(x_origin, y_origin, angle, distance):
    """
    This converts an angle starting at XY origin moving to distance into an XY coordinate.
    This is the 2d version
    # 0 degrees = North, 90 = East, 180 = South, 270 = West.
    """
    # 0 degrees = North, 90 = East, 180 = South, 270 = West
    dY = distance*math.cos(math.radians(angle))   # change in y
    dX = distance*math.sin(math.radians(angle))   # change in x
    Xfinal = x_origin + dX
    Yfinal = y_origin + dY
    return Xfinal, Yfinal


def grid_solver_xyz(x_origin, y_origin, z_origin, angle_xz, angle_yz, distance, return_ints=False):
    """
    This converts an angle starting at XY origin moving to distance into an XY coordinate.
    This is the 3d version
    # 0 degrees = North, 90 = East, 180 = South, 270 = West.
    """
    def int_ret(val, switch):
        """
        This returns ints or floats based on switch.
        """
        if switch:
            val = int(val)
        return val

    dY = distance*math.cos(math.radians(angle_yz))   # change in y.
    dX = distance*math.sin(math.radians(angle_xz))   # change in x.
    dZ = distance * math.cos(math.radians(angle_yz))  # Change in z.
    Xfinal = int_ret(x_origin + dX, return_ints)
    Yfinal = int_ret(y_origin + dY, return_ints)
    Zfinal = int_ret(z_origin + dZ, return_ints)
    return Xfinal, Yfinal, Zfinal


def grid_constructor(angles, pwm_angles, origin):
    """
    This will construct a grid based on the angles and axis supplied.
    NOTE: The accuracy of the grid is based on the passed resolution (in degrees.) - Future enhancement.
    NOTE: Origin is the XYZ coordinate of XYZ pivot.
    NOTE: Angles is the range of PWM steps that we need to evaluate (derived from min/max in settings).
    NOTE: PWM angles are the same as above just with PWM keying.
    """
    def iterator(angle_set, solved_dict):
        """
        This iterates through our dicts and creates the coordinate to angle mapping
        """
        x, y, z = angle_set
        for _x in x:
            for _y in y:
                for _z in z:
                    mapping = str(  # Disover the XYZ coordinate of the XYZ angle by distance.
                        grid_solver_xyz(
                            *origin,
                            angle_xz=_x,
                            angle_yz=_x,
                            distance=_x,
                            return_ints=True
                        )
                    )
                    if mapping not in solved_dict.keys():  # Update grid dictionary.
                        solved_dict[mapping] = _x, _x, _z
        return solved_dict

    # unsolved_pwm = dict()
    # unsolved_xyz = dict()
    # for idx, (x, p) in enumerate(angles, pwm_angles):  # Create dinctionary of angle mappings in sequence.
    #     unso_x = dict()
    #     unso_p = dict()
    #     for angle in angles[idx]:  # TODO: look into this. Do we need it...
    #         unso_x[str(x)] = p
    #         unso_p[str(p)] = x
    #     unsolved_xyz[str(idx)] = unso_x
    #     unsolved_pwm[str(idx)] = unso_p
    # Here we will take the range of our angles and figure out what position on the above grid they fall into.
    solved_xyz = dict()
    solved_pwm = dict()
    for idx, (angles, angles_pwm) in enumerate(zip(angles, pwm_angles)):  # Iterate through angles and produce grid mappings.
        solved_xyz = iterator(angles, solved_xyz)  # Create grid keyed by cordinates, valued by radial offsets.
        solved_pwm = iterator(angles_pwm, solved_pwm)  # Create grid keyed by coordinates, valued by pwm settings.
    return solved_xyz, solved_pwm
