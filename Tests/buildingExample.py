from CompoST import CompositeStandard as cs
from CompoST import CompositeStandard
from CompoST import Utilities
from jsonic import serialize, deserialize

import time
#STEP 1 layup definition


#STEP 2 optional, SmartDFM run


#STEP 3 Add an Axis
from testing_validation_definitions import AddSomeAxis

path = "D:\\CAD_library_sampling\\CompoST_examples\\TEMPLATE_example_v075"
filename = "x_test_142"

#AddSomeAxis(path,filename)

#
#STEP 4 Definte tolerances using AT.py
# import ApplyTolerances.AT as AT

# #currently available tolerance objects

# with open(path+"\\"+filename+"_layup_plus_axis.json","r") as in_file:
#     json_str= in_file.read()

# #turn file into workable classes
# D = deserialize(json_str,string_input=True)

# #re-link - if relevant
# D = Utilities.reLink(D)

# print(D.fileMetadata.maxID)

# #AT.start_tolerance_app(D,filename,path=path)

#STEP 5 - WRINKLE
from Wrinkle_UC.wrinkle_use_case import store_wrinkle 

t1 = time.perf_counter()

#path = "D:\\CAD_library_sampling\\CompoST_examples\\WO4502_minimized_bench_v70d\\"
#filename = "WO4502"

filename = filename+"_tols"
store_wrinkle(path,filename,splStore = True,meshStore = False)


t2 = time.perf_counter()
print("OVERALL RUNTIME:")
print(t2 - t1)



#STEP 6 - FibreOrientations


#TODO THIS IS WHERE WE CONTINUE, VERIFY THE EXAMPLE DATA IS WHERE IT NEEDS TO BE --- THEN STORE IT...!!
from Orientations_UC.orientations_use_case import store_FO

# filename = filename+"_wrinkle"
# store_FO(path,filename,ply_ID=int(15))




#STEP 7 - display this in CATIA
from CATIA.CATIA_utils import display_file

with open(path+"\\"+filename+"_wrinkle_FO.json","r") as in_file:
    json_str= in_file.read()

D = deserialize(json_str,string_input=True)
display_file(D,disp_mesh=True)
