#!/usr/bin/env python

## -*-Pyth-*-
 # ###################################################################
 #  FiPy - Python-based finite volume PDE solver
 # 
 #  FILE: "mayaviSurfactantViewer.py"
 #                                    created: 7/29/04 {10:39:23 AM} 
 #                                last update: 8/2/05 {4:58:24 PM}
 #  Author: Jonathan Guyer <guyer@nist.gov>
 #  Author: Daniel Wheeler <daniel.wheeler@nist.gov>
 #  Author: James Warren   <jwarren@nist.gov>
 #    mail: NIST
 #     www: http://www.ctcms.nist.gov/fipy/
 #  
 # ========================================================================
 # This software was developed at the National Institute of Standards
 # and Technology by employees of the Federal Government in the course
 # of their official duties.  Pursuant to title 17 Section 105 of the
 # United States Code this software is not subject to copyright
 # protection and is in the public domain.  FiPy is an experimental
 # system.  NIST assumes no responsibility whatsoever for its use by
 # other parties, and makes no guarantees, expressed or implied, about
 # its quality, reliability, or any other characteristic.  We would
 # appreciate acknowledgement if the software is used.
 # 
 # This software can be redistributed and/or modified freely
 # provided that any derivative works bear some notice that they are
 # derived from it, and any modified versions bear some notice that
 # they have been modified.
 # ========================================================================
 #  
 #  Description: 
 # 
 #  History
 # 
 #  modified   by  rev reason
 #  ---------- --- --- -----------
 #  2003-11-12 JEG 1.0 original
 # ###################################################################
 ##

__docformat__ = 'restructuredtext'

from fipy.viewers.viewer import Viewer
import pyvtk
from fipy.tools import numerix

class MayaviSurfactantViewer(Viewer):
    
    """
    The `MayaviSurfactantViewer` creates a viewer with the Mayavi_ python
    plotting package that displays a `DistanceVariable`.

    .. _Mayavi: http://mayavi.sourceforge.net/

    """
        
    def __init__(self, distanceVar, surfactantVar = None, levelSetValue = 0., limits = None, title = None, smooth = 0, zoomFactor = 1.):
        """
        Create a `MayaviDistanceViewer`.
        
        :Parameters:

          - `distanceVar`: a `DistanceVariable` object.
          - `levelSetValue`: the value of the contour to be displayed
          - `limits`: a dictionary with possible keys `xmin`, `xmax`,
            `ymin`, `ymax`, `zmin`, `zmax`, `datamin`, `datamax`.  A 1D
            Viewer will only use `xmin` and `xmax`, a 2D viewer will also
            use `ymin` and `ymax`, and so on.  All viewers will use
            `datamin` and `datamax`.  Any limit set to a (default) value of
            `None` will autoscale.
          - `title`: displayed at the top of the Viewer window
        """

        Viewer.__init__(self, vars = [], limits = limits, title = title)
        import mayavi
        self._viewer = mayavi.mayavi()
        self.distanceVar = distanceVar
        if surfactantVar is None:
            self.surfactantVar = numerix.zeros(len(self.distanceVar), 'd')
        else:            
            self.surfactantVar = surfactantVar
        self.smooth = smooth
        self.zoomFactor = zoomFactor
        if distanceVar.getMesh().getDim() != 2:
            raise 'The MayaviIsoViewer only works for 2D meshes.'

    def _getStructure(self):

        maxX = max(self.distanceVar.getMesh().getFaceCenters()[:,0])
        minX = min(self.distanceVar.getMesh().getFaceCenters()[:,0])

        IDs = numerix.nonzero(self.distanceVar._getCellInterfaceFlag())
        coordinates = numerix.take(numerix.array(self.distanceVar.getMesh().getCellCenters()), IDs)
        coordinates -= numerix.take(self.distanceVar.getGrad() * self.distanceVar, IDs)
        coordinates *= self.zoomFactor

        shiftedCoords = coordinates.copy()
        shiftedCoords[:,0] = -coordinates[:,0] + (maxX - minX)
        coordinates = numerix.concatenate((coordinates, shiftedCoords))

        from lines import _getOrderedLines
        print min(self.distanceVar.getMesh()._getCellDistances()) * 3
        lines = _getOrderedLines(range(2 * len(IDs)), coordinates, thresholdDistance = min(self.distanceVar.getMesh()._getCellDistances()) * 10)

        data = numerix.take(self.surfactantVar, IDs)

        data = numerix.concatenate((data, data))

        tmpIDs = numerix.nonzero(data > 0.0001)
        if len(tmpIDs) > 0:
            val = min(numerix.take(data, tmpIDs))
        else:
            val = 0.0001
            
        data = numerix.where(data < 0.0001,
                             val,
                             data)

        
        for line in lines:
            if len(line) > 2: 
                for smooth in range(self.smooth):
                    for arr in (coordinates, data):
                        tmp = numerix.take(arr, line)
                        tmp[1:-1] = tmp[2:] * 0.25 + tmp[:-2] * 0.25 + tmp[1:-1] * 0.5
                        if len(arr.shape) > 1:
                            for i in range(len(arr[0])):                            
                                arrI = arr[:,i].copy()
                                numerix.put(arrI[:], line, tmp[:,i])
                                arr[:,i] = arrI
                        else:
                            numerix.put(arrI[:], line, tmp[:])

        return (pyvtk.UnstructuredGrid(points = coordinates,
                                       poly_line = lines),
                pyvtk.PointData(pyvtk.Scalars(data)))
        
    def plot(self, filename = None):

        structure, data = self._getStructure()
        data = pyvtk.VtkData(structure, data)

        import tempfile
        (f, tempFileName) = tempfile.mkstemp('.vtk')
        data.tofile(tempFileName)
        self._viewer.open_vtk(tempFileName, config=0)

        import os
        os.close(f)
        os.remove(tempFileName)
        self._viewer.load_module('SurfaceMap', 0)
        rw = self._viewer.get_render_window()
        rw.z_plus_view()

        ## display legend
        dvm = self._viewer.get_current_dvm()
        mm = dvm.get_current_module_mgr()
        slh = mm.get_scalar_lut_handler()
        slh.legend_on.set(1)
        slh.legend_on_off()
        
        ## display legen with correct range
        slh.range_on_var.set(1)
        slh.v_range_on_var.set(1)
        
        xmax = self._getLimit('datamax')
        if xmax is None:
            xmax = max(self.surfactantVar)
            
        xmin = self._getLimit('datamin')
        if xmin is None:
            xmin = min(self.surfactantVar)
            
        slh.range_var.set((xmin, xmax))
        slh.set_range_var()
        
        slh.v_range_var.set((min(self.surfactantVar), max(self.surfactantVar)))
        slh.set_v_range_var()
        
        self._viewer.Render()
        
        if filename is not None:
            self._viewer.renwin.save_png(filename)

if __name__ == '__main__':
    dx = 1.
    dy = 1.
    nx = 11
    ny = 11
    Lx = ny * dy
    Ly = nx * dx
    from fipy.meshes.grid2D import Grid2D
    mesh = Grid2D(dx = dx, dy = dy, nx = nx, ny = ny)
    from fipy.models.levelSet.distanceFunction.distanceVariable import DistanceVariable
    var = DistanceVariable(mesh = mesh, value = -1)
    positiveCells = mesh.getCells(filter = lambda cell: (cell.getCenter()[0] - Lx / 2.)**2 + (cell.getCenter()[1] - Ly / 2.)**2 < (Lx / 4.)**2)
    
    var.setValue(1, positiveCells)
    var.calcDistanceFunction()
    viewer = MayaviSurfactantViewer(var, smooth = 2)
    viewer.plot()
    raw_input("press key to continue")

    var = DistanceVariable(mesh = mesh, value = -1)
    positiveCells = mesh.getCells(filter = lambda cell: cell.getCenter()[1] > 2. * Ly / 3. or (cell.getCenter()[0] > Lx / 2. and cell.getCenter()[1] > Ly / 3.) or (cell.getCenter()[1] < Ly / 6. and cell.getCenter()[0] > Lx / 2))
    var.setValue(1, positiveCells)
    var.calcDistanceFunction()
    viewer = MayaviSurfactantViewer(var)
    viewer.plot()
    raw_input("press key to continue")

    viewer = MayaviSurfactantViewer(var, smooth = 2)
    viewer.plot()