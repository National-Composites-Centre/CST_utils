import CompositeStandard as cs
from CompositeStandard import *
from pydantic import BaseModel
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



#call this function to store specific tolerance
def StoreTol(D,tolerance,sp_obj=None):
    #D main CompoST object
    #tolerance is the single tolerance object
    #sp_obj is used where the tolerance is specified to take effect for specific object rather than full part based on relimitation

    return()


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

    print("x")


def CreateTwo(event,yP2_var,yp_list):

    yP2 = yP2_var.get()
    print(yp_list)
    for o in yp_list:
        if o.ref_pos == yP2:
            if o.delete_button == None:

                yP3_var = IntVar(value=yP2)

                button1 = ttk.Button(my_frame,text="Define")
                button1.place(x=400,y=yP2)
                button2 = ttk.Button(my_frame,text="Delete",command= lambda: DeleteTol(event,yP3_var,yp_list))  
                button2.place(x=490,y=yP2)

                o.delete_button = button2
                o.value_button = button1

            

def AddTolLine(yP_var,yp_list):

    yP = yP_var.get()
    yP = yP + 20
    yP_var.set(yP)

    yP2_var = IntVar(value=yP)
    combo = ttk.Combobox(my_frame,state="readonly",values=toll,width=60,height=20)
    combo.bind("<<ComboboxSelected>>", lambda event: CreateTwo(event,yP2_var,yp_list))
    combo.place(x=0,y=yP)

    #create the object
    t = TolLine(main_button = combo,ref_pos=yP)
    yp_list.append(t)
    button.place(x=20,y=button.winfo_y()+20)
    print(yp_list)

 

# create app
root = tk.Tk()
root.title("xxx")
root.geometry("710x710+150+150")


yP_var = IntVar(value=0)
yp_list = []


my_frame = Frame(root, width=700, height=700) 
my_frame.pack() # Note the parentheses added here

root.resizable(True,True)

button = ttk.Button(my_frame,text="Add Tolerance Definition",command= lambda: AddTolLine(yP_var,yp_list))
button.place(x=20,y=50)



root.mainloop()




