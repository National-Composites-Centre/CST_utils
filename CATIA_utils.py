import win32com.client.dynamic
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