#digit_domain.py
from digit_base import LayerMaster
from re import findall
import math
from collections import OrderedDict 

class DxfPoly:
	def __init__(self, layer, ofType , handle):
		self.layer = layer
		self.ofType = ofType
		self.handle = handle
		self.points = []	#2d x,y
		self.rawpoints = []		#x,y,s,e,b
		self.hasBulge = False #default
		self.splayOverride=False #default for setting splay for non radius method
		self.sideLenghts=[]

		self.setBackList=[]
		self.bulge = 0.0 # for arc
		self.radius = 0.0 # for arc
		self.angle = 0.0  #angle
		self.chord = 0.0  # chord is 1/2 of distance between start and end point of arc
		self.modelbounds = []
		self.closed = 0 #True  by default
		self.color='0'

		self.miscProps=dict()

	def setColor(self,color:str):
		self.color=color

	#for stairs and any one-off keyvales based on object requirements - 11/22/2020 Eshwar
	#for center line # 4/18/2022
	def setMiscProps(self,miscProperties: dict):
		self.miscProps = miscProperties if miscProperties != None else dict()

	def getMiscProps(self):
		return self.miscProps

	def getColor(self):
		return self.color

	def setIsClosed(self, closed: bool ):
		self.closed = closed

	def isClosed(self) :
		return self.closed

	#for (splay) i.e. arcs method#1
	def set_bulge_radius_angle_chordlen(self,  bulge: float, radius : float, angle:float, chord:float ):
		self.hasBulge = True
		self.bulge = bulge
		self.radius = radius
		self.angle = angle
		self.chord = chord

	def add_sideLenghts(self,length:float):
		self.splayOverride= True
		self.sideLenghts.append(length)

	#for points with 2d coordinates  x,y
	def add_2dpoint(self,point):
		self.points.append(point)

	def get_points(self):
		return self.points

	def set_rawpoints(self, rawpoints :list ):
		self.rawpoints = rawpoints

	def get_rawpoints(self):
		return self.rawpoints

	def get_sideLengths(self):
		return self.sideLenghts

	def add_Setback(self,color:int,startPoint,endPoint,length:float):
		x1,y1,z1=startPoint
		x2,y2,z2=endPoint
		lineSegment=[]
		lineSegment.append(( x1, y1))
		lineSegment.append(( x2, y2 ))  		#('(' +  str(x2) + ', ' + str(y2) + ')' )
		sb = Setback(color, lineSegment, length)
		self.setBackList.append(sb)

	def getSetbacks(self):
		return self.setBackList


	def get_segment (self):
		if (self.hasBulge == True):
			theta = 4* math.atan(abs(self.bulge)) #math.radians(self.angle)
			radius_sq = (self.radius)**2
			area = (radius_sq/2) * (theta - math.sin(theta))
			return area
		else:
			return 0.0

	def to_dict(self):
		retVal = dict()
		retVal['handle']=self.handle
		retVal['color']=self.color
		retVal['closed']=self.closed
		retVal['points']=self.points
		retVal['type']=self.ofType
		retVal['miscProps']=self.miscProps
		retVal['setbacks']=self.setBackList
		return retVal

class Setback:
	def __init__(self,color:int,lineSegment:list,length:float):
		self.color=color

		if (color == 1 ):
			self.type='FRONT'
		elif(color == 6):
			self.type='REAR'
		elif(color == 104):
			self.type='SIDE1'
		elif(color == 5):
			self.type='SIDE2'
		else:
			self.type='INVALID'

		self.lineSegment=lineSegment

	def getSetback(self):

		return {'color':self.color,'type':self.type, 'lineSegment':self.lineSegment}

class BuildingName:
	def __init__(self,name,layer,polygon):
		self.name = name
		self.layer = layer
		self.polygon = polygon
		self.use = "N/A"
		self.subuse = "N/A"
		self.subtype =  "N/A"
		self.info = "N/A"

	def setDetails(self,use, subuse,subtype,info):
		self.use = use
		self.subuse = subuse
		self.subtype =  subtype
		self.info = info

class IndivSubPlot:

	def __init__(self, name, layer, polygon , length, width, area,handle:None ):
		self.name = name
		self.layer = layer 
		self.polygon = polygon 
		self.length = round(length,2)
		self.width = round(width,2)
		self.area = round(float(area),2)
		self.isvalid = 1  #False 
		self.handle=handle if handle != None else "" 
		self.color='0'

		self.frontageList = []
		self.abuttingRoadList = []
		self.errors = [] 
		self.misc = []
		if( float(length) * float(width) > float(area) ):
			self.isIrregularObject=True 
		else:
			self.isIrregularObject=False 
	
	def setColor(self,color:str):
		self.color=color

	def getColor(self):
		return self.color

	def add_errors(self, errors :list):
		self.errors.append(errors)
	
	def add_frontage_abuttingroad(self, abutRdFrontageDict:dict):
		for ite in abutRdFrontageDict.values():
			if ("|" in ite):
				itTmp = ite.split("|")
				self.abuttingRoadList.append(itTmp[0])
				try:

					if (itTmp[1] is not None and itTmp[1].isdigit() == False ):
						#print('raw str',itTmp[1])
						extractList = findall(r'\d+\.\d+', itTmp[1]) 
						if (len(extractList) > 0 ):
							self.frontageList.append(float(extractList[0]))
					else:
						self.frontageList.append(float(itTmp[1]))
				except Exception as excp:
					print('ERROR  - Problem parsing the frontage from input defaulting to 0. input value  ', str(abutRdFrontageDict), ' due to ', str(excp))
					self.frontageList.append(0.0)

	def set_isvalid(self, isvalid:bool ):
		self.isvalid = isvalid

	def get_frontage (self):
		if (self.frontageList is None or len(self.frontageList) == 0) : 
			return 0.0 
		else :
			return self.frontageList

	def get_abutting_road(self):
		#get the frontage side road 
		#get the index of max(frontageList ) and find corresponding value in 
		#abutting road list 
		if (self.frontageList == None ) :
			return "N/A"	
		idx = self.frontageList.index(min(self.frontageList))
		if (idx == 0 or self.abuttingRoadList is None or idx > len(self.abuttingRoadList)) :
			return "N/A"
		else:
			return self.abuttingRoadList[idx]

	def to_dict(self):
		returnValue = dict()
		returnValue['name']=self.name
		returnValue['handle']=self.handle
		returnValue['layer']=self.layer
		returnValue['length']=str(self.length)
		returnValue['width']=str(self.width)
		returnValue['area']=str(self.area)
		
		return returnValue


class Floor:
	def __init__(self, flayer, fname, parent:None, fcoords, fpolygon, flength, fwidth, farea):
		self.flayer = flayer   # "_Floor"
		self.fname = fname 
		self.parent = parent #if parent != None else ""  # Default is "" For floor 
		self.subtype = ""
		self.fcoords = fcoords
		self.fpolygon = fpolygon
		self.flength =  round(flength,2)
		self.fwidth =  round(fwidth,2)
		self.farea =  round(farea,2)
		self.residentialArea=0.0
		self.commercialArea=0.0
		self.specialArea=0.0
		self.industrialArea=0.0
		
		self.fheight= 0.0
		self.buaarea = 0.0
		self.balconyarea = 0.0  
		self.maxParkingarea = 0.0
		self.stairsarea = 0.0 # for stairs, lift, for STILT Type  
		self.accessoryarea = 0.0 #Fix 7/14/2022 changed logic to add 
		self.liftarea = 0.0 
		self.ramparea = 0.0 # ramp etc 
		self.passagearea= 0.0
		self.dwellarea = 0.0
		self.roomarea=0.0
		self.doorarea=0.0
		self.windowarea=0.0
		self.ventiShaftArea =0.0 # ventilationshafts, voids and cutouts 
		self.slabCutoutArea=0.0 
		self.excludedAccessoryArea=0.0 #Fix 7/14/2022 
		self.hasStackParking=False 
		self.noOfStacks=0
		self.stackFactor=1 #for stack above 2 it is n-1. i.e. stack 3 factor is 2, stack 4 factor is 3 
		self.stackParkingArea=0.0 #Fix 08/09/2023 add the stack area 
		self.isCommonFloorPlan=False #Fix 10/29/2022 to speed up the room checks 

		justFloor = fname.upper()

		if fname is None or len(fname) == 0:
			self.subtype = "N/A"

		elif LayerMaster.CELLAR_FLOOR in justFloor  or LayerMaster.BASEMENT_FLOOR in justFloor:
			self.subtype = LayerMaster.CELLAR_FLOOR  # use cellar name only for either of the values

		elif LayerMaster.PARKING_FLOOR in justFloor:
			self.subtype = LayerMaster.PARKING_FLOOR  # When Parking Floor are above STILT  has implications to the height in msbrs

		elif LayerMaster.STILT_FLOOR in justFloor   :
			self.subtype = LayerMaster.STILT_FLOOR  #"STILT" always 1

		elif LayerMaster.TERRACE_FLOOR in justFloor:

			self.subtype =  LayerMaster.TERRACE_FLOOR
		
		elif  LayerMaster.TYPICAL_FLOOR in justFloor :
			
			self.subtype =  LayerMaster.TYPICAL_FLOOR
		
		else:
			self.subtype = LayerMaster.NORMAL_FLOOR

		self.dwelUnits = []   # maps to carpet area/ dwelling units for floors. if stilt then to main_parking
		self.roomUnits = []
		self.doorUnits= []
		self.windowUnits=[]

		self.rampUnits = []  #ramp 
		self.accessoryUnits = []  # fire command center, watchman etc  
		self.ventiShaftUnits = []  #ventilator shaft/void/cutouts - to be excluded from NET BUA 1/7/2022 
		self.slabCutoutUnits = [] #slab cutvoid into separate field - 08/22/22
		self.parkingUnits = []  
		self.balcony = []  
		self.liftUnits = []  
		self.staircaseUnits = []  
		self.passageUnits = []
		self.mortagedUnits = []
		self.resibuaUnits = []
		self.commercialBuaUnits = []
		self.industrialBuaUnits = []
		self.specialBuaUnits = []
		self.parkingUnits = [] 
		self.excludedAccessories=[]


	def set_CommonFloorFlag(self,flag:bool):
		self.isCommonFloorPlan=flag
	

	def set_subtype(self,subtype:str):
		self.subtype = subtype

	def set_height(self,fheight:float):
		self.fheight = fheight

	def add_tofloor(self, objectType:str, bldgobj):

		area_tmp = bldgobj.getBUA() 
		
		if (objectType == LayerMaster.CARPETAREA ):
			self.dwelUnits.append(bldgobj)
			self.dwellarea += area_tmp
		
		elif (objectType == LayerMaster.ROOM ):
			self.roomUnits.append(bldgobj)
			self.roomarea += area_tmp

		elif (objectType == LayerMaster.DOOR ):
			self.doorUnits.append(bldgobj)
			self.doorarea += area_tmp

		elif (objectType == LayerMaster.WINDOW ):
			self.windowUnits.append(bldgobj)
			self.windowarea += area_tmp

		elif (objectType == LayerMaster.RAMP ):
			self.rampUnits.append(bldgobj)
			self.ramparea += area_tmp 
		
		elif (objectType == LayerMaster.ACCESSORYUSE):
			

			if (self.subtype in [LayerMaster.STILT_FLOOR,LayerMaster.CELLAR_FLOOR,LayerMaster.PARKING_FLOOR] and
				'WATCHMAN' in bldgobj.name.upper()  or 'TOILET' in bldgobj.name.upper() ):

				if ('WATCHMAN' in bldgobj.name.upper() ):
					self.accessoryUnits.append(bldgobj)

					if (area_tmp > 25):
						self.accessoryarea += 25
					else:
						self.accessoryarea += area_tmp
				else:
					self.accessoryUnits.append(bldgobj)
					self.accessoryarea += area_tmp
			else:
				self.excludedAccessories.append(bldgobj)
				self.excludedAccessoryArea += area_tmp
						
		#split into its own slot for deduction calculations
		elif (objectType == LayerMaster.VENTILATIONSHAFT ):

			self.ventiShaftUnits.append(bldgobj)
			self.ventiShaftArea += area_tmp

		elif (objectType == LayerMaster.SLABCUTOUTVOID):

			self.slabCutoutUnits.append(bldgobj)
			self.slabCutoutArea += area_tmp
		
		elif (objectType == LayerMaster.PARKING ):
			self.parkingUnits.append(bldgobj)
			if ("STACK" in bldgobj.name.upper() or "MECH." in bldgobj.name.upper()):
				self.hasStackParking=True

				if ("TWO" in bldgobj.name.upper() or "-1,2(MECH.)" in bldgobj.name.upper()):
					self.noOfStacks=2 
					self.stackFactor=2

				elif ("THREE" in bldgobj.name.upper() or "-1,2,3(MECH.)" in bldgobj.name.upper()):
					self.noOfStacks=3
					self.stackFactor=2
				elif ("FOUR" in bldgobj.name.upper() or "-1,2,3,4(MECH.)" in bldgobj.name.upper()):
					self.noOfStacks=4
					self.stackFactor=3
				else:
					self.noOfStacks=2 #default 
					self.stackFactor=2
				self.stackParkingArea+= (self.stackFactor * area_tmp)
				
			#need this pointer 
			if (area_tmp > self.maxParkingarea):
				self.maxParkingarea = area_tmp

		elif (objectType == LayerMaster.BALCONY ):
			self.balcony.append(bldgobj)
			self.balconyarea += area_tmp

		elif (objectType == LayerMaster.LIFT ):
			self.liftUnits.append(bldgobj)
			self.liftarea += area_tmp

		elif (objectType == LayerMaster.STAIRCASE ):
			self.staircaseUnits.append(bldgobj)
			self.stairsarea += area_tmp

		elif (objectType == LayerMaster.PASSAGE ):
			self.passageUnits.append(bldgobj)
			self.passagearea += area_tmp 

		elif (objectType == LayerMaster.MORTGAGEAREA ):
			self.mortagedUnits.append(bldgobj)

		elif (objectType == LayerMaster.RESIDENCE ):
			self.resibuaUnits.append(bldgobj)
			self.farea += area_tmp
			self.residentialArea += area_tmp

		elif (objectType == LayerMaster.INDUSTRIAL ):
			self.industrialBuaUnits.append(bldgobj)
			self.farea += area_tmp
			self.industrialArea += area_tmp

		elif (objectType == LayerMaster.COMMERCIAL ):
			self.commercialBuaUnits.append(bldgobj)
			self.farea += area_tmp
			self.commercialArea += area_tmp

		elif (objectType == LayerMaster.SPECIALUSE ):
			self.specialBuaUnits.append(bldgobj)
			self.farea += area_tmp
			self.specialArea += area_tmp
						
		else: 
			print('WARNING:  unknown object type to add to floor ' + objectType )


	def get_dimensions(self):
		retValue=dict()

		retValue['Name']= self.fname
		retValue['Building'] = self.parent
		retValue['Subtype'] = self.subtype
		retValue['Length']= self.flength
		retValue['Width']= self.fwidth
		retValue['Layer']= self.flayer
		retValue['Area']= self.farea
		retValue['ParkingUnits']=self.parkingUnits
		return retValue
		

	def get_dict(self):
		retValue = dict()
		retValue['Layer']=self.flayer
		retValue['Name']= self.fname
		retValue['Building'] = self.parent
		retValue['subtype'] = self.subtype
		retValue['DwellUnits']= str(len(self.dwelUnits))
		retValue['NoOfStairs']=str(len(self.staircaseUnits))
		retValue['NoOfLifts']=str(len(self.liftUnits))
		retValue['ResidentialArea']=str(round(self.residentialArea,2) )
		retValue['CommercialArea']=str(round(self.commercialArea,2) )
		retValue['IndustrialArea']=str(round(self.industrialArea,2) )
		retValue['SpecialArea']=str(round(self.specialArea,2) )
		retValue['BalconyArea']=str(round(self.balconyarea,2) )
		retValue['ExcludedAccessoryArea']=str(round(self.excludedAccessoryArea,2) )
		
		if self.subtype == LayerMaster.CELLAR_FLOOR or self.subtype == LayerMaster.STILT_FLOOR or self.subtype == LayerMaster.PARKING_FLOOR :
			
			retValue['BuiltUpArea'] = self.maxParkingarea 
			#net_parking_area = self.maxParkingarea - (self.ramparea + self.stairsarea +  self.liftarea + self.accessoryarea) 1/7/2022 dont remove ramp
			net_parking_area = self.maxParkingarea - (self.stairsarea +  self.liftarea + self.accessoryarea + self.ventiShaftArea)
			retValue['AccessoryUseArea'] = self.accessoryarea
			retValue['RampArea'] = round(self.ramparea,2)
			retValue['StairArea'] = round(self.stairsarea,2)
			retValue['LiftArea'] = round(self.liftarea,2)
			retValue['VentiShaftArea'] = round(self.ventiShaftArea,2)
			retValue['SlabCutoutArea'] = round(self.slabCutoutArea, 2)
			retValue['ProposedNetBUA'] = 0
			retValue['TotalNetBUA'] = round((self.stairsarea  + self.liftarea ),2)
			
			 
			
			retValue['ParkingFloorArea'] = net_parking_area 
			retValue['NoOfStacks']  = self.noOfStacks #Fix 8/22/2022
			retValue['StackFactor']= self.stackFactor # Fix 11/12/2022 
			retValue['TotalParkingArea'] = (net_parking_area * self.stackFactor)
			retValue['TotalStackParkingArea']=self.stackParkingArea

		else :
			retValue['BuiltUpArea'] = 0 if (self.subtype == LayerMaster.TERRACE_FLOOR) else (self.farea + self.balconyarea)
			#all below are part of BUA except Balcony 
			retValue['AccessoryUseArea'] = 0.0
			retValue['RampArea'] = 0.0
			retValue['StairArea'] = 0.0
			retValue['LiftArea'] = 0.0
			retValue['VentiShaftArea'] = 0.0 if (self.subtype == LayerMaster.TERRACE_FLOOR) else (round(self.ventiShaftArea,2))
			retValue['SlabCutoutArea'] = 0.0 if (self.subtype == LayerMaster.TERRACE_FLOOR) else (round(self.slabCutoutArea,2))
			retValue['ProposedNetBUA'] = (self.farea + self.balconyarea) - self.ventiShaftArea 
			retValue['TotalNetBUA'] = (self.farea + self.balconyarea) -self.ventiShaftArea 

			#if there are parking in the normal floors  
			sum_parking_bua_outline = sum(node.area for node in self.parkingUnits)
			sum_parking_bua_outline = sum_parking_bua_outline if sum_parking_bua_outline > 1 else 0.0 
			
			no_stacks = '-' if sum_parking_bua_outline == 0 else self.noOfStacks #Fix 8/22/2022 
			stackFactor = '-' if sum_parking_bua_outline == 0 else self.stackFactor #Fix 11/12/2022 
			
			retValue['ParkingFloorArea'] = sum_parking_bua_outline
			retValue['NoOfStacks']  = no_stacks
			retValue['StackFactor']= stackFactor # Fix 11/12/2022 
			retValue['TotalParkingArea'] = (sum_parking_bua_outline * self.stackFactor)
			retValue['TotalStackParkingArea']=self.stackParkingArea
		
		
		return retValue

class BldgBaseObj(IndivSubPlot):
	def __init__(self, parent:None, subtype:None, name, layer, polygon, length, width, height, area,handle:None):
		#inherit from base obj 
		super().__init__(name,layer,polygon,length,width,area,handle) 

		self.parent = parent if parent != None else ""  #Parking#1 mapped to Stilt-2-Floor 
		self.subtype = subtype if subtype != None else "" # floor, parking main, parking spot, stair,  
		self.height = round(float(height),2) 
		self.gradient = 0  #for Ramp Objects
		self.handle=handle if handle != None else "" 
		self.centerline=None #default 
		self.hasCenterLine=False
		self.DxfPoly = None
		
		if(subtype is not None and subtype in [LayerMaster.PARKING] and name is not None and  "MECH" in name.upper() ):
			self.isStackParking=True
		else:
			self.isStackParking=False

	def get_parent(self):
		return self.parent 

	# used for stairs to have a cross reference 11/22/20 Eshwar
	def get_handle(self):
		return self.handle 

	def get_subtype(self):
		return self.subtype 

	def set_DXFPoly(self,dxfpoly1):
		self.DxfPoly = dxfpoly1

	def get_DXFPoly(self):
		return self.DxfPoly

	def set_centerline(self,centerLineSegment):
		self.centerline=centerLineSegment
		self.hasCenterLine=True

	def get_centerline(self):
		return self.centreLine

	def has_centerline(self):
		return self.hasCentreLine

	def getIsStackParking(self):
		return self.isStackParking

	#for ramps we need the gradient check rule is 1:8  i.e. 1 mt in height for every 8 mt in slope length

	def getPolygonObj (self):
		return self.polygon
		
	def set_gradient(self,gradientValue:int ):
		self.gradient = gradientValue
	
	def getBUA(self):
		return round(self.area,2)

	def get_dict(self):
		retDict=OrderedDict()

		retDict['parent']=self.parent
		retDict['name']=self.name
		retDict['handle']=self.handle
		retDict['isStackParking']=self.isStackParking
		if ("FLOOR" in self.subtype):
			if "CELLAR" in self.subtype or "BASEMENT" in self.subtype:
				retDict['subtype']="BASEMENT"
			elif "STILT" in self.subtype :
				retDict['subtype']="STILT"
			elif "PLINTH" in self.subtype :
				retDict['subtype']="PLINTH"
			elif "TERRACE"	in self.subtype :
				retDict['subtype']="TERRACE"
			elif "MUMTY" in self.subtype:
				retDict['subtype'] = "MUMTY"
			else:
				retDict['subtype']="FLOOR"
		else:
			retDict['subtype']=self.subtype

		retDict['height']=self.height
		retDict['length']=self.length
		retDict['width']=self.width
		retDict['area']=self.area
		retDict['slope']=self.gradient
		return retDict