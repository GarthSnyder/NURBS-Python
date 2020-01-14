"""
.. module:: control_points
    :platform: Unix, Windows
    :synopsis: Provides helper classes for managing control points

.. moduleauthor:: Onur R. Bingol <contact@onurbingol.net>

"""

from functools import reduce
from .base import export, GeomdlBase, GeomdlDict, GeomdlFloat, GeomdlTypeSequence, GeomdlError

# Initialize an empty __all__ for controlling imports
__all__ = []


def default_find_index(pts_size, *args):
    """ Finds the array index from the input parametric position.

    .. code-block:: python

        from geomdl.control_points import find_index

        # parametric position: u=2, v=1, w=5
        # ctrlpts_size: number of control points in all parametric dimensions, e.g. (6, 7, 11)
        idx = find_index((6, 7, 11), 2, 1, 5)

    :param pts_size: number of control points in all parametric dimensions
    :type pts_size: list, tuple
    :param args: position in the parametric space
    :type args: tuple
    :return: index of the control points at the specified parametric position
    :rtype: int
    """
    idx = 0
    for i, arg in enumerate(args):
        mul_res = 1
        if i > 0:
            for j in pts_size[:i]:
                mul_res *= j
        idx += arg * mul_res
    return idx


def default_ctrlpts_init(num_ctrlpts, **kwargs):
    """ Initializes the control points container (default)

    Default functions use the container types included in the Python Standard Library.

    :param num_ctrlpts: total number of control points
    :type num_ctrlpts: int
    :return: a tuple containing initialized control points (as a ``list``) and data dictionary (as a ``dict``)
    :rtype: tuple
    """
    points = [() for _ in range(num_ctrlpts)]
    points_data = GeomdlDict()
    for k, v in kwargs.items():
        if v > 1:
            points_data[k] = [[0.0 for _ in range(v)] for _ in range(num_ctrlpts)]
        else:
            points_data[k] = [0.0 for _ in range(num_ctrlpts)]
    return points, points_data


def default_ctrlpts_set(pts_in, dim, pts_out):
    """ Fills the control points container with the input points (default)

    Default functions use the container types included in the Python Standard Library.

    :param pts_in: input list of control points
    :type pts_in: list, tuple
    :param dim: spatial dimension
    :type dim: int
    :param pts_out: output list of control points
    :type pts_out: list
    :return: ``pts_out`` will be returned
    :rtype: list
    """
    for idx, cpt in enumerate(pts_in):
        if not isinstance(cpt, GeomdlTypeSequence):
            raise GeomdlError("input[" + str(idx) + "] not valid. Must be a sequence.")
        if len(cpt) != dim:
            raise GeomdlError(str(cpt) + " not valid. Must be a " + str(dim) + "-dimensional list.")
        default_ctrlpt_set(pts_out, idx, cpt)
    return pts_out


def default_ctrlpt_set(pts_arr, idx, cpt):
    """ Assigns value to a single control point position inside the container (default)

    :param pts_arr: control points container
    :type pts_arr: list
    :param idx: container index
    :type idx: int
    :param cpt: control point
    :type cpt: list, tuple
    """
    pts_arr[idx] = tuple(GeomdlFloat(c) for c in cpt)


def extract_ctrlpts2d(cm):
    """ Extracts control points in u- and v-dimensions

    :param cm: control points manager
    :type cm: CPManager
    """
    if cm.get_opt('points_u') is None:
        pt_u = []
        for v in range(cm.size_v):
            pt_u += [cm[u, v] for u in range(cm.size_u)]
        cm.opt = ('points_u', pt_u)

    if cm.get_opt('points_v') is None:
        pt_v = []
        for u in range(cm.size_u):
            pt_v += [cm[u, v] for v in range(cm.size_v)]
        cm.opt = ('points_v', pt_v)


def extract_ctrlpts3d(cm):
    """ Extracts control points in u-, v- and w-dimensions

    :param cm: control points manager
    :type cm: CPManager
    """
    if cm.get_opt('points_u') is None:
        pt_u = []
        for w in range(cm.size_w):
            for v in range(cm.size_v):
                pt_u += [cm[u, v, w] for u in range(cm.size_u)]
        cm.opt = ('points_u', pt_u)

    if cm.get_opt('points_v') is None:
        pt_v = []
        for w in range(cm.size_w):
            for u in range(cm.size_u):
                pt_v += [cm[u, v, w] for v in range(cm.size_v)]
        cm.opt = ('points_v', pt_v)

    if cm.get_opt('points_w') is None:
        pt_w = []
        for v in range(cm.size_v):
            for u in range(cm.size_u):
                pt_w += [cm[u, v, w] for w in range(cm.size_w)]
        cm.opt = ('points_w', pt_w)


@export
class CPManager(GeomdlBase):
    """ Control points manager class

    Control points manager class provides an easy way to set control points without knowing the internal data structure
    of the geometry classes. The manager class is initialized with the number of control points in all parametric
    dimensions.

    This class inherits the following properties:

    * :py:attr:`type`
    * :py:attr:`id`
    * :py:attr:`name`
    * :py:attr:`dimension`
    * :py:attr:`opt`

    This class inherits the following methods:

    * :py:meth:`get_opt`
    * :py:meth:`reset`

    This class inherits the following keyword arguments:

    * ``id``: object ID (as an integer). *Default: 0*
    * ``name``: object name. *Default: name of the class*

    This class provides the following properties:

    * :py:attr:`points`
    * :py:attr:`points_data`
    * :py:attr:`size`
    * :py:attr:`count`
    * :py:attr:`dimension`

    This class provides the following methods:

    * :py:meth:`pt`
    * :py:meth:`set_pt`
    * :py:meth:`ptdata`
    * :py:meth:`set_ptdata`
    * :py:meth:`reset`

    This class provides the following keyword arguments:

    * ``config_pts_init``: function to initialize the control points container. *Default:* ``default_ctrlpts_init``
    * ``config_pts_set``: function to fill the control points container. *Default:* ``default_ctrlpts_set``
    * ``config_pt_set``: function to assign a single control point. *Default:* ``default_ctrlpt_set``
    * ``config_find_index``: function to find the index of the control point/vertex. *Default:* ``default_find_index``
    """
    __slots__ = ('_size', '_count', '_pts', '_ptsd', '_is_changed', '_iter_index')
    PDIM_ATTRIBS = ('size_u', 'size_v', 'size_w')

    def __init__(self, *args, **kwargs):
        super(CPManager, self).__init__(*args, **kwargs)
        # Update configuration dictionary
        self._cfg['func_pts_init'] = kwargs.pop('config_pts_init', default_ctrlpts_init)  # points init function
        self._cfg['func_pts_set'] = kwargs.pop('config_pts_set', default_ctrlpts_set)  # points set function
        self._cfg['func_pt_set'] = kwargs.pop('config_pt_set', default_ctrlpt_set)  # single point set function
        self._cfg['func_find_index'] = kwargs.pop('config_find_index', default_find_index)  # index finding function
        # Update size and count
        self._size = tuple(int(arg) for arg in args)  # size in all parametric dimensions
        self._count = reduce(lambda x, y: x * y, self.size)  # total number of control points
        # Initialize control points and associated data container
        self._pts, self._ptsd = self._cfg['func_pts_init'](self.count, **kwargs)
        self._is_changed = False  # flag to check changes

    def __call__(self, points):
        self.points = points
        self._is_changed = True

    def __reduce__(self):
        return (self.__class__, (self.points,))

    def __next__(self):
        try:
            result = self._pts[self._iter_index]
        except IndexError:
            raise StopIteration
        self._iter_index += 1
        return result

    def __len__(self):
        return self.count

    def __reversed__(self):
        return reversed(self._pts)

    def __getitem__(self, item):
        if isinstance(item, int):
            return self._pts[item]
        if isinstance(item, tuple):
            if len(item) != len(self.size):
                raise ValueError("The n-dimensional indices must be equal to number of parametric dimensions")
            idx = self._cfg['func_find_index'](self.size, *item)
            return self._pts[idx]
        raise TypeError(self.__class__.__name__ + " indices must be integer or tuple, not " + item.__class__.__name__)

    def __setitem__(self, key, value):
        # The input value must be a sequence type
        if not isinstance(value, GeomdlTypeSequence):
            raise TypeError("RHS must be a sequence")
        # If dimension is not set, try to find it
        if self.dimension < 1:
            self._dimension = len(value)
        # Always make sure that new input conforms with the existing dimension value
        if len(value) != self.dimension:
            raise ValueError("Input points must be " + str(self.dimension) + "-dimensional")
        if isinstance(key, int):
            self._cfg['func_pt_set'](self._pts, key, value)
            self._is_changed = True
            return
        if isinstance(key, tuple):
            if len(key) != len(self.size):
                raise ValueError("The n-dimensional indices must be equal to number of parametric dimensions")
            idx = self._cfg['func_find_index'](self.size, *key)
            self._cfg['func_pt_set'](self._pts, idx, value)
            self._is_changed = True
            return
        raise TypeError(self.__class__.__name__ + " indices must be integer or tuple, not " + key.__class__.__name__)

    def __getattr__(self, attr):
        try:
            idx = object.__getattribute__(self, 'PDIM_ATTRIBS').index(attr)
            return object.__getattribute__(self, '_size')[idx]
        except ValueError:
            raise AttributeError("'" + self.__class__.__name__ + "' object has no attribute '" + attr + "'")
        except AttributeError:
            return object.__getattribute__(self, attr)

    @property
    def points(self):
        """ Control points

        Please refer to the `wiki <https://github.com/orbingol/NURBS-Python/wiki/Using-Python-Properties>`_ for details
        on using this class member.

        :getter: Gets the control points (as a ``tuple``)
        :setter: Sets the control points
        """
        return tuple(self._pts)

    @points.setter
    def points(self, value):
        # Check input type
        if not isinstance(value, GeomdlTypeSequence):
            raise GeomdlError("Control points input must be a sequence")
        # Check input length
        if len(value) != self.count:
            raise GeomdlError("Number of control points must be " + str(self.count))
        # Determine dimension, if required
        if self.dimension < 1:
            self._dimension = len(value[0])
        # Set control points
        self._cfg['func_pts_set'](value, self.dimension, self._pts)
        self._is_changed = True

    @property
    def points_data(self):
        return self._ptsd

    @property
    def size(self):
        """ Number of the control points in all parametric dimensions

        Please refer to the `wiki <https://github.com/orbingol/NURBS-Python/wiki/Using-Python-Properties>`_ for details
        on using this class member.

        :getter: Gets the number of the control points (as a ``tuple``)
        """
        return self._size

    @property
    def count(self):
        """ Total number of the control points

        Please refer to the `wiki <https://github.com/orbingol/NURBS-Python/wiki/Using-Python-Properties>`_ for details
        on using this class member.

        :getter: Gets the total number of the control points (as an ``int``)
        """
        return self._count

    @property
    def is_changed(self):
        """ Flags changes in the current manager instance

        This flag is always false if there are no changes, e.g. add/update a control point. Otherwise, True

        Please refer to the `wiki <https://github.com/orbingol/NURBS-Python/wiki/Using-Python-Properties>`_ for details
        on using this class member.

        :getter: Gets the change status of the manager instance
        """
        return self._is_changed

    def reset(self, **kwargs):
        """ Resets the control points """
        # Call parent method
        super(CPManager, self).reset(**kwargs)
        # Reset the control points and the attached data
        self._cfg['func_pts_init'](self.count, **kwargs)

    def reset_changed(self):
        """ Resets 'is_changed' flag to False """
        self._is_changed = False

    def pt(self, *args):
        """ Gets the control point from the input position """
        return self[args]

    def set_pt(self, pt, *args):
        """ Puts the control point to the input position

        :param pt: control point
        :type pt: list, tuple
        """
        self[args] = pt
        self._is_changed = True

    def ptdata(self, dkey, *args):
        """ Gets the data attached to the control point

        :param dkey: key of the attachment dictionary
        :param dkey: str
        """
        # Find the index
        idx = self._cfg['func_find_index'](self.size, *args)
        # Return the attached data
        try:
            return self._ptsd[dkey][idx]
        except IndexError:
            return None
        except KeyError:
            return None

    def set_ptdata(self, adct, *args):
        """ Attaches the data to the control point

        :param adct: attachment dictionary
        :param adct: dict
        """
        # Find the index
        idx = self._cfg['func_find_index'](self.size, *args)
        # Attach the data to the control point
        try:
            for k, val in adct.items():
                if k in self._ptsd:
                    if isinstance(val, GeomdlTypeSequence):
                        for j, v in enumerate(val):
                            self._ptsd[k][idx][j] = v
                    else:
                        self._ptsd[k][idx] = val
                    self._is_changed = True
                else:
                    raise GeomdlError("Invalid key: " + str(k))
        except IndexError:
            raise GeomdlError("Index is out of range")
