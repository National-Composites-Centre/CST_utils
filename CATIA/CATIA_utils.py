import win32com.client.dynamic
from jsonic import serialize, deserialize
import CompositeStandard as cs

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

def display_file(JS):

    #open file
    with open(JS,"r") as in_file:
        json_str= in_file.read()
    
    print(json_str)
    D = deserialize(json_str,string_input=True)

    #Initiate CATIA interaction
    CATIA = win32com.client.dynamic.DumbDispatch('CATIA.Application')
    partDocument2 = CATIA.ActiveDocument
    cat_name = CATIA.ActiveDocument.Name

    part1 = partDocument2.Part
    HSF = part1.HybridShapeFactory

    hbs = part1.HybridBodies
    body1 = hbs.Add()
    body1.Name="Points"

    body2 = hbs.Add()
    body2.Name="Splines"

    #individual functions for specific objects to be displayed 
    #To be expanded with CompoST expansion
    for g in D.allGeometry:
        if type(g) == cs.AreaMesh:
            display_AreaMesh(g,part1,HSF,hbs)

        if type(g) == cs.Point:
            display_point(g,part1,HSF,body1)

        if type(g) == cs.Spline:
            display_spline(g,part1,HSF,body2,D)


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




display_file("D:\\CAD_library_sampling\\CompoST_examples\\NO_IP_v068b-3\\x_test_141_layup.json")