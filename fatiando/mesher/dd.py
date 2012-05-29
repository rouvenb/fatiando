"""
Create and operate on 2D meshes and objects like polygons, squares, and
triangles.

**Elements**

* :func:`~fatiando.mesher.dd.Polygon`
* :func:`~fatiando.mesher.dd.Square`

**Meshes**

* :class:`~fatiando.mesher.dd.SquareMesh`

**Utility functions**

* :func:`~fatiando.mesher.dd.square2polygon`

----

"""

import PIL.Image
import numpy
import scipy.misc

from fatiando import logger, gridder


log = logger.dummy('fatiando.mesher.dd')

def Polygon(vertices, props=None):
    """
    Create a polygon object.

    .. note:: Most applications require the vertices to be **clockwise**!

    Parameters:

    * vertices : list of lists
        List of [x, y] pairs with the coordinates of the vertices.        
    * props : dict
        Physical properties assigned to the polygon.
        Ex: ``props={'density':10, 'susceptibility':10000}``

    Returns:

    * polygon : dict
        A polygon
    
    """    
    x, y = numpy.array(vertices, dtype='f').T
    poly = {'x':x, 'y':y}
    if props is not None:
        for prop in props:
            poly[prop] = props[prop]
    return poly

def Square(bounds, props=None):
    """
    Create a square object.


    Parameters:

    * bounds : list = [x1, x2, y1, y2]
        Coordinates of the top right and bottom left corners of the square       
    * props : dict
        Physical properties assigned to the square.
        Ex: ``props={'density':10, 'slowness':10000}``

    Returns:

    * square : dict
        A square
    
    Example::

        >>> from fatiando.mesher.dd import Square
        >>> sq = Square([0, 1, 2, 4], {'density':750})
        >>> for k in sorted(sq):
        ...     print k, '=', sq[k]
        density = 750
        x1 = 0
        x2 = 1
        y1 = 2
        y2 = 4
    
    """
    x1, x2, y1, y2 = bounds
    square = {'x1':x1, 'x2':x2, 'y1':y1, 'y2':y2}
    if props is not None:
        for prop in props:
            square[prop] = props[prop]
    return square

class SquareMesh(object):
    """
    Generate a 2D regular mesh of squares.

    For all purposes, :class:`~fatiando.mesher.dd.SquareMesh` can be used as a
    list of :func:`~fatiando.mesher.dd.Square`. The order of the squares in the
    list is: x directions varies first, then y.

    Parameters:

    * bounds :  list = [x1, x2, y1, y2]
        Boundaries of the mesh
    * shape : tuple = (ny, nx)
        Number of squares in the y and x dimension, respectively
    * props : dict
        Physical properties of each square in the mesh.
        Each key should be the name of a physical property. The corresponding
        value should be a list with the values of that particular property on
        each square of the mesh.
        
    Examples:

        >>> from fatiando.mesher.dd import SquareMesh
        >>> def show(p):
        ...     print ' | '.join('%s : %.1f' % (k, p[k]) for k in sorted(p))
        >>> mesh = SquareMesh((0, 4, 0, 6), (2, 2))
        >>> for s in mesh:
        ...     show(s)
        x1 : 0.0 | x2 : 2.0 | y1 : 0.0 | y2 : 3.0
        x1 : 2.0 | x2 : 4.0 | y1 : 0.0 | y2 : 3.0
        x1 : 0.0 | x2 : 2.0 | y1 : 3.0 | y2 : 6.0
        x1 : 2.0 | x2 : 4.0 | y1 : 3.0 | y2 : 6.0
        >>> show(mesh[1])
        x1 : 2.0 | x2 : 4.0 | y1 : 0.0 | y2 : 3.0
        >>> show(mesh[-1])
        x1 : 2.0 | x2 : 4.0 | y1 : 3.0 | y2 : 6.0
        
    With physical properties::

        >>> def show(p):
        ...     print ' | '.join('%s : %.1f' % (k, p[k]) for k in sorted(p))
        >>> props = {'slowness':[3.4, 8.6]}
        >>> mesh = SquareMesh((0, 4, 0, 6), (2, 1), props)
        >>> for s in mesh:
        ...     show(s)
        slowness : 3.4 | x1 : 0.0 | x2 : 4.0 | y1 : 0.0 | y2 : 3.0
        slowness : 8.6 | x1 : 0.0 | x2 : 4.0 | y1 : 3.0 | y2 : 6.0

    Or::

        >>> def show(p):
        ...     print ' | '.join('%s : %.1f' % (k, p[k]) for k in sorted(p))
        >>> mesh = SquareMesh((0, 4, 0, 6), (2, 1))
        >>> mesh.addprop('slowness', [3.4, 8.6])
        >>> for s in mesh:
        ...     show(s)
        slowness : 3.4 | x1 : 0.0 | x2 : 4.0 | y1 : 0.0 | y2 : 3.0
        slowness : 8.6 | x1 : 0.0 | x2 : 4.0 | y1 : 3.0 | y2 : 6.0
        
    """

    def __init__(self, bounds, shape, props=None):
        object.__init__(self)
        log.info("Generating 2D regular square mesh:")
        ny, nx = shape
        size = int(nx*ny)
        x1, x2, y1, y2 = bounds
        dx = float(x2 - x1)/nx
        dy = float(y2 - y1)/ny
        self.bounds = bounds
        self.shape = tuple(int(i) for i in shape)
        self.size = size
        self.dims = (dx, dy)
        # props has to be None, not {} by default because {} would be permanent
        # for all instaces of the class (like a class variable) and changes
        # to one instace would lead to changes in another (and a huge mess)
        if props is None:
            self.props = {}
        else:
            self.props = props
        log.info("  bounds = (x1, x2, y1, y2) = %s" % (str(bounds)))
        log.info("  shape = (ny, nx) = %s" % (str(shape)))
        log.info("  number of squares = %d" % (size))
        log.info("  square dimensions = (dx, dy) = %s" % (str(self.dims)))
        # The index of the current square in an iteration. Needed when mesh is
        # used as an iterator
        self.i = 0
        # List of masked squares. Will return None if trying to access them
        self.mask = []    
        
    def __len__(self):
        return self.size

    def __getitem__(self, index):
        # To walk backwards in the list
        if index < 0:
            index = self.size + index
        if index in self.mask:
            return None
        ny, nx = self.shape
        j = index/nx
        i = index - j*nx
        x1 = self.bounds[0] + self.dims[0]*i
        x2 = x1 + self.dims[0]
        y1 = self.bounds[2] + self.dims[1]*j
        y2 = y1 + self.dims[1]
        props = dict([p, self.props[p][index]] for p in self.props)
        return Square((x1, x2, y1, y2), props=props)

    def __iter__(self):
        self.i = 0
        return self

    def next(self):
        if self.i >= self.size:
            raise StopIteration
        square = self.__getitem__(self.i)
        self.i += 1
        return square

    def addprop(self, prop, values):
        """
        Add physical property values to the cells in the mesh.

        Different physical properties of the mesh are stored in a dictionary.

        Parameters:
        
        * prop : str
            Name of the physical property
        * values : list or array
            The value of this physical property in each square of the mesh.
            For the ordering of squares in the mesh see
            :class:`~fatiando.mesher.dd.SquareMesh`
            
        """
        self.props[prop] = values

    def img2prop(self, fname, vmin, vmax, prop):
        """
        Load the physical property value from an image file.

        The image is converted to gray scale and the gray intensity of each
        pixel is used to set the value of the physical property of the
        cells in the mesh. Gray intensity values are scaled to the range
        ``[vmin, vmax]``.

        If the shape of image (number of pixels in y and x) is different from
        the shape of the mesh, the image will be interpolated to match the shape
        of the mesh. 

        Parameters:

        * fname : str
            Name of the image file
        * vmax, vmin : float
            Range of physical property values (used to convert the gray scale to
            physical property values)
        * prop : str
            Name of the physical property
            
        """
        log.info("Loading physical property from image file:")
        log.info("  file: '%s'" % (fname))
        log.info("  physical property: %s" % (prop))
        log.info("  range: [vmin, vmax] = %s" % (str([vmin, vmax])))
        image = PIL.Image.open(fname)
        imagearray = scipy.misc.fromimage(image, flatten=True)
        # Invert the color scale
        model = numpy.max(imagearray) - imagearray
        # Normalize
        model = model/numpy.max(numpy.abs(imagearray))
        # Put it in the interval [vmin,vmax]
        model = model*(vmax - vmin) + vmin
        # Convert the model to a list so that I can reverse it (otherwise the
        # image will be upside down)
        model = model.tolist()
        model.reverse()
        model = numpy.array(model)
        log.info("  image shape: (ny, nx) = %s" % (str(model.shape)))
        # Check if the shapes match, if not, interpolate
        if model.shape != self.shape:
            log.info("  interpolate image to match mesh shape")
            ny, nx = model.shape
            xs = numpy.arange(nx)
            ys = numpy.arange(ny)
            X, Y = numpy.meshgrid(xs, ys)
            model = gridder.interp(X.ravel(), Y.ravel(), model.ravel(),
                                   self.shape)[2]
            log.info("  new image shape: (ny, nx) = %s" % (str(model.shape)))
        self.props[prop] = model.ravel()

    def get_xs(self):
        """
        Get a list of the x coordinates of the corners of the cells in the
        mesh.

        If the mesh has nx cells, get_xs() will return nx + 1 values.
        """
        dx, dy = self.dims
        x1, x2, y1, y2 = self.bounds
        ny, nx = self.shape
        xs = numpy.arange(x1, x2 + dx, dx, 'f')
        if len(xs) == nx + 2:
            return xs[0:-1]
        elif len(xs) == nx:
            xs = xs.tolist()
            xs.append(x2)
            return numpy.array(xs)
        else:
            return xs
        
    def get_ys(self):
        """
        Get a list of the y coordinates of the corners of the cells in the
        mesh.

        If the mesh has ny cells, get_ys() will return ny + 1 values.
        """
        dx, dy = self.dims
        x1, x2, y1, y2 = self.bounds
        ny, nx = self.shape
        ys = numpy.arange(y1, y2, dy, 'f')
        if len(ys) == ny + 2:
            return ys[0:-1]
        elif len(ys) == ny:
            ys = ys.tolist()
            ys.append(y2)
            return numpy.array(ys)
        else:
            return ys

def square2polygon(square):
    """
    Convert a square into a polygon.

    Vertices are ordered clockwise considering that x is North.

    Parameters:

    * square : :func:`~fatiando.mesher.dd.Square`
        A square

    Returns:

    * polygon : :func:`~fatiando.mesher.dd.Polygon`
        The polygon equivalente of *square*

    Example::

        >>> from fatiando.mesher.dd import Square, square2polygon
        >>> square = Square((0, 1, 0, 3), {'vp':1000})
        >>> poly = square2polygon(square)
        >>> print poly['x']
        [ 0.  1.  1.  0.]
        >>> print poly['y']
        [ 0.  0.  3.  3.]
        >>> print poly['vp']
        1000
        
    """
    verts = [[square['x1'], square['y1']], [square['x2'], square['y1']],
             [square['x2'], square['y2']], [square['x1'], square['y2']]]
    notprops = ['x1', 'x2', 'y1', 'y2']
    props = dict([p, square[p]] for p in square if p not in notprops)
    return Polygon(verts, props)
