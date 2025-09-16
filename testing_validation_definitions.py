
from CompoST import CompositeStandard as cs
from CompoST import CompositeStandard
from CompoST import Utilities
from jsonic import serialize, deserialize
#from utils import reLink
#from STL.file_utils import clean_json


def AddSomeAxis(path,filename):

    with open(path+"\\"+filename+"_layup.json","r") as in_file:
        json_str= in_file.read()

    #turn file into workable classes
    D = deserialize(json_str,string_input=True)

    #re-link - if relevant
    D = Utilities.reLink(D)

    pt0 = cs.Point(x=0,y=0,z=0)
    pt1 = cs.Point(x=10,y=0,z=0)
    pt2 = cs.Point(x=0,y=10,z=0)

    D.allGeometry.append(cs.AxisSystem(o_pt=pt0,x_pt=pt1,y_pt=pt2,ID=D.fileMetadata.maxID+1))
    D.fileMetadata.maxID += 1

    #turn data back to JSON
    json_str = serialize(D, string_output = True)

    #clean the JSON
    json_str = Utilities.clean_json(json_str)

    #save the JSON
    #save as file
    print("saving as:",path+"\\"+filename+"_layup_plus_axis.json")
    with open(path+"\\"+filename+"_layup_plus_axis.json", 'w') as out_file:
        out_file.write(json_str)


def PredefineStages(path,filename):
    #currently only add hock function
    #TODO create a definition of standard Stages (as an example)

    with open(path+"\\"+filename+"_tols.json","r") as in_file:
        json_str= in_file.read()

    #turn file into workable classes
    D = deserialize(json_str,string_input=True)

    #re-link - if relevant
    D = Utilities.reLink(D)

    if D.allStages == None:
        D.allStages = []

    D.allStages.append(cs.PlyScan(memberName = "PlyScanning",stageID=len(D.allStages)+1,SourceSystem=cs.SourceSystem(softwareName = "Polyworkx"),
                                  processRef="ReferenceProcessX"))
    
    D.allStages.append(cs.Stage(memberName = "FixingPlies",stageID=len(D.allStages)+1,
                                processRef="ReferenceProcessX2"))
     
    #turn data back to JSON
    json_str = serialize(D, string_output = True)

    #clean the JSON
    json_str = Utilities.clean_json(json_str)

    #save the JSON
    #save as file
    print("saving as:",path+"\\"+filename+"_loggedStages.json")
    with open(path+"\\"+filename+"_loggedStages.json", 'w') as out_file:
        out_file.write(json_str)


#NOT WORKING RIGHT NOW

def TestIDMat():
    path = "Tests\\ForTests\\x_test_142_layup.json"
    with open(path,"r") as in_file:
        json_str= in_file.read()

    #turn file into workable classes
    D = deserialize(json_str,string_input=True)

    #re-link - if relevant
    D = Utilities.reLink(D)

    D.allMaterials[0].E1 = 200000

    testedID = D.allComposite[0].subComponents[0].material.E1

    return(testedID)


# path = "D:\\CAD_library_sampling\\CompoST_examples\\TEMPLATE_example_v71a_V1"
# filename = "x_test_142"

# #AddSomeAxis(path,filename)
# PredefineStages(path,filename)

#x = TestIDMat()
#print(x)