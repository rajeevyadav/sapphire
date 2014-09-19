""" Perform various Celestial coordinate transformations

    This module performs transformations between different
    Celestial coordinate systems.

    Formulae from: Duffett-Smith1990
    'Astronomy with your personal computer'
    ISBN 0-521-38995-X

    TODO: CHECK IF THESE CONVERSIONS ARE CORRECT!

"""
from numpy import (arcsin, arccos, arctan2, cos, sin,
                   array, radians, degrees, pi)

from . import clock, angles, axes


def horizontal_to_equatorial(longitude, latitude, timestamp, azimuth, zenith):
    """Convert Horizontal to Equatorial coordinates (J2000.0)

    :param longitude,latitude: Position of the observer on Earth in degrees.
                               North and east positive.
    :param timestamp: GPS timestamp of the observation.
    :param azimuth: zenith angle of the observation in radians.
    :param zenith: azimuth angle of the observation in radians.

    :returns: Right ascension (ra) and Declination (dec) in radians.

    From Duffett-Smith1990, 1500 EQHOR and 1600 HRANG

    """
    # altitude is the angle above the horizon
    altitude = pi / 2. - zenith

    slat = sin(radians(latitude))
    clat = cos(radians(latitude))
    sazi = sin(azimuth)
    cazi = cos(azimuth)
    salt = sin(altitude)
    calt = cos(altitude)

    dec = arcsin((salt * slat) + (calt * clat * cazi))
    HA = arccos((salt - (slat * sin(dec))) / (clat * cos(dec)))

    if sazi > 0:
        HA = 2 * pi - HA

    lst = clock.gps_to_lst(timestamp, longitude)
    ra = (angles.hours_to_radians(lst) - HA)
    ra %= 2 * pi

    return ra, dec


def equatorial_to_horizontal(longitude, latitude, timestamp, right_ascension,
                             declination):
    """Convert Equatorial (J2000.0) to Horizontal coordinates

    :param longitude,latitude: Position of the observer on Earth in degrees.
                               North and east positive.
    :param timestamp: GPS timestamp of the observation.
    :param right_ascension: right_ascension of the observation in radians.
    :param declination: declination of the observation in radians.

    :returns: azimuth and zenith in radians.

    From Duffett-Smith1990, 1500 EQHOR and 1600 HRANG

    """
    lst = clock.gps_to_lst(timestamp, longitude)
    HA = (angles.hours_to_radians(lst) - right_ascension)
    HA %= 2 * pi

    slat = sin(radians(latitude))
    clat = cos(radians(latitude))
    sha = sin(HA)
    cha = cos(HA)
    sdec = sin(declination)
    cdec = cos(declination)

    altitude = arcsin((sdec * slat) + (cdec * clat * cha))
    azimuth = arccos((sdec - (slat * sin(altitude))) / (clat * cos(altitude)))

    if sha > 0:
        azimuth = 2 * pi - azimuth

    # altitude is the angle above the horizon
    zenith = pi / 2. - altitude

    return azimuth, zenith


def equatorial_to_galactic(right_ascension, declintation, epoch='J2000'):
    """Convert Equatorial (J2000.0) to Galactic coordinates

    :param right_ascension: Right ascension (ra) in degrees.
    :param declintation: Declination (dec) in degrees.
    :param epoch: Epoch for Equatorial coordinates, either 'J2000' or 'B1950'.

    :returns: Galactic longitude (l) and latitude (b) in degrees.

    From Duffett-Smith1990, 2100 EQGAL

    """
    ra = radians(right_ascension)
    dec = radians(declintation)

    xyz = array(axes.spherical_to_cartesian(1, dec, ra))
    rotMatrix = array([[-0.054875539, 0.494109454, -0.867666136],
                       [-0.873437105, -0.444829594, -0.198076390],
                       [-0.483834992, 0.746982249, 0.455983795]])

    newxyz = dot(xyz, rotMatrix)
    latitude, longitude = axes.cartesian_to_spherical(*newxyz)[1:]

    return degrees(longitude), degrees(latitude)

    # some smart stuff..


def galactic_to_equatorial(longitude, latitude, epoch='J2000'):
    """Convert Galactic to Equatorial coordinates (J2000.0)

    :param longitude: Galactic longitude (l) in degrees.
    :param latitude: Galactic latitude (b) in degrees.
    :param epoch: Epoch for Equatorial coordinates, either 'J2000' or 'B1950'.

    :returns: Right ascension (ra) and Declination (dec) in radians.

    From Duffett-Smith1990, 2100 EQGAL

    """
    l = radians(longitude)
    b = radians(latitude)

    if epoch == 'J2000':
        # North galactic pole (J2000)
        # Reid & Brunthaler 2004
        pole_ra = radians(192.859508)
        pole_dec = radians(27.128336)
        # Position angle with respect to celestial pole
        posangle = radians(122.932 - 90.0)
    elif epoch == 'B1950':
        # North galactic pole (B1950)
        pole_ra = radians(192.25)
        pole_dec = radians(27.4)
        # Position angle with respect to celestial pole
        posangle = radians(123.0 - 90.0)

    sinb = sin(b)
    cosb = cos(b)
    sinlpos = sin(l - posangle)
    coslpos = cos(l - posangle)
    cospoledec = cos(pole_dec)
    sinpoledec = sin(pole_dec)

    ra = arctan2((cosb * coslpos),
                 (sinb * cospoledec - cosb * sinpoledec * sinlpos)) + pole_ra
    dec = arcsin(cosb * cospoledec * sinlpos + sinb * sinpoledec)

    return ra, dec