from jsonic import serialize, deserialize

import CompositeStandard as cs

import numpy as np
import os

from utils import reLink

from STL.file_utils import clean_json



def store_FO(path,filename,ply_ID,zone=None):
    #This is now done per ply, but could also be modified to do per zone
    
    #load composite definition JSON
    
    with open(path+"\\"+filename+"_layup.json","r") as in_file:
        json_str= in_file.read()

    #turn file into workable classes
    D = deserialize(json_str,string_input=True)

    #re-link - if relevant
    D = reLink(D) #TODO UNTESTED - CHECK IT WORKS

    #Create FibreOrientations object
    fo = cs.FibreOrientations(lines=[],orientations=[])


    #find spline for the full part (currently for full part)

    #TODO for generic ID search without info on file, you need recursive search through
    for c in D.allComposite[0].subComponents:
        print("xx",type(c))
        print("yy",cs.Ply)
        if type(c) == cs.Ply:
            if int(c.ID) == ply_ID:
                eff_ply = c

    #Open csv Orientation lines file


    with open(path+"\\"+filename+"_FibreOrientationsLines.csv","r") as exc:
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
                                        z=float(line.split(",")[2])+float(line.split(",")[6])*float(line.split(",")[5]))])
        fo.lines.append(l)    


    #check if file exists
    if os.path.isfile(path+"\\"+filename+"_FibreOrientationsOri.csv"):
        with open(path+"\\"+filename+"_FibreOrientationsOri.csv","r") as exc:
            excT = exc.read()

        o = [] #orientations
        s = 0 #sum
        i = 0 # iterator
        d = 0 #difference
        for line in excT.split("\n")[1:]:
            if line != "":
                o.append(float(line))
                s += float(line)
                i += 1
                d += abs(float(line)-float(eff_ply.orientation))

        fo.orientations = o
        fo.averageOrientation = s/i
        fo.avDiffToNominal = d
        fo.splineRelimitationRef = eff_ply.splineRelimitationRef


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
    print("saving as:",path+"\\"+filename+".json")
    with open(path+"\\"+filename+".json", 'w') as out_file:
        out_file.write(json_str)


path = "D:\\CAD_library_sampling\\CompoST_examples\\orientation_map_example"
filename = "sq_test_001"
store_FO(path,filename,ply_ID=int(8))


#(how to use this?)(compare to tolearnace?)
