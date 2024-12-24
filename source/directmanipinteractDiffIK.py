import os,sys, math, time
import re
import numpy
numpy.set_printoptions(precision=2)
from numpy import linalg
from numpy.linalg import inv

import maya.cmds as cmds
import maya.mel as mel
import maya.utils as utils
import maya.OpenMaya as OM
import maya.OpenMayaAnim as OMA

cmds.loadPlugin( 'dmPinConnectorDiffIK.py' )

verbose = 0
if verbose: print 'zmaya jan11'

def selCB():
    sel = cmds.ls( selection=True )
    vertCB(sel)
    
cmds.scriptJob( event = ["SelectionChanged", selCB] )

def setloc(thename,pointName):
    tran = cmds.pointPosition(pointName,w=True)
    cmds.setAttr(thename+'.tx', tran[0]) 
    cmds.setAttr(thename+'.ty', tran[1]) 
    cmds.setAttr(thename+'.tz', tran[2])
    
def createMaterial( name, color, type ):
    cmds.sets( renderable=True, noSurfaceShader=True, empty=True, name=name + 'SG' )
    cmds.shadingNode( type, asShader=True, name=name )
    cmds.setAttr( name+".color", color[0], color[1], color[2], type='double3')
    cmds.connectAttr(name+".outColor", name+"SG.surfaceShader")

def assignMaterial (name, object):
    cmds.sets(object, edit=True, forceElement=name+'SG')

def assignNewMaterial( name, color, type, object):
    createMaterial (name, color, type)
    assignMaterial (name, object)
    
def getPinnedPointPositions(sliders):
    npins = pinsCount()
    if verbose: print 'getPinnedPointPositions found %d active pins' % npins
    R = numpy.zeros((2*npins,len(sliders)))
    iip = 0
    for ip in Pins:
	if not ip.isactive(): continue
        R[iip:iip+2,:] = ip.R
	iip = iip + 2
    return numpy.mat(R)

def getMouse():
    npins = pinsCount()
    m = numpy.zeros((2*npins,1))
    iip = 0
    for ip in Pins:
	if not ip.isactive(): continue
	if verbose: print 'getting translate for ',ip.geom
	nx = cmds.getAttr(ip.geom+".tx") 
	ny = cmds.getAttr(ip.geom+".ty") 
	nz = cmds.getAttr(ip.geom+".tz")
	if verbose: print 'getmouse nxyz = ',nx,ny,nz
	newloc = numpy.array([nx,ny,nz])
	newloc = getRelevantDimensions(newloc)
	newloc = numpy.array(newloc)
	newloc = newloc - ip.neutral
	newloc = newloc.reshape(2,1)
	if verbose: print 'm.shape, newloc.shape',m.shape,newloc.shape
	if verbose: print 'iip = ',iip
	m[iip:iip+2,0] = newloc[:,0]
	iip = iip + 2
    if verbose: print 'm = ',m.T
    return numpy.mat(m)

def mkLS(R):
    def solve(movedpoint):
	if verbose: print 'solveLS'
	w1 = R.T * movedpoint
	return w1
    return solve

def setsliders(w):
    ie = 0
    for slider in Sliders:
	val = w[ie,0]
	if val >= 1: 
	    val = 1 
	if val <= 0: 
	    val = 0 
	cmds.setAttr(slider, val)
	cmds.setKeyframe(slider)
	ie = ie + 1

def getsliders():
  w = numpy.zeros((len(Sliders),1))
  ie = 0
  for slider in Sliders:
    w[ie] = cmds.getAttr(slider)
    ie = ie + 1
  return w

def zeroAllsliders():
    for slider in Allsliders:
	    cmds.setAttr(slider, 0.)
	    cmds.setKeyframe(slider)

Pins = []

createMaterial('pinShaderGreen',(0.2,0.6,0.1),'lambert')
createMaterial('pinShaderRed',(0.6,0.2,0.1),'lambert')

class Pin():
    geomname = -1
    pointname = -1
    istarget = 0		
    neutral = -1
    R = -1
    
    suffixes = ['0','1','2','3','4','5','6','7','8','9','10','11']
        
    sufidx = 0
    
    @staticmethod
    def reset():
	for ip in Pins:
	    cmds.delete(ip.geom)
	for i in range(len(Pins)):
	    del Pins[0]
	Pin.sufidx = 0
	assert len(Pins)==0    

    def __init__(self, pntname, exists=False):
	idxHeat = int(re.search(r'\d+', pntname).group())
	suffix = Pin.suffixes[Pin.sufidx]
			
	Pin.sufidx = Pin.sufidx + 1
		
	if verbose: print 'creating pin %s %s' % (suffix,pntname)
		
	if not exists:
	    self.geomname = 'pullme%s' % suffix
	    self.pointname = pntname
	    if verbose: print 'making pin %s %s' % (self.geomname, self.pointname)
	    thesize = 1.5 * TheModel['FaceSize']
	    if verbose: print 'pin radiussssssssssssssssssssssssssssssssssssssssssssssssssssssssss = ',thesize
	    self.geom = cmds.sphere(name=self.geomname, r=thesize)
	    cmds.snapMode( q=True, point=True )
	    self.geom = self.geom[0]
	    cmds.addAttr(longName='isactive',storable=True,keyable=1,attributeType='bool')
	    cmds.addAttr(longName='istarget',storable=True,keyable=1,attributeType='bool')
	    	    
	    cmds.addAttr(dataType='string',storable=1,longName='pointname')
	    cmds.setAttr('%s.isactive' % self.geom, 0)
	    cmds.setAttr('%s.istarget' % self.geom, 0)
	    cmds.setAttr('%s.pointname' % self.geom, self.pointname, type='string')
			
	else:
	    self.geom = exists
	    self.geomname = exists
	    self.istarget = cmds.getAttr('%s.istarget' % self.geom)
	    self.pointname = cmds.getAttr('%s.pointname' % self.geom)	    
	    	    
	    	   	    	
	cmds.select(self.geom)
	setloc(self.geom,pntname)
	
	self.neutral = cmds.pointPosition(pntname,w=True)
	self.neutral = getRelevantDimensions(self.neutral)
	self.neutral = numpy.array(self.neutral)
	
					
	saveW = getsliders()
	self.R = numpy.zeros((2,len(Sliders)))
	ie = 0
	start = time.time()
	for attr in Sliders:
	    magP = 0
	    if verbose > 1 : print 'attr', attr, Sliders[ie]
	    setsliders(saveW)
	    cmds.setAttr(Sliders[ie],1)
	    p = cmds.pointPosition(self.pointname,w=True)
	    p = getRelevantDimensions(p)
	    p = numpy.array(p)
	    p = p - self.neutral
	    p = p.reshape(2,1)
	    self.R[:,ie] = p[:,0]
	    ie = ie + 1
	setsliders(saveW)
	end = time.time()
	print "pin creation time in seconds", end - start
            
    def setactivecolor(self):
	assignMaterial('pinShaderGreen',self.geom)    

    def settargetcolor(self):
	assignMaterial('pinShaderRed',self.geom)	

    def isactive(self):
	return cmds.getAttr('%s.isactive' % self.geom)
    
    def setactive(self,isactive):
	cmds.setAttr('%s.isactive' % self.geom, isactive)
	if not isactive:
	    cmds.setAttr('%s.tx' % self.geomname, 1000)
	else:
	    pass
	
    def settarget(self,istarget):
	self.istarget = istarget
	cmds.setAttr('%s.istarget' % self.geom, istarget)
	if istarget:
	    cmds.setAttr('%s.isactive' % self.geom, 1)
	    assignMaterial('pinShaderRed',self.geom)
	else:
	    if verbose: print 'setting to green'
	    assignMaterial('pinShaderGreen',self.geom)    
	    
def pinsCount():
    npins = 0
    for ip in Pins:
	if ip.isactive():
	    npins = npins + 1
    if verbose: print 'pinsCount found %d active pins' % npins
    return npins


GlobalsSet = False
TheModel = None
getRelevantDimensions = None
Sliders = None
Allsliders = None
Nw = None
Lvals = None
L = None
ModelsWithBlendShapeDeformers = None 


def setglobals():
  if verbose: print 'setglobals'
  global GlobalsSet
  global TheModel,getRelevantDimensions,Sliders,Allsliders,Nw,Lvals,L,ModelsWithBlendShapeDeformers 
  
  def getRelevantDimensions(vec):
      return [vec[0],vec[1]]		
  
  GirlNurbs = {}
  GirlNurbs['relevantdimensions'] = getRelevantDimensions
  
    
  GirlNurbs['ignoresliders'] = []
  for iw in range(999):		
      GirlNurbs['ignoresliders'].append('weight[%d]' % iw)
      GirlNurbs['ignoresliders'].append('hirokigirlEXP_ALL_12_tri_wlessBS_new:weight[%d]' % iw) 
  GirlNurbs['ignoresliders'].append('parallelBlender')
  GirlNurbs['ignoresliders'].append('hirokigirlEXP_ALL_12_tri_wlessBS_new:parallelBlender') 
  GirlNurbs['ignoresliders'].append('parallelBlender1')
  GirlNurbs['ignoresliders'].append('hirokigirlEXP_ALL_12_tri_wlessBS_new:parallelBlender1') 
  
  
  def getslidernames():
      if verbose: print 'GirlInfo.getsidernames()'
      sliders = []
      allsliders = []
      ignore = GirlNurbs['ignoresliders']
      if verbose: print 'ignore list:',ignore
      slidergroups = cmds.ls(type='blendShape')
      for slidergroup in slidergroups:
	  if slidergroup in ignore:
	      if verbose: print 'Ignoring Group: ',slidergroup
	      continue		
	  if verbose: print 'slidergroup', slidergroup
	  gsliders = cmds.aliasAttr(slidergroup,q=True)
	  for slider in gsliders:
	      allsliders.append(slidergroup +'.'+ slider)
	      if not slider in ignore:
		 sliders.append(slidergroup +'.'+ slider)
      if verbose: print 'sliders', sliders
      if verbose: print 'allsliders', allsliders
      return sliders,allsliders
  
  GirlNurbs['getslidernames'] = getslidernames
  GirlNurbs['FaceSize'] = 0.3	
  
  GirlNurbs['ProjDir'] = '-z'
  TheModel = GirlNurbs

  getRelevantDimensions = TheModel['relevantdimensions']
  Sliders,Allsliders = TheModel['getslidernames']()
  if verbose: print len(Sliders),'sliders:',Sliders
  Nw = len(Sliders)
    
  zeroAllsliders()
    
setglobals()

DoPCA = False
if verbose: print 'importing vertexSelecter, DoPCA = ', DoPCA
verbose = 0

gSelVerts = {}		
gPins = []		
			

gCurpin = None

sal = -1

selep = []
pinCon = ['dmPinConnector1','dmPinConnector2','dmPinConnector3','dmPinConnector4','dmPinConnector5','dmPinConnector6','dmPinConnector7','dmPinConnector8','dmPinConnector9','dmPinConnector10','dmPinConnector11','dmPinConnector12']
pinkey = 0

w0 = numpy.zeros((Nw,1))

def reset():
    global gCurpin, gPins, gSelVerts, selep, pinkey
    gSelVerts = {}
    gPins = []
    gCurpin = None
    pinkey = 0

def vertCB(sel):
    global gCurpin, pinkey
    if verbose: print 'vertexSelecter HI THERE:  ', sel
    sel = cmds.ls(sl=True)  
    if verbose: print 'vertselCB sel=',sel
    
    if len(sel) == 0:
	if verbose: print 'vertselCB nothing selected, ignoring'
	return
	
    sel = sel[0]

    isVertex = False
    idx1 = sel.find('.cv')	
    idx2 = sel.find('.vtx')	
    if (idx1 >= 0)   or   (idx2 >= 0):
      isVertex = True
    else:
      if verbose: print 'vertselCB not a vertex: ',sel
      

    if sel in gSelVerts:
    
      raise 'already selected'
    elif sel in gPins:
      if verbose: print 'comparing ',sel,gPins
      if verbose: print 'pin already selected'
      gCurpin = sel
      pinindex = gPins.index(sel)
      if verbose: print 'pin name ', gCurpin
      for ip in Pins:
        if ip.geom == sel:
          ip.settarget(1)
        else:
          ip.settarget(0)
      cmds.select(pinCon[pinindex], add = True)
    elif isVertex:
      if verbose: print 'vertselCB newly selected ', sel
      thepin = Pin(sel)
      thepin.setactive(1)
      thepin.settarget(0)
      if verbose: print 'cccccccccccccccccccccccc'
      gSelVerts[sel] = thepin
      gPins.append(thepin.geomname)
      Pins.append(thepin)
      gCurpin = thepin.geomname
      if verbose: print 'pin name ', gCurpin
      cmds.createNode ('dmPinConnector')	  
      cmds.connectAttr(gCurpin+'.tx', pinCon[pinkey]+'.Tx')
      cmds.connectAttr(gCurpin+'.ty', pinCon[pinkey]+'.Ty')
      cmds.select(pinCon[pinkey], add = True) 
      pinkey = pinkey + 1
      mel.eval('setToolTo moveSuperContext;')		  
    else:
      if verbose: print 'vertselCB ignoring', sel
      pass

def dragCB():
  R = getPinnedPointPositions(Sliders)
  solver = mkLS(R)
  movedpoint = getMouse()
  w = solver(movedpoint)
  setsliders(w)