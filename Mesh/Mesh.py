from CATIA.CATIA_utils import CATIA_ctrl, display_file, load_step
from jsonic import serialize, deserialize
from utils import reLink, clean_json
import win32com.client.dynamic
from CATIA.vecEX3 import wrmmm
import numpy as np

import CompositeStandard as cs

def projectMesh(D,xNO = 300, yNO =240,meshPlane=True):
    #Assume for now projection always happens in z direction

    #xNo and yNO is the mesh seed in the principle directions (this can be calculated based on aspect ratio in the future)

    #for now fix it to location 
    #TODO in future iterate intersects until one works (deleting broken ones) - that way locatin in x-y does not matter

    #load step file
    #TODO - independent of file format
    #D.fileMetadata.cadFilePath = D.fileMetadata.cadFilePath.replace("CATPart",".stp")
    #C = load_step(D)

    #Initially developed for KinDrape OS draping tool

    #package CATIA setup for moving it around
    C = CATIA_ctrl()

    #Initiate CATIA interaction
    C.CAT = win32com.client.dynamic.DumbDispatch('CATIA.Application')
    C.doc = C.CAT.ActiveDocument

    #Initiate CATIA interaction
    C.doc = C.CAT.ActiveDocument
    C.cat_name = C.CAT.ActiveDocument.Name

    C.part = C.doc.Part
    C.HSF = C.part.HybridShapeFactory

    C.bodies = C.part.HybridBodies


    #display basic geometries (not needed now)
    #C = display_file(D,disp_mesh = False)

    #This needs to be draping tool..... TODO 

    #crete new bodies
    C.b_list = []
    body1 = C.bodies.Add()
    body1.Name="Planes"
    C.b_list.append(body1)

    body2 = C.bodies.Add()
    body2.Name="Intersects"
    C.b_list.append(body2)

    #Hide the above so that .wrl point extraction below works
    selection1 = C.doc.Selection
    selection1.Clear() # added recently delete if error
    visPropertySet1 = selection1.VisProperties
    selection1.Add(body1)
    selection1.Add(body2)
    visPropertySet1 = visPropertySet1.Parent
    visPropertySet1.SetShow(1)
    selection1.Clear()

    #starting x 
    x0 = 0
    xMax = -2500
    #ending X

    #grid like mesh 
    X = np.zeros([xNO,yNO])
    Y = np.zeros([xNO,yNO])
    Z = np.zeros([xNO,yNO])

    if meshPlane == False:
        #Reference default plane
        originElements1 = C.part.OriginElements
        pe1 = originElements1.PlaneYZ
        ref1 = C.part.CreateReferenceFromObject(pe1)

    #when plane and geometry exists in CAD
    else:
        hb1 = C.bodies.Item("ForMesh")
        hs1 = hb1.HybridShapes
        m = hs1.Item("ForMesh")
        ref1 = C.part.CreateReferenceFromObject(m)

    #list os splines
    #TODO now IDs because KinDrape does not work with CompoST fully
    spls = []

    #iterate to create cross sections
    for i , x in enumerate(range(int(x0),int(xMax),int((xMax-x0)/(xNO)))):

        #Create offset plane for intersection
        pe2 = C.HSF.AddNewPlaneOffset(ref1, x/10, False)
        body1.AppendHybridShape(pe2)
        ref2 = C.part.CreateReferenceFromObject(pe2)

        #"split changed for MainS" #TODO !!!
        #intersect
        hb1 = C.bodies.Item("DrapingSim")
        hs1 = hb1.HybridShapes
        hsp1 = hs1.Item("DrapeTool")
        ref3 = C.part.CreateReferenceFromObject(hsp1)

        HSI = C.HSF.AddNewIntersection(ref2,ref3)
        HSI.PointType = 0

        body2.AppendHybridShape(HSI)
        ref4 = C.part.CreateReferenceFromObject(HSI)

        #(create point for reference above)
        pREF= C.HSF.AddNewPointCoord(0,-100000,-100000)
        body1.AppendHybridShape(pREF)
        ref5 = C.part.CreateReferenceFromObject(pREF)

        body3 = C.bodies.Add()
        body3.Name="Points_"+str(x)
        C.b_list.append(body3)

        for y in range(0,100000,int(100000/yNO)):

            #create a point with reference to extremity in y direction
             
            poc = C.HSF.AddNewPointOnCurveWithReferenceFromPercent(ref4, ref5, y/100000, False)
            body3.AppendHybridShape(poc)
            

        #for each intersect points
        C.part.Update()
        C.doc.ExportData("C:\\temp\\xxx.wrl", "wrl")
        vec,f_point = wrmmm(Multi=True)
        f_point = np.delete(f_point,0,axis=0)

        col = 0
        spl = cs.Spline(points=[],ID=D.fileMetadata.maxID+1)
        while col < yNO:
            spl.points.append(cs.Point(x=f_point[col,0],y=f_point[col,1],z=f_point[col,2]))
            col += 1
        D.allGeometry.append(spl)
        D.fileMetadata.maxID += 1
        spls.append(int(D.fileMetadata.maxID))

        #Hide last set of points for future exports
        selection1 = C.doc.Selection
        selection1.Clear() # added recently delete if error
        visPropertySet1 = selection1.VisProperties
        selection1.Add(body3)
        visPropertySet1 = visPropertySet1.Parent
        visPropertySet1.SetShow(1)
        selection1.Clear()

    #store point cloud to CompoST
    D.allGeometry.append(cs.AreaMesh(additionalParameters={"GridSplines":spls} , ID=D.fileMetadata.maxID+1))
    D.fileMetadata.maxID += 1

    #turn data back to JSON
    json_str = serialize(D, string_output = True)

    #clean the JSON
    json_str = clean_json(json_str)

    #save the JSON
    #save as file
    print("saving as:",path+"\\"+filename+"_DrapeMesh3.json")
    with open(path+"\\"+filename+"_DrapeMesh3.json", 'w') as out_file:
        out_file.write(json_str)



    return(D)

#load compost


path = "D:\\CORE\\cad_data\\ABS"
filename = "ABS_005"
with open(path+"\\"+filename+"_layup.json","r") as in_file:
    json_str= in_file.read()

#turn file into workable classes
D = deserialize(json_str,string_input=True)

#re-link - if relevant
D = reLink(D)

projectMesh(D)
