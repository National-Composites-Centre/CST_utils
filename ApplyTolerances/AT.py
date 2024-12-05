import CompositeStandard as cs
from CompositeStandard import *
from pydantic import BaseModel
import importlib
from utils import reLink
from STL.file_utils import clean_json
from jsonic import serialize, deserialize
from CATIA.CATIA_utils import display_file, CATIA_ctrl
import tkinter.messagebox as msg
import itertools
import win32com.client.dynamic
from CATIA.vecEX3 import wrmmm

import math

#TKINTER UI
import tkinter as tk
from tkinter import ttk
from tkinter import OptionMenu, Frame, IntVar

#apply tolerances

#This set of functions enables UI that allows user to specify tolerances for a component
#This relies on prescribed CompositeStandard (CompoST) tolerances.

#spline relim, can be taken from loaded file (have design at the start of this process)


class TolLine(BaseModel):

    # Object corresponding to one tolerance object, but including local UI and temporary parameters

    main_button: Optional[object] = Field(None)
    ref_pos: Optional[int] = Field(None)
    delete_button: Optional[object] = Field(None)
    value_button: Optional[object] = Field(None)
    tol_obj: Optional[object] = Field(None)
    var_inputs: Optional[list[object]] = Field(None) #field objects
    cat_button: Optional[object] = Field(None)
    relim: Optional[str] = Field(None)
    splineRelimitation: Optional[object] = Field(None)
    splineRelimitationRef: Optional[int] = Field(None)

def tol_list():
    #initiate empty list
    #class_names = [name for name, obj in globals().items() if isinstance(obj, type)]
    class_types = [obj for name, obj in globals().items() if isinstance(obj, type)]

    tolOptions = []
    #print(class_types)
    for c in class_types:
        for e in c.__mro__:
            if e == cs.Tolerance:
                #avoid Tolerance parent class itself
                if str(c) != """<class 'CompositeStandard.Tolerance'>""":
                    tolOptions.append(c)

    return(tolOptions)


def pts100(sp,C,hs,dir = False,no_p = 100):
    # Adding new body to part1
    body1 = C.bodies.Add()
    # Naming new body as "wireframe"
    body1.Name="ref"+str(sp)
    
    # Adding new body to part1
    body2 = C.bodies.Add()
    # Naming new body as "wireframe"
    body2.Name="output"+str(sp)
    hs = C.b_list[1].HybridShapes
    hpo1 = hs.Item(str(sp))
    ref1 = C.part.CreateReferenceFromObject(hpo1)
    
    #reference point on default - does not need to be on part
    point=C.HSF.AddNewPointCoord(0,0,0)
    body1.AppendHybridShape(point) 
    point.Name="p1"
    ref2 = C.part.CreateReferenceFromObject(point)
    selection1 = C.doc.Selection
    visPropertySet1 = selection1.VisProperties
    selection1.Add(point)
    visPropertySet1 = visPropertySet1.Parent
    visPropertySet1.SetShow(1)
    
    #iterate to add 100 equidistant points on the spline - irrespective of lenght
    i = 0
    while i < no_p:
        hpc1 = C.HSF.AddNewPointOnCurveWithReferenceFromPercent(ref1, ref2, i/no_p, dir)
        body2.AppendHybridShape(hpc1)
        i = i + 1
        
    C.part.Update()
    #export .wrl with only the latest spline points visible
    C.doc.ExportData("C:\\temp\\xxx.wrl", "wrl")
    #standard .wrl interogation to obtain point locations
    vec, x = wrmmm(Multi = True)
    #corrects for extra 0,0,0 point
    x = np.delete(x,0,axis=0)

    return(x)





def SaveTols(D,yp_list):

    #first check relimitation references which could be stored in local

    for yp in yp_list:
        if yp.splineRelimitation != None:
            yp.tol_obj.splineRelimitation = yp.splineRelimitation
        if yp.splineRelimitationRef != None:
            yp.tol_obj.splineRelimitationRef = yp.splineRelimitationRef

    #turn data back to JSON
    json_str = serialize(D, string_output = True)

    #clean the JSON
    json_str = clean_json(json_str)

    #save the JSON
    #save as file
    print("saving as:",path+"\\"+filename+".json")
    with open(path+"\\"+filename+"_tols.json", 'w') as out_file:
        out_file.write(json_str)

    #ttk pop-up to check the user has started CATIA
    msg.showwarning(title="User interaction",message="The new JSON has been saved as "+path+"\\"+filename+"_tols.json")

    return(D)


def SaveOBJ(o,subWin):

    #add relimitation

    #TODO keep ignores the same, or find a diff. mechanic for saving below
    ignore = ["stageID","deactivate_stageID","additionalParameters","additionalProperties",
                        "ID","axisSystemID","splineRelimitation","splineRelimitationRef","active"]

    #loop through all attributes
    i = 0
    for at in o.tol_obj.__dict__:

        if at not in ignore:

            print(o.var_inputs, "o.var_inputs")
            setattr(o.tol_obj,at,o.var_inputs[i].get())
            
            i += 1

    subWin.destroy()
  
def DefineTol(event,yP3_var,yp_list):

    yP3 = yP3_var.get()
    for o in yp_list: 
        if o.ref_pos == yP3:
            
            atrs = o.tol_obj.__dict__

            # create app
            subWin = tk.Tk()
            subWin.title("Specify Parameters")
            subWin.geometry("510x610")


            my_frame = Frame(subWin, width=500, height=600) 
            my_frame.pack() # Note the parentheses added here

            subWin.resizable(True,True)

            posy = 10
            posx = 5

            #ignore these attributes
            ignore = ["stageID","deactivate_stageID","additionalParameters","additionalProperties",
                        "ID","axisSystemID","splineRelimitation","splineRelimitationRef","active"]
            #TODO axisSystemID selection add - interactive?

            o.var_inputs = []
            #loop through all attributes
            for at in atrs:

                #create name and input field for each attribute
                if at not in ignore:
                    l = ttk.Label(subWin, text = at,width = 80)
                    l.place(x=posx,y=posy)

                    it = ttk.Entry(subWin,width = 40 )
                    #if values already availble, display them
                    if atrs[at] != None:
                        it.insert(0,str(atrs[at]))
                    it.place(x=posx+160,y=posy)
                    posy += 30

                    o.var_inputs.append(it)
                    
            #create button that submits the info and closes the subWindow
            button = ttk.Button(my_frame,text="Save",command= lambda: SaveOBJ(o,subWin))
            button.place(x=60,y=posy)

            subWin.mainloop()



def DeleteTol(event,yP3_var,yp_list):

    yP3 = yP3_var.get()
    for o in yp_list:
        if o.ref_pos == yP3:
            #delete from UI
            o.delete_button.destroy()
            o.value_button.destroy()
            o.main_button.destroy()

            #delete from list
            yp_list.remove(o)



def CreateTwo(D, event,yP2_var,yp_list):

    yP2 = yP2_var.get()
    class_selected = event.widget.get()
    #print(yp_list)
    for o in yp_list:
        if o.ref_pos == yP2:
            if o.delete_button == None:

                yP3_var = IntVar(value=yP2)

                button1 = ttk.Button(my_frame,text="Define",command= lambda: DefineTol(event,yP3_var,yp_list))
                button1.place(x=400,y=yP2)
                button2 = ttk.Button(my_frame,text="Delete",command= lambda: DeleteTol(event,yP3_var,yp_list))  
                button2.place(x=490,y=yP2)

                o.delete_button = button2
                o.value_button = button1

            #regardless of weather buttons needed generating
            module_name = "CompositeStandard"
            module = importlib.import_module(module_name)
            class_name = class_selected.strip("<>").split("'")[1].split('.', 1)[1]
            class_ = getattr(module,class_name)
            o.tol_obj = class_()

            #also add to tolerances immediately 
            if D.allTolerances == None:
                D.allTolerances = []

            o.tol_obj.ID = D.fileMetadata.maxID + 1
            D.allTolerances.append(o.tol_obj)
            D.fileMetadata.maxID += 1


def AddTolLine(D,yP_var,yp_list):

    yP = yP_var.get()
    yP = yP + 30
    yP_var.set(yP)

    yP2_var = IntVar(value=yP)
    combo = ttk.Combobox(my_frame,state="readonly",values=toll,width=60,height=20)
    combo.bind("<<ComboboxSelected>>", lambda event: CreateTwo(D,event,yP2_var,yp_list))
    combo.place(x=0,y=yP)

    #create the object
    t = TolLine(main_button = combo,ref_pos=yP)
    yp_list.append(t)
    button.place(x=20,y=button.winfo_y()+30)
    buttonS.place(x=20,y=buttonS.winfo_y()+30)
    button5.place(x=20,y=button5.winfo_y()+30)


def CAT_selection(rp,yp_list,C):

    c_sel = C.doc.Selection
    
    sel_obj = None
    for yp in yp_list:
        if rp == yp.ref_pos:
            #from user selection
            try:
                sel_obj = c_sel.Item(1).Value.Name

                yp.relim = str(sel_obj)
                yp.cat_button.configure(text = str(sel_obj))
 
            except:
                print("please select an object first")
                #TODO popup

            if sel_obj != None: #making sure above exception wasn't triggered 
                #TODO Somewhere instruct user not to name CATIA objects using ID...
                if "ID" in yp.relim:
                    #find the relimitation object (in geometry)
                    for g in D.allGeometry:
                        if str(g.ID) == yp.relim.split("ID")[1]:
                            yp.splineRelimitation = g
                            yp.splineRelimitationRef = g.ID

                    print("appended to existent spline")

                else:
                    #in case the object was manually created in the just opened CATIA window
                    pts = pts100(yp.relim,C,c_sel)

                    #now figure out if spline is closed
                    tdist = math.sqrt((pts[0,0]-pts[98,0])**2+(pts[0,1]-pts[98,1])**2+(pts[0,2]-pts[98,2])**2)

                    #TODO save closed/open spline - used to create sharp corners etc
                    if tdist < 12: #arbitrary 5mm treshold
                        sp_closed = "closed spline"
                    else:
                        sp_closed = "open spline"

                    #TODO includde "sharpness" from LD to attribute to splines
                    sp_temp_points = []
                    for ii, pt in enumerate(pts[:,0]):
                        sp_temp_points.append(cs.Point(x=pts[ii,0],y=pts[ii,1],z=pts[ii,2]))

                    if D.allGeometry == None:
                        D.allGeometry = []
                    D.allGeometry.append(cs.Spline(points=sp_temp_points, memberName = yp.relim,ID = (D.fileMetadata.maxID+1)))#,breaks=breaks)) -- breaks only once sharpness is collected
                    D.fileMetadata.maxID += 1
                    yp.splineRelimitation = D.allGeometry[len(D.allGeometry)-1]
                    yp.splineRelimitationRef = D.fileMetadata.maxID -1  #recored the ID before edit above


def enableCATIA(D,yp_list,filename,path):
    #Enables CATIA selection of objects to use as tolerance delimitation

    if (button5["text"] == "CATIA interactive - detivate"):
        button5.configure(text = "CATIA interactive - activate")
        
    else:
        #ttk pop-up to check the user has started CATIA
        msg.showwarning(title="User interaction",message="Please make sure CATIA is already running with a Part window open, then click ok. (Empty part is fine)")

        #TODO switch colour of the button to green
        button5.configure(text = "CATIA interactive - deactivate")

        #load CATIA part
        C = display_file(D)
        
        #loop through yp_list
        for yp in yp_list:
            #if button not available
            if yp.cat_button == None:
                yp.cat_button = ttk.Button(my_frame,text="[select]",command = lambda yp=yp: CAT_selection(yp.ref_pos ,yp_list,C))
                yp.cat_button.place(x=570,y=yp.ref_pos)


#currently available tolerance objects
toll = tol_list()

path = "D:\\CAD_library_sampling\\CompoST_examples\\TEMPLATE_example_v70c"
filename = "x_test_141"
with open(path+"\\"+filename+"_layup_plus_axis.json","r") as in_file:
    json_str= in_file.read()

#turn file into workable classes
D = deserialize(json_str,string_input=True)

#re-link - if relevant
D = reLink(D)

print(D.fileMetadata.maxID)

# create app
root = tk.Tk()
root.title("Tolerance definitions")
root.geometry("710x610+150+150")

yP_var = IntVar(value=0)
yp_list = []

my_frame = Frame(root, width=700, height=600) 
my_frame.pack() # Note the parentheses added here

root.resizable(True,True)

#This button adds a line for specifying tolerance, along with the corresponding object
button = ttk.Button(my_frame,text="Add Tolerance Definition",command= lambda: AddTolLine(D,yP_var,yp_list))
button.place(x=20,y=50)

#This button is used once user is happy with their defined tolerances
buttonS = ttk.Button(my_frame,text="Save All",command = lambda: SaveTols(D,yp_list))
buttonS.place(x=20,y=80)

#This button initiates interactive options with CATIA
button5 = ttk.Button(my_frame,text="CATIA interactive - activate", command = lambda: enableCATIA(D,yp_list,filename,path))
button5.place(x=20,y=110)

root.mainloop()




