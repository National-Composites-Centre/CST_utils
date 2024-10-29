
from jsonic import serialize, deserialize

from CATIA.CATIA_utils import CAT_points
from STL.file_utils import import_stl_v1, clean_json
from STL.mts import MTS, meshToSpline
import CompositeStandard as cs

import numpy as np
from utils import reLink




def store_mesh(path,filename,meshStore = False, splStore = False):
    #Import pre-existent layup definition file

    #open file
    D = cs.CompositeDB()

    #Create a stage for defect storage

    if D.allStages == None:
        D.allStages = []
    if D.allGeometry == None:
        D.allGeometry = []

    stage = cs.PlyScan(stageID = len(D.allStages)+1,sourceSystem = cs.SourceSystem(softwareName = "Polyworks"))
    D.allStages.append(stage)

    fl = path+"//"+filename+".stl"
    AM = import_stl_v1(fl)


    if splStore == True:
        #generate the spline that relimits the defect

        #This option uses the flat circle calculations - works better for complicated meshes
        #EP = meshToSpline(AM)

        #This option uses number of element-node associations - works better for consistent and simple meshes
        EP = MTS(AM)

        #store the relimitation spline and reference it in defect
        D.allGeometry.append(cs.Spline(points = EP,ID = D.fileMetadata.maxID + 1))
        D.fileMetadata.maxID += 1

    #if user requires storing the area mesh itself
    if meshStore == True:
        AM.ID = D.fileMetadata.maxID + 1
        D.fileMetadata.maxID += 1
        D.allGeometry.append(AM)


    #turn data back to JSON
    json_str = serialize(D, string_output = True)

    #clean the JSON
    json_str = clean_json(json_str)

    #save the JSON
    #save as file
    print("saving as:",path+"\\"+filename+".json")
    with open(path+"\\"+filename+".json", 'w') as out_file:
        out_file.write(json_str)

    #save_to_hdf5(D, path+"\\"+filename+".h5")

#binary choice of storing the Mesh itself in JSON for each defects
#meshStore = False

#binary choise weather slipe should be generated to delimit defects
#splStore = False

#path = "D:\\CAD_library_sampling\\CompoST_examples\\WO4502_minimized_v067_no_spline\\"
#filename = "WO4502"
path = "D:\\CAD_library_sampling\\CompoST_examples\\kevNsteve"
filename = "xxx_5"
store_mesh(path,filename,splStore = False,meshStore = True)


