from jsonic import serialize, deserialize

import CompositeStandard as cs

import numpy as np
import math
import os

from utils import reLink

from STL.file_utils import clean_json
from CATIA.CATIA_utils import CATIA_ctrl
import win32com.client.dynamic


def store_FO(path,filename,ply_ID,zone=None):
    #This is now done per ply, but could also be modified to do per zone
    
    #load composite definition JSON
    
    with open(path+"\\"+filename+".json","r") as in_file:
        json_str= in_file.read()

    #turn file into workable classes
    D = deserialize(json_str,string_input=True)

    #re-link - if relevant
    D = reLink(D) #TODO UNTESTED - CHECK IT WORKS

    #Create FibreOrientations object
    fo = cs.FibreOrientations(lines=[],orientations=[])

    #Create a stage for defect storage
    if D.allStages == None:
        D.allStages = []

    stNo = len(D.allStages)+1
    stage = cs.PlyScan(stageID = stNo,sourceSystem = cs.SourceSystem(softwareName = "Polyworks"))
    D.allStages.append(stage)


    #find spline for the full part (currently for full part)

    #TODO for generic ID search without info on file, you need recursive search through
    for c in D.allComposite[0].subComponents:
        if type(c) == cs.Ply:
            if int(c.ID) == ply_ID:
                eff_ply = c

    #Open csv Orientation lines file
    temp_name = "FO_synt_data.txt" #temporarily fixed name

    #NOTE TODO sort out later
    #SYNTETIC FILE HAS ORIENTATION IN THE SAME FILE, real sample (flat) had these as 2 separate files

    with open(path+"\\"+temp_name,"r") as exc:
        excT = exc.read()

    #each row represents arrow showing local fibre direction


    for line in excT.split("\n")[:]:
        if line.count(",") > 2:
            l = cs.Line(points =[cs.Point(x=float(line.split(",")[0]),
                                          y=float(line.split(",")[1]),
                                          z=float(line.split(",")[2]))
                                ,cs.Point(
                                        x=float(line.split(",")[0])+float(line.split(",")[6])*float(line.split(",")[3]),
                                        y=float(line.split(",")[1])+float(line.split(",")[6])*float(line.split(",")[4]),
                                        z=float(line.split(",")[2])+float(line.split(",")[6])*float(line.split(",")[5]))],stageID=stNo)
        fo.lines.append(l)    


    #check if file exists
    if os.path.isfile(path+"\\"+temp_name):
        with open(path+"\\"+temp_name,"r") as exc:
            excT = exc.read()

        o = [] #orientations
        s = 0 #sum
        i = 0 # iterator
        d = 0 #difference
        for line in excT.split("\n")[:]:
            if line != "":
                o.append(float(line.split(",")[8]))
                s += float(line.split(",")[8])
                i += 1
                d += abs(float(line.split(",")[8])-float(eff_ply.orientation))

        fo.orientations = o
        fo.averageOrientation = s/i
        fo.avDiffToNominal = d
        fo.splineRelimitationRef = eff_ply.splineRelimitationRef
        fo.stageID = stNo

    else:
        print("file for FO not found")

    fo.ID = D.fileMetadata.maxID + 1
    D.fileMetadata.maxID += 1

    if eff_ply.defects == None:
        eff_ply.defects = []
    eff_ply.defects.append(fo)

    if D.allDefects == None:
        D.allDefects = []
    #append copy of the defect object to allDefects
    D.allDefects.append(eff_ply.defects[len(eff_ply.defects)-1])


    #turn data back to JSON
    json_str = serialize(D, string_output = True)

    #clean the JSON
    json_str = clean_json(json_str)

    #save the JSON
    #save as file
    print("saving as:",path+"\\"+filename+"_withFO.json")
    with open(path+"\\"+filename+"_withFO.json", 'w') as out_file:
        out_file.write(json_str)


path = "D:\\CAD_library_sampling\\CompoST_examples\\TEMPLATE_example_v70d_V1.2"
filename = "x_test_141_tols_wrinkle"
store_FO(path,filename,ply_ID=int(14))



import random
def makingFakeData(file):
    #This allows for generation of synthetic orientation data (as provided by Polyworx) 

    #open .wrl with default point
    vec,f_point = wrm2(file,Multi=True)
    #f_point is the point matrix

    C = CATIA_ctrl()
    #for each point create a second point and project it on surface
    #Initiate CATIA interaction
    C.CAT = win32com.client.dynamic.DumbDispatch('CATIA.Application')
    C.doc = C.CAT.ActiveDocument
    C.cat_name = C.CAT.ActiveDocument.Name

    C.part = C.doc.Part
    C.HSF = C.part.HybridShapeFactory

    C.bodies = C.part.HybridBodies

    C.b_list = []
    body1 = C.bodies.Add()
    body1.Name="Projects"
    C.b_list.append(body1)
    body2 = C.bodies.Add()
    body2.Name="PTS_step"
    C.b_list.append(body2)

    orientations = []

    for i in range(0,np.size(f_point,0)):

        #direction vector
        mdl = random.randint(15,80)/10

        yDir = random.randint(-30*int(mdl),30*(int(mdl)))/100
        dVec = np.asarray([[mdl,yDir,0.5]])
        #optional (randomness to vector) 


        #calc the actual angle
        angle = math.atan(yDir)
        angle = angle*180/math.pi
        orientations.append(angle)

        point=C.HSF.AddNewPointCoord(f_point[i,0]+dVec[0,0],f_point[i,1]+dVec[0,1],f_point[i,2]+dVec[0,2])

        body2.AppendHybridShape(point)
        r1 = C.part.CreateReferenceFromObject(point) 

        parameters1 = C.part.Parameters
        
        hybridBody2 = C.bodies.Item("main_shape")
        hybridShapes2 = hybridBody2.HybridShapes
        hybridShapeAssemble1 =  hybridShapes2.Item("MainS")
        #hybridShapeSurfaceExplicit1 = parameters1.Item("MainS")

        r2 = C.part.CreateReferenceFromObject(hybridShapeAssemble1)

        pr = C.HSF.AddNewProject(r1, r2)

        body1.AppendHybridShape(pr)

    selection1 = C.doc.Selection
    selection1.Clear() # added recently delete if error
    visPropertySet1 = selection1.VisProperties
    selection1.Add(body2)
    visPropertySet1 = visPropertySet1.Parent
    visPropertySet1.SetShow(1)
    selection1.Clear()

    C.part.Update()
    nf = "D:\\CAD_library_sampling\\CompoST_examples\\FO_fake_data\\x_test_141_pointsOnly_3.wrl"
    C.doc.ExportData("D:\\CAD_library_sampling\\CompoST_examples\\FO_fake_data\\x_test_141_pointsOnly_3.wrl", "wrl")

    #(here check how new points ordered)

    #for each point that already existed, find the relevant point
    #open .wrl with default point
    vec_2,f_point_2 = wrm2(nf,Multi=True)

    #check sizes
    print("f1", np.size(f_point,0))
    print("f2",np.size(f_point_2,0))

    #initiate storage string
    FO = ""
    #Loop through all points
    for i in range(0,np.size(f_point,0)):
        if i !=0:
            FO += "\n"
        X = f_point[i,0]
        Y = f_point[i,1]
        Z = f_point[i,2]
        
        #iF jF kF are the full vector (not unit)
        iF = f_point_2[i,0]-X
        jF = f_point_2[i,1]-Y
        kF = f_point_2[i,2]-Z
        LEN = np.sqrt((iF)**2+(jF)**2+(kF)**2)
        FullVec = np.asarray([iF,jF,kF])/LEN
        I = FullVec[0]
        J = FullVec[1]
        K = FullVec[2]
        NM = "Orientation Line "+str(i)+" -meas-"
        a = orientations[i]

        FO += str(X)+","+str(Y)+","+str(Z)+","+str(I)+","+str(J)+","+str(K)+","+str(LEN)+","+str(NM)+","+str(a)

    #create line in .txt (initial point + vector + lenght + string as per example)
    f = open("D:\\CAD_library_sampling\\CompoST_examples\\FO_fake_data\\FO_synt_data.txt", "w")
    f.write(FO)
    f.close()

    return()


import numpy as np 
import os
    
def wrm2(file,Multi = False):
    #Supports collection of geometry information (vecotr/point coordinates) from Catia
    #creates temporary file to export vector and point:
    #C:\Users\jk17757\Local Documents\python\TheProject\CatiaFiles\wrmmm
    #IDP_scriptsource_1902_A001_JK.wrl
    fl = open(file, "rt")
    flstr1 = fl.read() 
    vec = np.zeros([1,3])
    #interogates the .wrl file and creates vector data:
    # ~~~ check for when there is no vector ~~~ error handling to be added ~~~~~
    if "geometry  IndexedLineSet" in flstr1: 
        flstr = flstr1.split("geometry  IndexedLineSet")[1]
        flstr = flstr.split("[")[1]
        flstr = flstr.split("]")[0]
        p1 = flstr.split(",")[0]
        p2 = flstr.split(",")[1]
        x1 = float(p1.split(" ")[1])
        y1 = float(p1.split(" ")[2])
        z1 = float(p1.split(" ")[3])
        x2 = float(p2.split(" ")[1])
        y2 = float(p2.split(" ")[2])
        z2 = float(p2.split(" ")[3])
        vec[0,0] = x2 - x1
        vec[0,1] = y2 - y1
        vec[0,2] = z2 - z1
    
    #interogates the .wrl file and creates point data:
    # ~~~ more error handling required ~~~ what if multiple points are present... etc..~~~~~
    if Multi == False:
        f_point = np.zeros([1,3])
        if "geometry PointSet" in flstr1: 
            flstr = flstr1.split("geometry PointSet")[1]
            flstr = flstr.split("[")[1]
            flstr = flstr.split("]")[0]
            p1 = flstr.split(",")[0]
            f_point[0,0] = float(p1.split(" ")[1])
            f_point[0,1] = float(p1.split(" ")[2])
            f_point[0,2] = float(p1.split(" ")[3])

        f_point = np.delete(f_point,0,axis=0)

    elif Multi == True:
        cnt = flstr1.count("geometry PointSet")
        f_point = np.zeros([cnt,3])
        i = 0
        while i < cnt:
            flstr = flstr1.split("geometry PointSet")[i+1]
            flstr = flstr.split("[")[1]
            flstr = flstr.split("]")[0]
            p1 = flstr.split(",")[0]
            f_point[i,0] = float(p1.split(" ")[1])
            f_point[i,1] = float(p1.split(" ")[2])
            f_point[i,2] = float(p1.split(" ")[3])
            i = i + 1

    
    #closes the .wrl file
    fl.close()
    #~~~~~the remove should have "finally" clause, needs to always remove the file or next sim will fail~~~~
    #os.remove("C:\\temp\\xxx.wrl")
    #print(f_point,"f_point")
    return(vec, f_point)
    
    


#file = "D:\\CAD_library_sampling\\CompoST_examples\\FO_fake_data\\x_test_141_pointsOnly_ff.wrl"
#makingFakeData(file)
    
