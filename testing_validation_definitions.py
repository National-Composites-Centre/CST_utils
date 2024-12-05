
import CompositeStandard as cs
from jsonic import serialize, deserialize
from utils import reLink
from STL.file_utils import clean_json

def AddSomeAxis():

    path = "D:\\CAD_library_sampling\\CompoST_examples\\TEMPLATE_example_v70c"
    filename = "x_test_141"
    with open(path+"\\"+filename+"_layup.json","r") as in_file:
        json_str= in_file.read()

    #turn file into workable classes
    D = deserialize(json_str,string_input=True)

    #re-link - if relevant
    D = reLink(D)

    pt0 = cs.Point(x=0,y=0,z=0)
    pt1 = cs.Point(x=10,y=0,z=0)
    pt2 = cs.Point(x=0,y=10,z=0)

    D.allGeometry.append(cs.AxisSystem(o_pt=pt0,x_pt=pt1,y_pt=pt2,ID=D.fileMetadata.maxID+1))
    D.fileMetadata.maxID += 1

    #turn data back to JSON
    json_str = serialize(D, string_output = True)

    #clean the JSON
    json_str = clean_json(json_str)

    #save the JSON
    #save as file
    print("saving as:",path+"\\"+filename+".json")
    with open(path+"\\"+filename+"_layup_plus_axis.json", 'w') as out_file:
        out_file.write(json_str)

#AddSomeAxis()

def PredefineStages(path):

    filename = "x_test_141"
    with open(path+"\\"+filename+"_tols.json","r") as in_file:
        json_str= in_file.read()

    #turn file into workable classes
    D = deserialize(json_str,string_input=True)

    #re-link - if relevant
    D = reLink(D)

    if D.allStages == None:
        D.allStages = []

    D.allStages.append(cs.PlyScan(memberName = "PlyScanning",stageID=len(D.allStages)+1,SourceSystem=cs.SourceSystem(softwareName = "Polyworkx"),
                                  processRef="ReferenceProcessX"))
    
    D.allStages.append(cs.Stage(memberName = "FixingPlies",stageID=len(D.allStages)+1,
                                processRef="ReferenceProcessX2"))
     
    #turn data back to JSON
    json_str = serialize(D, string_output = True)

    #clean the JSON
    json_str = clean_json(json_str)

    #save the JSON
    #save as file
    print("saving as:",path+"\\"+filename+".json")
    with open(path+"\\"+filename+"_loggedStages.json", 'w') as out_file:
        out_file.write(json_str)



PredefineStages("D:\\CAD_library_sampling\\CompoST_examples\\TEMPLATE_example_v70c")