import win32com.client.dynamic
from jsonic import serialize, deserialize
import CompositeStandard as cs
from pydantic import BaseModel, Field
from typing import Optional


class CATIA_ctrl(BaseModel):
    #this is made simply to pass around info around loaded CATIA
    bodies: Optional[object] = Field(None)
    CAT: Optional[object] = Field(None)
    HSF: Optional[object] = Field(None)
    doc: Optional[object] = Field(None)
    part: Optional[object] = Field(None)
    b_list: Optional[list[object]] = Field(None) # list of bodies 
    cat_name: Optional[str] = Field(None) #active document name

def bug_fixing(pt, loc_elem):

    #Initiate CATIA interaction
    
    CATIA = win32com.client.dynamic.DumbDispatch('CATIA.Application')
    partDocument2 = CATIA.ActiveDocument
    cat_name = CATIA.ActiveDocument.Name

    part1 = partDocument2.Part
    HSF = part1.HybridShapeFactory
    originElements1 = part1.OriginElements
    hbs = part1.HybridBodies
    

    body1 = hbs.Add()
    # Naming new body as "wireframe"
    body1.Name="rrr"
    
    #reference point on default - does not need to be on part
    point=HSF.AddNewPointCoord(pt[0],pt[1],pt[2])
    body1.AppendHybridShape(point)
    body1 = hbs.Add()
    # Naming new body as "wireframe"
    body1.Name="rrr"
    for element in loc_elem:
        for n in element.nodes[:]:
            point=HSF.AddNewPointCoord(n.x,n.y,n.z)
            body1.AppendHybridShape(point)


def CAT_points(points,seg=0):

    #Initiate CATIA interaction
    CATIA = win32com.client.dynamic.DumbDispatch('CATIA.Application')
    partDocument2 = CATIA.ActiveDocument
    cat_name = CATIA.ActiveDocument.Name

    part1 = partDocument2.Part
    HSF = part1.HybridShapeFactory
    originElements1 = part1.OriginElements
    hbs = part1.HybridBodies
    
    body1 = hbs.Add()
    # Naming new body as "wireframe"
    body1.Name="Segment"+str(seg)
    for p in points:
        
        #reference point on default - does not need to be on part
        point=HSF.AddNewPointCoord(p.x,p.y,p.z)
        body1.AppendHybridShape(point)



#next few are display tools 

def display_file(D,disp_mesh = True):

    #package CATIA setup for moving it around
    C = CATIA_ctrl()

    #Initiate CATIA interaction
    C.CAT = win32com.client.dynamic.DumbDispatch('CATIA.Application')
    C.doc = C.CAT.ActiveDocument
    C.cat_name = C.CAT.ActiveDocument.Name

    C.part = C.doc.Part
    C.HSF = C.part.HybridShapeFactory

    C.bodies = C.part.HybridBodies

    C.b_list = []
    body1 = C.bodies.Add()
    body1.Name="Points"
    C.b_list.append(body1)

    body2 = C.bodies.Add()
    body2.Name="Splines"
    C.b_list.append(body2)

    body3 = C.bodies.Add()
    body3.Name="Splines"
    C.b_list.append(body3)

    #individual functions for specific objects to be displayed 
    #To be expanded with CompoST expansion
    for g in D.allGeometry:
        if type(g) == cs.AreaMesh:
            if disp_mesh == True:
                display_AreaMesh(g,C.part,C.HSF,C.bodies)

        if type(g) == cs.Point:
            display_point(g,C.part,C.HSF,body1)

        if type(g) == cs.Spline:
            display_spline(g,C.part,C.HSF,body2,D)

        if type(g) == cs.AxisSystem:
            C = display_AxisSystem(g,C)

        if type(g) == cs.Line:
            display_line(g,C)

    return(C)

def display_AxisSystem(AS,C):
    #CATIA axis definition causes issue for scripting.
    #Currently the below displayed as lines instead .
    #This can be manually created into axis system if needed.
    #TODO explore the issue with passing arguments to actual axis system object in CATIA

    body1 = C.bodies.Add()
    if AS.ID != None:
        body1.Name="AxiSystem_"+"ID_"+str(AS.ID)
    else:
        body1.Name="AxiSystem_"+"_ID_NONE"
    C.b_list.append(body1)

    #Create Origin
    point0= C.HSF.AddNewPointCoord(AS.o_pt.x,AS.o_pt.y,AS.o_pt.z)
    body1.AppendHybridShape(point0)
    r0 = C.part.CreateReferenceFromObject(point0)
    point0.Name = "o_pt"
    
    #Create x axis point
    point= C.HSF.AddNewPointCoord(AS.x_pt.x,AS.x_pt.y,AS.x_pt.z)
    body1.AppendHybridShape(point)
    r1 = C.part.CreateReferenceFromObject(point)
    point.Name = "x_pt"

    #create y axis point
    point= C.HSF.AddNewPointCoord(AS.y_pt.x,AS.y_pt.y,AS.y_pt.z)
    body1.AppendHybridShape(point)
    r2 = C.part.CreateReferenceFromObject(point)
    point.Name = "y_pt"

    #create z axis point
    point= C.HSF.AddNewPointCoord(AS.z_pt.x,AS.z_pt.y,AS.z_pt.z)
    body1.AppendHybridShape(point)
    r3 = C.part.CreateReferenceFromObject(point)
    point.Name = "z_pt"

    #create x axis line
    line = C.HSF.AddNewLinePtPt(r0, r1)
    body1.AppendHybridShape(line)
    r4 = C.part.CreateReferenceFromObject(line)
    line.Name = "x_v"

    #create y axis line
    line = C.HSF.AddNewLinePtPt(r0, r2)
    body1.AppendHybridShape(line)
    r5 = C.part.CreateReferenceFromObject(line)
    line.Name = "y_v"

    #create z axis line
    line = C.HSF.AddNewLinePtPt(r0, r3)
    body1.AppendHybridShape(line)
    r6 = C.part.CreateReferenceFromObject(line)
    line.Name = "z_v"

    #AxisSystem itself currently not created in CATIA

    return(C)



def display_line(line,C):

    #Currently only displays lines with embeded points (rather than ID referenced)
    #TODO to fix ^^ points would have to be run before lines then IDs are found in CATIA
    if line.points != None:
        #Point 1
        point0= C.HSF.AddNewPointCoord(line.points[0].x,line.points[0].y,line.points[0].z)
        C.b_list[2].AppendHybridShape(point0)
        r0 = C.part.CreateReferenceFromObject(point0)

        #Point 2
        point= C.HSF.AddNewPointCoord(line.points[1].x,line.points[1].y,line.points[1].z)
        C.b_list[2].AppendHybridShape(point)
        r1 = C.part.CreateReferenceFromObject(point)

        #Line
        line1 = C.HSF.AddNewLinePtPt(r0, r1)
        C.b_list[2].AppendHybridShape(line1)
        r3 = C.part.CreateReferenceFromObject(line1)
        if line.ID != None:
            line1.Name="ID"+str(line.ID)


    return()

def display_AreaMesh(AM,part1,HSF,hbs):
    body3 = hbs.Add()
    body3.Name="AreaMesh"

    for el in AM.meshElements:
        lines = []
        for i,n in enumerate(el.nodes):
            point = HSF.AddNewPointCoord(n.x,n.y,n.z)
            body3.AppendHybridShape(point)
            r1 = part1.CreateReferenceFromObject(point)
            if i != 0:
                lpt = HSF.AddNewLinePtPt(r1, r2)
                body3.AppendHybridShape(lpt)
                rl1 = part1.CreateReferenceFromObject(lpt)
                lines.append(rl1)
            else:
                r3 = r1
            r2 = r1

        #add last line to close element
        lpt = HSF.AddNewLinePtPt(r2, r3)
        body3.AppendHybridShape(lpt)
        rl1 = part1.CreateReferenceFromObject(lpt)
        lines.append(rl1)

        #add the fill (to be able to export stl etc)
        fll = HSF.AddNewFill()
        for r in lines:
            fll.AddBound(r)
        fll.Continuity = 1
        fll.Detection = 2
        fll.AdvancedTolerantMode = 2
        body3.AppendHybridShape(fll)
    return()


def display_point(pt,part1,HSF,body1):
    point=HSF.AddNewPointCoord(pt.x,pt.y,pt.z)
    if pt.ID != None:
        point.Name="ID"+str(pt.ID)
    body1.AppendHybridShape(point)
    return()


def display_spline(spl,part1,HSF,body2,D):

    ref_list = []
    # Starting new spline f
    spline2 = HSF.AddNewSpline()
    spline2.SetSplineType(0)
    if (spl.breaks != None) and (spl.breaks != []):
        spline2.SetClosing(0)
        
    else:
        spline2.SetClosing(1)

    #For points stored directly under spline
    if spl.points != None:
        for i,p in enumerate(spl.points):
            point=HSF.AddNewPointCoord(p.x,p.y,p.z)
            spline2.AddPoint(point)

            #if the current point is marked in breaks, finish spline and start a new one
            if spl.breaks != None:
                if (i in spl.breaks) and (i != len(spl.points)-1):
                    #Submit the spline and create reference.
                    body2.AppendHybridShape(spline2) 
                    spline2.Name="ID"+str(spl.ID)+"breakAt_"+str(i)
                    rs2 = part1.CreateReferenceFromObject(spline2) 
                    ref_list.append(rs2)

                    spline2 = HSF.AddNewSpline()
                    spline2.SetSplineType(0)

                    #add same point as a start
                    point = HSF.AddNewPointCoord(p.x,p.y,p.z)
                    point.Name="ID"+str(p.ID)
                    spline2.AddPoint(point)


    #For list of points stored as ID refernces only
    elif spl.pointRefs != None:
        for i,p in enumerate(spl.pointRefs):
            for O in D.allGeometry:
                try:
                    if O.ID == p:
                        pt = O
                        break
                except:
                    #no ID
                    pass
            point = HSF.AddNewPointCoord(pt.x,pt.y,pt.z)
            point.Name="ID"+str(pt.ID)
            spline2.AddPoint(point)

            #if the current point is marked in breaks, finish spline and start a new one
            if spl.breaks != None:
                if (i in spl.breaks) and (i != len(spl.points)-1):
                    #Submit the spline and create reference.
                    body2.AppendHybridShape(spline2) 
                    spline2.Name="ID"+str(spl.ID)+"breakAt_"+str(i)
                    rs2 = part1.CreateReferenceFromObject(spline2) 
                    ref_list.append(rs2)

                    spline2 = HSF.AddNewSpline()
                    spline2.SetSplineType(0)

                    #add same point as a start
                    point = HSF.AddNewPointCoord(pt.x,pt.y,pt.z)
                    point.Name="ID"+str(pt.ID)
                    spline2.AddPoint(point)


    #if breaks were employed first point has to be added
    if spl.breaks != None:
        p = spl.points[0]
        point = HSF.AddNewPointCoord(p.x,p.y,p.z)
        point.Name="ID"+str("__0__")
        spline2.AddPoint(point)



    #Submit the spline and create reference.
    body2.AppendHybridShape(spline2) 
    spline2.Name="ID"+str(spl.ID)
    rs2 = part1.CreateReferenceFromObject(spline2) 
    ref_list.append(rs2)

    #merge splienes
    if len(ref_list) > 1:
        
        #initiate assembly
        asm = HSF.AddNewJoin(ref_list[0], ref_list[1])
        i = 2
        #depending on number of breaks add other pieces
        while i < len(ref_list):
            asm.AddElement(ref_list[i])
            i = i + 1 

        asm.SetConnex(1)
        asm.SetManifold(1)
        asm.SetSimplify(0)
        asm.SetSuppressMode(0)
        asm.SetDeviation(0.001000)
        asm.SetAngularToleranceMode(0)
        asm.SetAngularTolerance(0.500000)
        asm.SetFederationPropagation(0)
        body2.AppendHybridShape(asm)
        #rename
        asm.Name="ID"+str(spl.ID)+"_asm"
        

    return()

def SurfaceGen(AM):

    #Not used in the end because of the fidelity of provided data

    #Can be continued according to notes below if .stl with reasonable size is provided

    #package CATIA setup for moving it around
    C = CATIA_ctrl()

    #Initiate CATIA interaction
    C.CAT = win32com.client.dynamic.DumbDispatch('CATIA.Application')
    C.doc = C.CAT.ActiveDocument
    C.cat_name = C.CAT.ActiveDocument.Name

    C.part = C.doc.Part
    C.HSF = C.part.HybridShapeFactory

    C.bodies = C.part.HybridBodies

    b_list = []
    body1 = C.bodies.Add()
    body1.Name="SG"
    b_list.append(body1)

    body2 = C.bodies.Add()
    body2.Name="MainSurface"
    b_list.append(body2)

    #initiate assembly


    #for each element
        #create surface 

        #append to assembly

    #finalize assembly

    #loop through lenght of the part

        #create a plane

        #intersect with assembly 

        #save intersect to list

    

    #for each intersect in the loft 
    #    no_p = 30
    
    #    i = 0
        #initiate spline
    #    while i < no_p+1:
            #create points and append to spline
            
    #        hpc1 = HSF.AddNewPointOnCurveWithReferenceFromPercent(ref1, ref2, i/no_p, False)

        #finalize spline, add to spl list
        

    #initiate loft

        #for each intersect in the spl list, add to loft

    #how is the surface?
    print("x")


#open file
# with open("D:\\CAD_library_sampling\\CompoST_examples\\WO4502_minimized bench\\WO4502.json","r") as in_file:
#     json_str= in_file.read()

# #print(json_str)
# D = deserialize(json_str,string_input=True)

# display_file(D,disp_mesh=False)
