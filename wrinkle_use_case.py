
from jsonic import serialize, deserialize
import CompositeStandard as cs
from CATIA_utils import CAT_points
from file_utils import import_stl_v1, clean_json
from mts import MTS, meshToSpline


def store_wrinkle(path,filename,meshStore = False, splStore = False):
    #Import pre-existent layup definition file

    #open file
    with open(path+filename+"_layup.json","r") as in_file:
        json_str= in_file.read()

    #turn file into workable classes
    D = deserialize(json_str,string_input=True)

    #Open csv with wrinkle info (TODO store directly to CompoST)
    with open(path+filename+"_wrinkle.csv","r") as exc:
        excT = exc.read()

    #each row represents individual wrinkle
    for line in excT.split("\n")[1:]:
        #stop the loop when iterating through mostly empty lines
        if line.count(",") > 2:
            print(line.split(",")[1])
            #find sequence - for now assuming defects are fully through thicknesss
            for c in D.rootElements:
                if type(c) == cs.Sequence:
                    #if no defects have been stored yet,initiate the list
                    if c.defects == None:
                        c.defects = []
                    
                    #basic wrinkle information store
                    wrinkle = cs.Wrinkle(ID = D.fileMetadata.maxID + 1)
                    wrinkle.area = float(line.split(",")[2])
                    wrinkle.location = [float(line.split(",")[3]),float(line.split(",")[4]),float(line.split(",")[5])]
                    wrinkle.source = cs.SourceSystem(softwareName = "Polyworks")
                    wrinkle.maxRoC = float(line.split(",")[15])
                    wrinkle.size_x = float(line.split(",")[12])
                    wrinkle.size_y = float(line.split(",")[13])

                    #Defect object ID will be added so maxID has to increase for the below
                    D.fileMetadata.maxID += 1

                    #find a file corresponding to specific wrinkle - based on listed Polywork export ID
                    pID = line.split(",")[1]
                    typeW = line.split(",")[0]
                    fl = path+"defects\\"+typeW +" Defect "+pID+".stl"

                    #TODO can also store ref. to file

                    #try opening the file
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

                            #This option uses the flat circle calculations - works better for complicated meshes
                            #EP = meshToSpline(AM)

                            #This option uses number of element-node associations - works better for consistent and simple meshes
                            EP = MTS(AM)
                            
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

                    c.defects.append(wrinkle)
        else:
            #breaks out if lines are empty
            break

    #turn data back to JSON
    json_str = serialize(D, string_output = True)

    #clean the JSON
    json_str = clean_json(json_str)

    #save the JSON
    #save as file
    print("saving as:",path+filename+".json")
    with open(path+filename+".json", 'w') as out_file:
        out_file.write(json_str)

#binary choice of storing the Mesh itself in JSON for each defects
#meshStore = False

#binary choise weather slipe should be generated to delimit defects
#splStore = False

path = "D:\\CAD_library_sampling\\CompoST_examples\\NO_IP\\"
filename = "x_test_140"
store_wrinkle(path,filename,splStore = True,meshStore = True)
