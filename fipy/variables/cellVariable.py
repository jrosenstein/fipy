## -*-Pyth-*-
 # ###################################################################
 #  PFM - Python-based phase field solver
 # 
 #  FILE: "CellVariable.py"
 #                                    created: 12/9/03 {2:03:28 PM} 
 #                                last update: 12/10/03 {10:27:52 AM} 
 #  Author: Jonathan Guyer
 #  E-mail: guyer@nist.gov
 #    mail: NIST
 #     www: http://ctcms.nist.gov
 #  
 # ========================================================================
 # This software was developed at the National Institute of Standards
 # and Technology by employees of the Federal Government in the course
 # of their official duties.  Pursuant to title 17 Section 105 of the
 # United States Code this software is not subject to copyright
 # protection and is in the public domain.  PFM is an experimental
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
 #  See the file "license.terms" for information on usage and  redistribution
 #  of this file, and for a DISCLAIMER OF ALL WARRANTIES.
 #  
 # ###################################################################
 ##

from variable import Variable
import Numeric
import meshes.tools

class CellVariable(Variable):
    def __init__(self, mesh, name = '', value=0., viewer = None, hasOld = True):
	array = Numeric.zeros([len(mesh.getCells())],'d')
	array[:] = value
	
	if viewer is not None:
	    self.viewer = viewer(var = self)
	else:
	    self.viewer = None
	    
	Variable.__init__(self, mesh, name = name, value = array)
	
	if hasOld:
	    self.old = self.copy()
	else:
	    self.old = None

    def copy(self):
	if self.viewer is None:
	    viewer = None
	else:
	    viewer = self.viewer.__class__
	    
	return CellVariable(
	    mesh = self.mesh, 
	    name = self.name + "_old", 
	    value = self.getValue(),
	    viewer = viewer,
	    hasOld = False)

    def plot(self):
	if self.viewer != None:
	    self.viewer.plot()
	
    def getGridArray(self):
	return self.mesh.makeGridData(self.value)
	
    def setValue(self,value,cells = ()):
	if cells == ():
	    if type(value) == type(Numeric.array((1.))):
		self.value[:] = value[:]
	    elif type(value) in [type(1.),type(1)]:
		self.value[:] = value
	    else:
		raise TypeError, str(value) + " is not numeric or a Numeric.array"
	else:
	    for cell in cells:
		self.value[cell.getId()] = value
		
    def getGrad(self):
	areas = self.mesh.getAreaProjections()
	faceValues = Numeric.reshape(self.getFaceValue(), (len(areas),1))
	faceGradientContributions = areas * faceValues
	
	N = len(self.value)
	M = self.mesh.getMaxFacesPerCell()
	
	ids = self.mesh.getCellFaceIDs()

	contributions = Numeric.take(faceGradientContributions, ids)
	contributions = Numeric.reshape(contributions,(N,M,self.mesh.getDim()))

	orientations = self.mesh.getCellFaceOrientations()

	grad = Numeric.sum(orientations*contributions,1)

	volumes = self.mesh.getCellVolumes()
	volumes = Numeric.reshape(volumes, Numeric.shape(volumes)+(1,))
	grad = grad/volumes

	return grad
    
    def getGradMag(self):
	grad = self.getGrad()
	return meshes.tools.arraySqrtDot(grad,grad)	

    def getFaceValue(self):
	dAP = self.mesh.getCellDistances()
	dFP = self.mesh.getFaceToCellDistances()
	alpha = dFP / dAP
	id1, id2 = self.mesh.getAdjacentCellIDs()
	return Numeric.take(self[:], id1) * alpha + Numeric.take(self[:], id2) * (1 - alpha)
	    
    def getFaceGrad(self):
	dAP = self.mesh.getCellDistances()
	id1, id2 = self.mesh.getAdjacentCellIDs()
	N = (Numeric.take(self[:], id2) - Numeric.take(self[:], id1))/dAP
	normals = self.mesh.getFaceNormals().copy()
	normals *= Numeric.reshape(self.mesh.getFaceOrientations(),(len(normals),1))
	tangents1 = self.mesh.getFaceTangents1()
	tangents2 = self.mesh.getFaceTangents2()
	cellGrad = self.getGrad()
	grad1 = Numeric.take(cellGrad, id1)
	grad2 = Numeric.take(cellGrad, id2)
	t1grad1 = Numeric.sum(tangents1*grad1,1)
	t1grad2 = Numeric.sum(tangents1*grad2,1)
	t2grad1 = Numeric.sum(tangents2*grad1,1)
	t2grad2 = Numeric.sum(tangents2*grad2,1)
	T1 = (t1grad1 + t1grad2) / 2.
	T2 = (t2grad1 + t2grad2) / 2.
	
	N = Numeric.reshape(N, (len(normals),1)) 
	T1 = Numeric.reshape(T1, (len(normals),1)) 
	T2 = Numeric.reshape(T2, (len(normals),1)) 

	return normals * N + tangents1 * T1 + tangents2 * T2

    def getOld(self):
	if self.old == None:
	    return self
	else:
	    return self.old

    def updateOld(self):
	if self.old != None:
	    self.old.setValue(self.value)
	    
