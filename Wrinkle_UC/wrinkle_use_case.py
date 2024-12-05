
from jsonic import serialize, deserialize

#from CATIA.CATIA_utils import CAT_points
from STL.file_utils import import_stl_v1, clean_json
from STL.mts import MTS, meshToSpline, MTS_np, meshToSpline_np, meshToSpline_o3d
import CompositeStandard as cs
import h5py

import numpy as np
from utils import reLink

def save_to_hdf5(obj, file_name):
    
    #HDF5 DOES NOT CURRENTLY WORK -- TODO READ ERRORS IN EXCEPTIONS AND FIGURE OUT WHY IT STRUGGLES TO STORE SOME DATA TYPES

    obj_dict = obj.model_dump()  # Pydantic's model_dump() returns a dictionary

    # Create and save the dictionary to HDF5
    with h5py.File(file_name, 'w') as f:
        for key, value in obj_dict.items():
            # Store simple values directly
            if isinstance(value, (int, float, str)):
                if value != None:
                    print("value",value)
                    try:
                        f.attrs[key] = value
                    except:
                        print("error occured")
            # Store list or array data as datasets
            elif isinstance(value, list):
                if value != None:
                    print("value",value)
                    try:
                        f.create_dataset(key, data=value)
                    except:
                        print("error 2 occured")

def store_wrinkle(path,filename,meshStore = False, splStore = False):
    #Import pre-existent layup definition file

    #open file
    with open(path+"\\"+filename+".json","r") as in_file:
        json_str= in_file.read()

    #turn file into workable classes
    D = deserialize(json_str,string_input=True)
    
    D = reLink(D) #TODO UNTESTED - CHECK IT WORKS

    #Open csv with wrinkle info (TODO store directly to CompoST)
    with open(path+"\\"+filename+"_wrinkle.csv","r") as exc:
        excT = exc.read()

    #Create a stage for defect storage

    if D.allStages == None:
        D.allStages = []

    stage = cs.PlyScan(stageID = len(D.allStages)+1,sourceSystem = cs.SourceSystem(softwareName = "Polyworks"))
    D.allStages.append(stage)

    
    #each row represents individual wrinkle
    for line in excT.split("\n")[1:]:
        t3 = time.perf_counter()
        #stop the loop when iterating through mostly empty lines
        if line.count(",") > 2:
            print(line.split(",")[1])
            #find sequence - for now assuming defects are fully through thicknesss
            for c in D.allComposite:
                if type(c) == cs.Sequence:
                    #if no defects have been stored yet,initiate the list
                    if c.defects == None:
                        c.defects = []
                    
                    #basic wrinkle information store
                    wrinkle = cs.Wrinkle(ID = D.fileMetadata.maxID + 1)
                    wrinkle.area = float(line.split(",")[2])
                    wrinkle.location = [float(line.split(",")[3]),float(line.split(",")[4]),float(line.split(",")[5])]
                    wrinkle.maxRoC = float(line.split(",")[15])
                    wrinkle.size_x = float(line.split(",")[12])
                    wrinkle.size_y = float(line.split(",")[13])
                    wrinkle.stageID = stage.stageID

                    #Defect object ID will be added so maxID has to increase for the below
                    D.fileMetadata.maxID += 1

                    #find a file corresponding to specific wrinkle - based on listed Polywork export ID
                    pID = line.split(",")[1]
                    typeW = line.split(",")[0]
                    fl = path+"\\"+"defects\\"+filename+" "+typeW +" "+pID+".stl"

                    #TODO can also store ref. to file

                    #try opening the file
                    print("fl",fl)
                    try:
                        #extract the mesh in CompositeStandard format
                        AM = import_stl_v1(fl)
                    except:
                        print("no mesh file found for defect no:", pID)
                        AM = []

                    #if file was found
                    if AM != []:
                        if splStore == True:
                            #generate the spline that relimits the defect

                            #Overall this has some issues, and is very slow with large messy meshes.
                            #Multiple options exist, all saved int mts.py

                            #This option uses the flat circle calculations - works better for complicated meshes
                            #EP = meshToSpline(AM)
                            EP = meshToSpline_np(AM)
                            #This option uses number of element-node associations - works better for consistent and simple meshes
                            #np versions highly experimental
                            #EP = MTS_np(AM)

                            #This version uses external library to import mesh
                            #This does not require previous mesh conversion - therefore the code here could be simplified if this becomes the default
                            #EP = meshToSpline_o3d(fl)

                            #store the relimitation spline and reference it in defect
                            D.allGeometry.append(cs.Spline(points = EP,ID = D.fileMetadata.maxID + 1))
                            wrinkle.splineRelimitationRef = D.fileMetadata.maxID + 1
                            D.fileMetadata.maxID += 1

                        #if user requires storing the area mesh itself
                        if meshStore == True:
                            AM.ID = D.fileMetadata.maxID + 1
                            D.fileMetadata.maxID += 1
                            D.allGeometry.append(AM)
                            wrinkle.meshRef = AM.ID

                        if (meshStore == False) and (splStore == False):
                            wrinkle.file = "defects\\"+typeW +" Defect "+pID+".stl"
                    if D.allDefects == None:
                        D.allDefects = [wrinkle]
                    else:
                        D.allDefects.append(wrinkle)

                    
                    c.defects.append(D.allDefects[len(D.allDefects)-1])
        else:
            #breaks out if lines are empty
            break


        t4 = time.perf_counter()
        print("Wrinkle runtime: "+pID)
        print(t4 - t3)
    #turn data back to JSON
    json_str = serialize(D, string_output = True)

    #clean the JSON
    json_str = clean_json(json_str)

    #save the JSON
    #save as file
    print("saving as:",path+"\\"+filename+"_wrinkle.json")
    with open(path+"\\"+filename+"_wrinkle.json", 'w') as out_file:
        out_file.write(json_str)

    #save_to_hdf5(D, path+"\\"+filename+".h5")

#binary choice of storing the Mesh itself in JSON for each defects
#meshStore = False

#binary choise weather slipe should be generated to delimit defects
#splStore = False

import time
t1 = time.perf_counter()

#path = "D:\\CAD_library_sampling\\CompoST_examples\\WO4502_minimized_v067_no_spline\\"
#filename = "WO4502"
path = "D:\\CAD_library_sampling\\CompoST_examples\\TEMPLATE_example_v70c_V1.0"
filename = "x_test_141_tols"
store_wrinkle(path,filename,splStore = True,meshStore = True)


t2 = time.perf_counter()
print("OVERALL RUNTIME:")
print(t2 - t1)
