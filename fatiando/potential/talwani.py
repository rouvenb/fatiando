"""
Calculate the gravitational attraction of a 2D body with polygonal vertical
cross-section using the formula of Talwani et al. (1959)

Use the :func:`~fatiando.mesher.dd.Polygon` object to create polygons.

.. warning:: the vertices must be given clockwise! If not, the result will have
    an inverted sign.

**Components**

* :func:`~fatiando.potential.talwani.gz`

**References**

Talwani, M., J. L. Worzel, and M. Landisman (1959), Rapid Gravity Computations
for Two-Dimensional Bodies with Application to the Mendocino Submarine
Fracture Zone, J. Geophys. Res., 64(1), 49-59, doi:10.1029/JZ064i001p00049.

----

"""
import numpy
from numpy import arctan2, pi, sin, cos, log, tan

# The gravitational constant (m^3*kg^-1*s^-1)
G = 0.00000000006673
# Conversion factor from SI units to mGal: 1 m/s**2 = 10**5 mGal
SI2MGAL = 100000.0


def gz(xp, zp, polygons):
    """
    Calculates the :math:`g_z` gravity acceleration component.

    .. note:: The coordinate system of the input parameters is z -> **DOWN**.

    .. note:: All input values in **SI** units(!) and output in **mGal**!

    Parameters:
    
    * xp, zp : arrays
        The x and z coordinates of the computation points.        
    * polygons : list of :func:`~fatiando.mesher.dd.Polygon`
        The density model used.
        Polygons must have the property ``'density'``. Polygons that don't have
        this property will be ignored in the computations. Elements of
        *polygons* that are None will also be ignored.

        .. note:: The y coordinate of the polygons is used as z! 

    Returns:
    
    * gz : array
        The :math:`g_z` component calculated on the computation points

    """
    if xp.shape != zp.shape:
        raise ValueError("Input arrays xp and zp must have same shape!")
    res = numpy.zeros_like(xp)
    # Extract the indexes of an array that have cond == True
    subset = lambda cond: [i for i, istrue in enumerate(cond) if istrue]
    for polygon in polygons:
        if polygon is None or 'density' not in polygon:
            continue
        density = polygon['density']
        x = polygon['x']
        z = polygon['y']
        nverts = len(polygon['x'])
        for v in xrange(nverts):
            # Change the coordinates of this vertice
            xv = x[v] - xp
            zv = z[v] - zp
            # The last vertice pairs with the first one
            if v == nverts - 1:
                xvp1 = x[0] - xp
                zvp1 = z[0] - zp
            else:
                xvp1 = x[v + 1]- xp
                zvp1 = z[v + 1] - zp                
            # Temporary fix. The analytical conditions for these limits don't
            # work. So if the conditions are breached, sum 0.01 meters to the
            # coodinates and be happy
            xv[subset(xv == 0.)] += 0.01
            xv[subset(xv == xvp1)] += 0.01
            zv[subset(zv[subset(xv == zv)] == 0.)] += 0.01
            zv[subset(zv == zvp1)] += 0.01
            zvp1[subset(zvp1[subset(xvp1 == zvp1)] == 0.)] += 0.01
            xvp1[subset(xvp1 == 0.)] += 0.01
            # End of fix
            phi_v = arctan2(zvp1 - zv, xvp1 - xv)
            ai = xvp1 + zvp1*(xvp1 - xv)/(zv - zvp1)
            theta_v = arctan2(zv, xv)
            theta_vp1 = arctan2(zvp1, xvp1)
            theta_v[subset(theta_v < 0)] += pi
            theta_vp1[subset(theta_vp1 < 0)] += pi
            tmp = ai*sin(phi_v)*cos(phi_v)*(
                    theta_v - theta_vp1 + tan(phi_v)*log(
                        (cos(theta_v)*(tan(theta_v) - tan(phi_v)))/
                        (cos(theta_vp1)*(tan(theta_vp1) - tan(phi_v)))))
            tmp[subset(theta_v == theta_vp1)] = 0.
            res = res + tmp*density
    res = res*SI2MGAL*2.0*G
    return res
