import CompositeStandard as cs
from CompositeStandard import *
from pydantic import BaseModel
import importlib
from utils import reLink
from STL.file_utils import clean_json
from jsonic import serialize, deserialize
#apply tolerances


#open UI with drop-down offering available tolerance definitions





#when 1 is selected fields are provided based on paramaters available

#spline relim, can be taken from loaded file (have design at the start of this process)

import sys, inspect
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


toll = tol_list()
print(toll)



#create a drop-down in the UI to load toll into


#use __getvar__ to obtain editable variables  to fill 


#use load definition in CATIA and store objects shown in FLAT dictionary with IDs


#when stored, append object to selected ID  --- CATIA used to match ID in user friendly manner


#



#TKINTER UI
import tkinter as tk
from tkinter import ttk
from tkinter import OptionMenu, Frame, IntVar

class TolLine(BaseModel):#

    main_button: Optional[object] = Field(None)
    ref_pos: Optional[int] = Field(None)
    delete_button: Optional[object] = Field(None)
    value_button: Optional[object] = Field(None)
    tol_obj: Optional[object] = Field(None)
    var_inputs: Optional[list[object]] = Field(None)

def SaveTols(D,yp_list):

    #assign ID!
    ID = D.fileMetadata.maxID
    
    if D.allTolerances == None:
        D.allTolerances = []

    for tol in yp_list:
        ID = ID + 1
        tol.tol_obj.ID = ID
        D.allTolerances.append(tol.tol_obj)

    #save max ID
    D.fileMetadata.maxID = ID

        #turn data back to JSON
    json_str = serialize(D, string_output = True)

    #clean the JSON
    json_str = clean_json(json_str)

    #save the JSON
    #save as file
    print("saving as:",path+"\\"+filename+".json")
    with open(path+"\\"+filename+"_.tolsjson", 'w') as out_file:
        out_file.write(json_str)
    return(D)

def SaveOBJ(yP3_var,yp_list,subWin):

    #add relimitation
    
    yP3 = yP3_var.get()
    
    #TODO keep ignores the same, or find a diff. mechanic for saving below
    ignore = ["stageID","deactivate_stageID","additionalParameters","additionalProperties",
                        "ID","axisSystemID","splineRelimitation","splineRelimitationRef","active"]

    for o in yp_list: 
        if o.ref_pos == yP3:
            #loop through all attributes
            i = 0
            for at in o.tol_obj.__dict__:

                if at not in ignore:

                    print(o.var_inputs, "o.var_inputs")
                    setattr(o.tol_obj,at,o.var_inputs[i].get())
                    
                    i += 1

    subWin.destroy()

    #print(o.tol_obj)
    
def DefineTol(event,yP3_var,yp_list):

    yP3 = yP3_var.get()
    for o in yp_list: 
        if o.ref_pos == yP3:
            
            atrs = o.tol_obj.__dict__
            #print(atrs)


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
            #TODO spliner relims to be done internactively 

            o.var_inputs = []
            #loop through all attributes
            for at in atrs:
                #print(at)
                #create name and input field for each attribute
                if at not in ignore:
                    l = ttk.Label(subWin, text = at,width = 80)
                    l.place(x=posx,y=posy)

                    it = ttk.Entry(subWin,width = 40,text = atrs[at] )
                    it.place(x=posx+160,y=posy)
                    posy += 30

                    o.var_inputs.append(it)
                    
            #create button that submits the info and closes the subWindow
            button = ttk.Button(my_frame,text="Save",command= lambda: SaveOBJ(yP_var,yp_list,subWin))
            button.place(x=60,y=posy)

            subWin.mainloop()

            
            #print("x")


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



def CreateTwo(event,yP2_var,yp_list):

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




def AddTolLine(yP_var,yp_list):

    yP = yP_var.get()
    yP = yP + 30
    yP_var.set(yP)

    yP2_var = IntVar(value=yP)
    combo = ttk.Combobox(my_frame,state="readonly",values=toll,width=60,height=20)
    combo.bind("<<ComboboxSelected>>", lambda event: CreateTwo(event,yP2_var,yp_list))
    combo.place(x=0,y=yP)

    #create the object
    t = TolLine(main_button = combo,ref_pos=yP)
    yp_list.append(t)
    button.place(x=20,y=button.winfo_y()+30)
    buttonS.place(x=20,y=buttonS.winfo_y()+30)
    #print(yp_list)



path = "D:\\CAD_library_sampling\\CompoST_examples\\orientation_map_example"
filename = "sq_test_001"
with open(path+"\\"+filename+"_layup.json","r") as in_file:
    json_str= in_file.read()

#turn file into workable classes
D = deserialize(json_str,string_input=True)

#re-link - if relevant
D = reLink(D)


# create app
root = tk.Tk()
root.title("Tolerance definitions")
root.geometry("610x610+150+150")

yP_var = IntVar(value=0)
yp_list = []

my_frame = Frame(root, width=700, height=600) 
my_frame.pack() # Note the parentheses added here

root.resizable(True,True)

button = ttk.Button(my_frame,text="Add Tolerance Definition",command= lambda: AddTolLine(yP_var,yp_list))
button.place(x=20,y=50)

buttonS = ttk.Button(my_frame,text="Save All",command = lambda: SaveTols(D,yp_list))
buttonS.place(x=20,y=80)

root.mainloop()




