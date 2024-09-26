#this module collects utility scripts for importing information from reference files
from stl import mesh
import CompositeStandard as cs
from pydantic import BaseModel
from jsonic import serialize, deserialize
from CATIA.CATIA_utils import CAT_points


def clean_json(strin):
    #strin = input json string to clean
    s = strin.replace("{","\n{\n")
    s = s.replace("}","\n}\n")


    tabs = 0
    new_str = ""
    for line in s.split("\n")[:]:
        
        if "}" in line:
            tabs = tabs - 1

        for ii in range(0,tabs):
            new_str += "   "
        new_str += line+"\n"

        if "{" in line:
            tabs = tabs + 1
    #returns a human readable JSON
    return(new_str)


def import_stl_v1(file):
    #v1 simply stores elements as list of points

    msh = mesh.Mesh.from_file(file)

    #for each line in data
    AM = cs.AreaMesh()
    AM.meshElements = []
    for line in msh.data:
        
        this_el = cs.MeshElement(nodes=[])
        #for each point
        for pt in line[1]:
            #check if pt in list already
            pt2 = cs.Point(x= pt[0],y =pt[1],z = pt[2])
            this_el.nodes.append(pt2)            
            
        #append element with node refs.
        #print(this_el)
        AM.meshElements.append(this_el)

    #return list of points and list of elements in CompositeStandard format
    
    return(AM)

def import_stl_v0(file):
    #OBSOLETE 


    #v0 creates separate point list and element list with references

    msh = mesh.Mesh.from_file(file)

    #for each line in data
    points = []
    points_lstr  = []
    elements = []
    for line in msh.data:
        this_el = []
        #for each point
        for pt in line[1]:
            #check if pt in list already
            pt2 = [pt[0],pt[1],pt[2]]
            pt_str = str(pt2)
            c = method_reverse_lookup([pt_str],points_lstr)
            
            if c == -1:
                #add pt to list
                points.append(pt2)
                points_lstr.append(pt_str)
                c = len(points)
            this_el.append(c)
        #append element with node refs.
        elements.append(this_el)

    #return list of points and list of elements
    print(points)
    print(elements)
    return(points, elements)



def splitDefects(AM):
    #splits multiple part .stl into separate meshes

    #separate meshes
    allM = []

    for e in AM.meshElements:
        allocated = False
        to_remove_ID = 0
        multi_aloc = False
        for n in e.nodes[:]:
        
            
            for i,M in enumerate(allM):
                if allocated == False:

                    for e2 in M.meshElements:
                        for n1 in e2.nodes[:]:
                            if n1 == n:
                                
                                allocated = True
                                M.meshElements.append(e)
                                rm = i
                                break
                        if allocated == True:
                            break
                elif allocated == True:

                    #if allocated twice, merge
                    multi_aloc = False

                    for iii,M2 in enumerate(allM):
                        if iii != rm:
                            for e2 in M2.meshElements:
                                for n1 in e2.nodes[:]:
                                    if n1 == n:
                                        multi_aloc = True
                                        rm_a = iii
                                        #merge the two meshes
                                        break
                                if multi_aloc == True:
                                    break

                    if multi_aloc == True:
                        print("here 2")
                        ii = 0
                        l = len(allM[rm_a].meshElements)
                        while ii < l:
                            
                            allM[rm].meshElements.append(allM[rm_a].meshElements[ii])
                            ii += 1

                        #currently one removal at a time - assumed 1 element will connect max 2  pre-existing
                        to_remove_ID = rm_a
                        #only allow for two regions merging at once
                        break

            if multi_aloc == True:
                #prevenets other nodes from re-allocating elements
                break
                
            
        #removed merged Ms
        print("tri",to_remove_ID)
        if to_remove_ID != 0:
            print("HEREE 333",to_remove_ID)
            del allM[to_remove_ID]
        to_remove_ID == 0

        #create new M if element does not belong
        if allocated == False:
            am = cs.AreaMesh()
            am.meshElements = [e]
            #am.meshElements.append(e)
            allM.append(am)

        print("current number:", len(allM))
        for M in allM:
            print(len(M.meshElements))

    return(allM)

'''

AM = import_stl_v1("source_files\\WO4502_SO.stl")
#print(len(AM.meshElements))
allM = splitDefects(AM)


F = cs.CompositeDB()
F.allGeometry = []
for M in allM:
    F.allGeometry.append(M)

json_str = serialize(F, string_output = True)
#json_str = pprint.pformat(json_str,indent=2).replace("'",'"')
#json_str = clean_json(json_str)

#save as file
with open("TESTING_SPLIT.json", 'w') as out_file:
    out_file.write(json_str)

'''


def read_show(file="TESTING_SPLIT.json"):

    with open(file,"r") as fl:
        json_str= fl.read()
    
        D = deserialize(json_str,string_input=True)



    i = 0 
    while i < 22:
        print(i)


        seg = D.allGeometry[i]

        dupli = []
        for e in seg.meshElements:
            for n in e.nodes:
                if n not in dupli:

                    dupli.append(n)

        CAT_points(dupli,i)

        i = i + 1




#read_show()
 