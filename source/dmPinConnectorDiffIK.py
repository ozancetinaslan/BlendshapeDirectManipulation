import math, sys

import maya.OpenMaya as OM
import maya.OpenMayaMPx as OMPx

import directmanipinteractDiffIK as DM

kPluginNodeTypeName = "dmPinConnector"

dmPinConnectorId = OM.MTypeId(0x87001)

class dmPinConnector(OMPx.MPxNode):
	input = OM.MObject()
	aTx = OM.MObject()
	aTy = OM.MObject()
	output = OM.MObject()
	

	def __init__(self):
		OMPx.MPxNode.__init__(self)

	def compute(self,plug,dataBlock):
		if ( plug == dmPinConnector.output ):

			tx = dataBlock.inputValue( self.aTx ).asDouble()
			ty = dataBlock.inputValue( self.aTy ).asDouble()
						
			DM.dragCB()
						
			result = 1.
			outputHandle = dataBlock.outputValue( dmPinConnector.output )
			outputHandle.setFloat( result )
			dataBlock.setClean( plug )
			
		return OM.kUnknownParameter

def nodeCreator():
	return OMPx.asMPxPtr( dmPinConnector() )

def nodeInitializer():
	nAttr = OM.MFnNumericAttribute()
	uAttr = OM.MFnUnitAttribute()

	dmPinConnector.aTx = uAttr.create("transx", "Tx", OM.MFnUnitAttribute.kDistance, 0.0);
	uAttr.setStorable(True)

	dmPinConnector.aTy = uAttr.create("transy", "Ty", OM.MFnUnitAttribute.kDistance, 0.0);
	uAttr.setStorable(True)
	
	dmPinConnector.input = nAttr.create( "input", "in", dmPinConnector.aTx, dmPinConnector.aTy)
	nAttr.setStorable(1)
	
	nAttr = OM.MFnNumericAttribute()
	dmPinConnector.output = nAttr.create( "output", "out", OM.MFnNumericData.kFloat, 1.0 )
	nAttr.setStorable(1)
	nAttr.setWritable(1)
	
	dmPinConnector.addAttribute( dmPinConnector.input )
	dmPinConnector.addAttribute( dmPinConnector.output )
	dmPinConnector.attributeAffects( dmPinConnector.input, dmPinConnector.output )
	
def initializePlugin(mobject):
	mplugin = OMPx.MFnPlugin(mobject)
	try:
		mplugin.registerNode( kPluginNodeTypeName, dmPinConnectorId, nodeCreator, nodeInitializer )
	except:
		sys.stderr.write( "Failed to register node: %s" % kPluginNodeTypeName )
		raise

def uninitializePlugin(mobject):
	mplugin = OMPx.MFnPlugin(mobject)
	try:
		mplugin.deregisterNode( dmPinConnectorId )
	except:
		sys.stderr.write( "Failed to deregister node: %s" % kPluginNodeTypeName )
		raise
	
