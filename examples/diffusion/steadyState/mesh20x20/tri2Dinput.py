#!/usr/bin/env python

## 
 # ###################################################################
 #  FiPy - Python-based finite volume PDE solver
 # 
 #  FILE: "ttri2Dinput.py"
 #                                    created: 12/29/03 {3:23:47 PM}
 #                                last update: 4/4/05 {3:10:49 PM} 
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
 #  2003-11-10 JEG 1.0 original
 # ###################################################################
 ##

"""

This input file again solves a 2D diffusion problem on a triangular mesh.

    >>> ImplicitDiffusionTerm().solve(var, boundaryConditions = boundaryConditions)

The result is again tested in the same way:

    >>> Lx = nx * dx
    >>> x = mesh.getCellCenters()[:,0]
    >>> analyticalArray = valueLeft + (valueRight - valueLeft) * x / Lx
    >>> print var.allclose(analyticalArray)
    1

"""

from fipy.meshes.numMesh.tri2D import Tri2D
from fipy.boundaryConditions.fixedValue import FixedValue
from fipy.variables.cellVariable import CellVariable
import fipy.viewers
from fipy.terms.implicitDiffusionTerm import ImplicitDiffusionTerm

nx = 20
ny = 20

dx = 1.

valueLeft = 0.
valueRight = 1.

mesh = Tri2D(dx = dx, nx = nx, ny = ny)

var = CellVariable(name = "solution variable",
                   mesh = mesh,
                   value = valueLeft)

viewer = fipy.viewers.make(vars = var)

boundaryConditions = (FixedValue(mesh.getFacesLeft(),valueLeft),
                      FixedValue(mesh.getFacesRight(),valueRight))

if __name__ == '__main__':
    ImplicitDiffusionTerm().solve(var, boundaryConditions = boundaryConditions)
    viewer.plot()
    raw_input("finished")
