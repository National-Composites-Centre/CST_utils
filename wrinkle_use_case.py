
from jsonic import serialize, deserialize
import CompositeStandard as cs
from CATIA_utils import CAT_points

#Import pre-existent layup definition file


#open file
with open('D:\CAD_library_sampling\CompoST_examples\WO4502_minimized\split.json',"r") as in_file:
    json_str= in_file.read()


D = deserialize(json_str,string_input=True)

pts = []
for am in D.allGeometry:
    try:
        pt = am.meshElements.nodes[0]
        if pt not in pts:
            pts.append(pt)
    except:
        print(type(am))
        print("ff")



CAT_points(pts)


#load wrinkle file


#split wrinkle file


#create spline definition for each wrinkle


#each defect allocate to sequence + add spline reference + add parameters from excel
