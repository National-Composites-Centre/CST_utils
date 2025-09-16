import win32com.client.dynamic
from jsonic import serialize, deserialize
from CompoST import CompositeStandard as cs
from CompoST import Utilities
#from STL.file_utils import clean_json
from pydantic import BaseModel, Field
from typing import Optional

from CATIA.CATIA_utils import CATIA_ctrl
from CATIA.vecEX3 import wrmmm
import numpy as np



def test_initial():

    path = "D:\\CAD_library_sampling\\CompoST_examples\\EOP_example\\PolylineExample.txt"

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



    with open(path, "r") as fl:
        strX = fl.read()

        for i, line in enumerate(strX.split("\n")[:]):
            if i != 0:
                x = line.split(",")[0]
                y = line.split(",")[1]
                z = line.split(",")[2]

                #Create Origin
                point0= C.HSF.AddNewPointCoord(x,y,z)
                body1.AppendHybridShape(point0)
            

#test_initial()

import random
#Script 1 to generate some test data
def generate_points(no_points = 100):
    #this script is not used when processing data
    #it merely creates synthetic data for demonstrator part

    #catia setup
    C = CATIA_ctrl()

    #Initiate CATIA interaction
    C.CAT = win32com.client.dynamic.DumbDispatch('CATIA.Application')
    C.doc = C.CAT.ActiveDocument
    C.cat_name = C.CAT.ActiveDocument.Name

    C.part = C.doc.Part
    C.HSF = C.part.HybridShapeFactory

    C.bodies = C.part.HybridBodies

    #new body 1 
    C.b_list = []
    body1 = C.bodies.Add()
    body1.Name="ToHide"
    C.b_list.append(body1)

    #hide body 1
    selection1 = C.doc.Selection
    visPropertySet1 = selection1.VisProperties
    selection1.Add(body1)
    visPropertySet1 = visPropertySet1.Parent
    visPropertySet1.SetShow(1)

    #new body 2
    C.b_list = []
    body2 = C.bodies.Add()
    body2.Name="ToSave"
    C.b_list.append(body2)

    hybridBody1 = C.bodies.Item("gs2")
    hybridShapes1 = hybridBody1.HybridShapes
    hybridShapeBoundary1 = hybridShapes1.Item("Boundary.1")
    r1 = C.part.CreateReferenceFromObject(hybridShapeBoundary1)

    #Create Origin
    point0= C.HSF.AddNewPointCoord(0,0,0)
    body1.AppendHybridShape(point0)
    r2 = C.part.CreateReferenceFromObject(point0)

    hybridBody2 = C.bodies.Item("GG")
    hybridShapes2 = hybridBody2.HybridShapes
    hybridShapeAssemble1 =  hybridShapes2.Item("MEOP")
    r5 = C.part.CreateReferenceFromObject(hybridShapeAssemble1)

    i = 0
    while i < no_points:

        #append to body 1
        POC = C.HSF.AddNewPointOnCurveWithReferenceFromPercent(r1, r2, i/no_points, False)
        body1.AppendHybridShape(POC)
        r3 = C.part.CreateReferenceFromObject(POC)

        #create offset in x + y, append to body 1
        pt1 = C.HSF.AddNewPointCoord(random.randint(-3,3), random.randint(-3,3), 0.000000)
        pt1.PtRef = r3
        body1.AppendHybridShape(pt1)
        r4 = C.part.CreateReferenceFromObject(pt1)       

        #create project of ^, append to body 2
        pr = C.HSF.AddNewProject(r4, r5)
        body2.AppendHybridShape(pr)

        i += 1

    #save as .wrl (all from body 2)
    C.part.Update()
    #export .wrl with only the latest spline points visible
    C.doc.ExportData("C:\\temp\\xxx.wrl", "wrl")

    #load from .wrl (vec_x3)
    vec, pts = wrmmm(Multi = True) 

    #save as .txt into sub-folder
    txt_col = ""
    json_col = cs.CompositeDB()
    #example spline
    json_col.allGeometry =[cs.Spline(points=[])]

    for i in range(0,np.size(pts,0)):
        #txt build
        txt_col +=str(pts[i,0])+","+str(pts[i,1])+","+str(pts[i,2])+"\n"

        #json build
        json_col.allGeometry[0].points.append(cs.Point(x=pts[i,0],y=pts[i,1],z=pts[i,2]))

    path = "D:\\CAD_library_sampling\\CompoST_examples\\TEMPLATE_example_v71a_V1\\EOP_measurements"
    filename = "example_ply_edge"

    #save .txt defect into EOP_measurements sub-folder
    with open(path+"\\"+filename+str(no_points)+".txt", 'w') as out_file:
        out_file.write(txt_col)

    #save .json defect into EOP_measurements sub-folder
    json_str = serialize(json_col, string_output = True)

    #clean the JSON
    json_str = Utilities.clean_json(json_str)

    print("saving as:",path+"\\"+filename+str(no_points)+".json")
    with open(path+"\\"+filename+str(no_points)+".json", 'w') as out_file:
        out_file.write(json_str)

    return()

#generate_points(47)

def rec_memberName(D,member,locObj):

    #pass overall database, keyword searched for, and localObj
    #recursively looks through nested lists
    obtainedObject = None
    if locObj.splineRelimitation != None:
        if locObj.splineRelimitation.memberName == member:
            obtainedObject = locObj

    #for cases where splines are not directly appended, but are specified by ID
    elif locObj.splineRelimitationRef != None:
        for geo in D.allGeometry:
            print(type(geo))
            if geo.ID == locObj.splineRelimitationRef:
                if geo.memberName == member:
                    obtainedObject = locObj

    #if the current object is not it, but has SubComponents recursively do ^^ again
    if obtainedObject == None:
        if locObj.subComponents != None:
            for loc in locObj.subComponents:
                D,obtainedObject = rec_memberName(D,member,loc)
                if obtainedObject != None:
                    break

    return(D,obtainedObject)

#Script 2 to store generated data in CompoST
def load_EOP(path,filename,example_file):

    #loop through folder with EOP data, for each file allocate data to correct ply!

    #for now only main ply (no loop) -- more plies with more boundaries later! #TODO
    #work with JSON for now, but from script above can easily pick .txt and translate

    #Open file

    with open(path+"\\EOP_measurements\\"+example_file+".json", 'r') as in_file:
         json_str = in_file.read()

    EOP_D = deserialize(json_str,string_input=True)

    #Open layup file
    with open(path+"\\"+filename+".json","r") as in_file:
        json_str= in_file.read()
    #print(json_str)
    D = deserialize(json_str,string_input=True)

    #find "edge" spline, create "defect", append the point cloud as delimitation


    for comp in D.allComposite:
        D, returnedObject = rec_memberName(D,"edge",comp)
        print(returnedObject)

        if returnedObject != None:
            

            if returnedObject.defects == None:
                returnedObject.defects = []
            if D.allDefects == None:
                D.allDefects = []
            lastID = D.fileMetadata.maxID
            EOP_D.allGeometry[0].ID = lastID+1
            lastID = lastID + 1
            returnedObject.defects.append(cs.BoundaryDeviation(splineRelimitation=EOP_D.allGeometry[0], ID=lastID+1))
            D.allDefects.append(returnedObject.defects[len(returnedObject.defects)-1])
            D.fileMetadata.maxID += 1

            break

    #turn data back to JSON
    json_str = serialize(D, string_output = True)

    #clean the JSON
    json_str = Utilities.clean_json(json_str)

    #re-save te file
    print("saving as:",path+"\\"+filename+"_X.json")
    with open(path+"\\"+filename+"_X.json", 'w') as out_file:
        out_file.write(json_str)

    return()

    #Ideally the ^^ above not part of the actual process, storing of points happens directly into CompoST
    #However, here we generated few examples to include variation


def rec_defect(D,ID,locList):

    #recursively search for defect ID within allComposites tree
    obtainedObject = None
    for locObj in locList:
        if locObj.defects != None:
            for de in locObj.defects:
                if de.ID == ID:
                    #save object and leave loop when the desired defect found
                    obtainedObject = locObj
                    break
        
        #if this object does not have defect appended, look through subComponents recursively
        if obtainedObject == None:
            print(type(locObj.subComponents))
            if type(locObj.subComponents) == list:
                D, obtainedObject = rec_defect(D,ID,locObj.subComponents)
                if obtainedObject != None:
                    break


    return(D,obtainedObject)


#Script 3 to process the "defect" specific parameters (half-way to sentencing)
def process_EOP(file):

    #open file
    with open(file,"r") as in_file:
        json_str= in_file.read()
    #print(json_str)
    D = deserialize(json_str,string_input=True)

    #for every defect - find parent 
    for de in D.allDefects:

        if type(de) == cs.BoundaryDeviation:
            #recursively look for defects ID in objects
            print(de.ID)
            D, obtainedObject = rec_defect(D,de.ID,D.allComposite)

            #for cases where splines are not directly appended, but are specified by ID
            if obtainedObject.splineRelimitation == None:
                for geo in D.allGeometry:
                    print(type(geo))
                    if geo.ID == obtainedObject.splineRelimitationRef:
                        localSpline = geo

            else: 
                localSpline = obtainedObject.splineRelimitation


            #once you have both splines, find which has less points and collect min distance...

            if len(de.splineRelimitation.points) < len(localSpline.points):
                spline1 = de.splineRelimitation
                spline2 = localSpline
            else: 
                spline2 = de.splineRelimitation
                spline1 = localSpline

            print(spline1.ID)
            print(spline2.ID)
            distances = []
            for pt in spline1.points:
                print(pt)
                #to be obtained min distances and pts
                minD1 = 99999
                minD2 = 999999
                near1 = None
                near2 = None
                for pt2 in spline2.points:
                    dist = np.sqrt((pt.x-pt2.x)**2+(pt.y-pt2.y)**2+(pt.z-pt2.z)**2)
                    if dist < minD1:
                        #demote current minDist to minD2?
                        minD2 = minD1
                        near2 = near1
                        #adjust minDist
                        minD1 = dist
                        near1 = pt2
                    
                    elif dist < minD2:
                        #if not closest but taking 2nd closest
                        minD2 = dist
                        near2 = pt2

                #TODO adjust granularity of this to the actual tolerance when available (for now 10 points)
                minDist = minD1
                PTS = 10
                for i in range(0,int(PTS/2)):
                    #only half points need to be checked as we now which is closer

                    #all the point operations would be faster in numpy matrices, TODO consider redoing
                    locPT = cs.Point(x=near1.x+(near2.x-near1.x)*i/PTS,
                                     y=near1.y+(near2.y-near1.y)*i/PTS,
                                     z=near1.z+(near2.z-near1.z)*i/PTS)
                    dist = np.sqrt((pt.x-locPT.x)**2+(pt.y-locPT.y)**2+(pt.z-locPT.z)**2)
                    if dist < minDist:
                        minDist = dist

                distances.append(minDist)

            #variables ready to compare to tolerance
            de.maxDeviation = max(distances)
            de.avDeviation = np.average(distances)


    #turn data back to JSON
    json_str = serialize(D, string_output = True)

    #clean the JSON
    json_str = Utilities.clean_json(json_str)

    #re-save te file
    print("saving as:",path+"\\"+filename+"_X.json")
    with open(path+"\\"+filename+"_all.json", 'w') as out_file:
        out_file.write(json_str)
    
    return()


path = "D:\\CAD_library_sampling\\CompoST_examples\\TEMPLATE_example_v71a_V1"
filename = "x_test_142_tols_wrinkle_withFO"
example_file = "Test_Output_PA"
load_EOP(path,filename,example_file)

process_EOP("D:\\CAD_library_sampling\\CompoST_examples\\TEMPLATE_example_v71a_V1\\x_test_142_tols_wrinkle_withFO_X.json")


