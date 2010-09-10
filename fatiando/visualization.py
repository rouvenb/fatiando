# Copyright 2010 Leonardo Uieda
#
# This file is part of Fatiando a Terra.
#
# Fatiando a Terra is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Fatiando a Terra is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Fatiando a Terra.  If not, see <http://www.gnu.org/licenses/>.
"""
Collection of plotting functions. Uses Matplotlib for 2D and Mayavi2 for 3D.
"""
__author__ = 'Leonardo Uieda (leouieda@gmail.com)'
__date__ = 'Created 01-Sep-2010'


import pylab
import numpy
from enthought.mayavi import mlab
from enthought.tvtk.api import tvtk


def plot_prism(prism):
        
    vtkprism = tvtk.RectilinearGrid()
    vtkprism.cell_data.scalars = [prism.dens]
    vtkprism.cell_data.scalars.name = 'Density'
    vtkprism.dimensions = (2, 2, 2)
    vtkprism.x_coordinates = [prism.x1, prism.x2]
    vtkprism.y_coordinates = [prism.y1, prism.y2]
    vtkprism.z_coordinates = [prism.z1, prism.z2]    
        
    source = mlab.pipeline.add_dataset(vtkprism)
    outline = mlab.pipeline.outline(source)
    outline.actor.property.line_width = 4
    outline.actor.property.color = (1,1,1)