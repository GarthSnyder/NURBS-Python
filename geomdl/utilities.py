"""
.. module:: utilities
    :platform: Unix, Windows
    :synopsis: Provides common utility functions

.. moduleauthor:: Onur R. Bingol <contact@onurbingol.net>

"""

from .base import GeomdlFloat
from . import linalg


def make_zigzag(points, num_cols):
    """ Converts linear sequence of points into a zig-zag shape.

    This function is designed to create input for the visualization software. It orders the points to draw a zig-zag
    shape which enables generating properly connected lines without any scanlines. Please see the below sketch on the
    functionality of the ``num_cols`` parameter::

             num cols
        <-=============->
        ------->>-------|
        |------<<-------|
        |------>>-------|
        -------<<-------|

    Please note that this function does not detect the ordering of the input points to detect the input points have
    already been processed to generate a zig-zag shape.

    :param points: list of points to be ordered
    :type points: list
    :param num_cols: number of elements in a row which the zig-zag is generated
    :type num_cols: int
    :return: re-ordered points
    :rtype: list
    """
    new_points = []
    points_size = len(points)
    forward = True
    idx = 0
    rev_idx = -1
    while idx < points_size:
        if forward:
            new_points.append(points[idx])
        else:
            new_points.append(points[rev_idx])
            rev_idx -= 1
        idx += 1
        if idx % num_cols == 0:
            forward = False if forward else True
            rev_idx = idx + num_cols - 1

    return new_points


def make_quad(points, size_u, size_v):
    """ Converts linear sequence of input points into a quad structure.

    :param points: list of points to be ordered
    :type points: list, tuple
    :param size_v: number of elements in a row
    :type size_v: int
    :param size_u: number of elements in a column
    :type size_u: int
    :return: re-ordered points
    :rtype: list
    """
    # Start with generating a zig-zag shape in row direction and then take its reverse
    new_points = make_zigzag(points, size_v)
    new_points.reverse()

    # Start generating a zig-zag shape in col direction
    forward = True
    for row in range(0, size_v):
        temp = []
        for col in range(0, size_u):
            temp.append(points[row + (col * size_v)])
        if forward:
            forward = False
        else:
            forward = True
            temp.reverse()
        new_points += temp

    return new_points


def make_quadtree(points, size_u, size_v, **kwargs):
    """ Generates a quadtree-like structure from surface control points.

    This function generates a 2-dimensional list of control point coordinates. Considering the object-oriented
    representation of a quadtree data structure, first dimension of the generated list corresponds to a list of
    *QuadTree* classes. Second dimension of the generated list corresponds to a *QuadTree* data structure. The first
    element of the 2nd dimension is the mid-point of the bounding box and the remaining elements are corner points of
    the bounding box organized in counter-clockwise order.

    To maintain stability for the data structure on the edges and corners, the function accepts ``extrapolate``
    keyword argument. If it is *True*, then the function extrapolates the surface on the corners and edges to complete
    the quad-like structure for each control point. If it is *False*, no extrapolation will be applied.
    By default, ``extrapolate`` is set to *True*.

    Please note that this function's intention is not generating a real quadtree structure but reorganizing the
    control points in a very similar fashion to make them available for various geometric operations.

    :param points: 1-dimensional array of surface control points
    :type points: list, tuple
    :param size_u: number of control points on the u-direction
    :type size_u: int
    :param size_v: number of control points on the v-direction
    :type size_v: int
    :return: control points organized in a quadtree-like structure
    :rtype: tuple
    """
    # Get keyword arguments
    extrapolate = kwargs.get('extrapolate', True)

    # Convert control points array into 2-dimensional form
    points2d = []
    for j in range(0, size_v):
        row_list = []
        for i in range(0, size_u):
            row_list.append(points[i + (j * size_u)])
        points2d.append(row_list)

    # Traverse 2-dimensional control points to find neighbors
    qtree = []
    for v in range(size_v):
        for u in range(size_u):
            temp = [points2d[u][v]]
            # Note: negative indexing actually works in Python, so we need explicit checking
            if u + 1 < size_u:
                temp.append(points2d[u+1][v])
            else:
                if extrapolate:
                    extrapolated_edge = linalg.vector_generate(points2d[u - 1][v], points2d[u][v])
                    translated_point = linalg.point_translate(points2d[u][v], extrapolated_edge)
                    temp.append(translated_point)
            if v + 1 < size_v:
                temp.append(points2d[u][v+1])
            else:
                if extrapolate:
                    extrapolated_edge = linalg.vector_generate(points2d[u][v - 1], points2d[u][v])
                    translated_point = linalg.point_translate(points2d[u][v], extrapolated_edge)
                    temp.append(translated_point)
            if u - 1 >= 0:
                temp.append(points2d[u-1][v])
            else:
                if extrapolate:
                    extrapolated_edge = linalg.vector_generate(points2d[u + 1][v], points2d[u][v])
                    translated_point = linalg.point_translate(points2d[u][v], extrapolated_edge)
                    temp.append(translated_point)
            if v - 1 >= 0:
                temp.append(points2d[u][v-1])
            else:
                if extrapolate:
                    extrapolated_edge = linalg.vector_generate(points2d[u][v + 1], points2d[u][v])
                    translated_point = linalg.point_translate(points2d[u][v], extrapolated_edge)
                    temp.append(translated_point)
            qtree.append(tuple(temp))

    # Return generated quad-tree
    return tuple(qtree)


def evaluate_bounding_box(ctrlpts):
    """ Computes the minimum bounding box of the point set.

    The (minimum) bounding box is the smallest enclosure in which all the input points lie.

    :param ctrlpts: points
    :type ctrlpts: list, tuple
    :return: bounding box in the format [min, max]
    :rtype: tuple
    """
    # Estimate dimension from the first element of the control points
    dimension = len(ctrlpts[0])

    # Evaluate bounding box
    bbmin = [GeomdlFloat('inf') for _ in range(0, dimension)]
    bbmax = [GeomdlFloat('-inf') for _ in range(0, dimension)]
    for cpt in ctrlpts:
        for i, arr in enumerate(zip(cpt, bbmin)):
            if arr[0] < arr[1]:
                bbmin[i] = arr[0]
        for i, arr in enumerate(zip(cpt, bbmax)):
            if arr[0] > arr[1]:
                bbmax[i] = arr[0]

    return tuple(bbmin), tuple(bbmax)


def compute_delta_from_sample_size(sample_size, domain, domain_range):
    """ Computes delta from sample size

    :param sample_size: sample size
    :type sample_size: int
    :param domain: parametric domain
    :type domain: list, tuple
    :param domain: parametric domain range
    :type domain: float
    :return: delta value
    :rtype: float
    """
    return (domain[1] - domain[0]) / (domain_range * GeomdlFloat(sample_size - 1))


def compute_sample_size_from_delta(delta):
    """ Computes sample size from delta

    :param delta: evaluation delta
    :type delta: float
    :return: sample size
    :rtype: int
    """
    return int(1.0 / delta) + 1
