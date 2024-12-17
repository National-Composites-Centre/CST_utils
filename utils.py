from stl import mesh
import CompositeStandard as cs
from pydantic import BaseModel
from jsonic import serialize, deserialize

#Only leave python related utilities in this module - rest to dedicated "utils"

def method_reverse_lookup(a, b, c=None):
    #Check if [a] is in list [b] and return index c (currently only last index returned)
    reverse_lookup = {x:i for i, x in enumerate(b)}
    for i, x in enumerate(a):
        i = reverse_lookup.get(x, -1)
    return i



#BELOW FROM MAIN COMPOST REPO - ONLY COPY HERE - EDITING TO BE DONE THERE

import numpy as np
from numpy.linalg import norm
import copy

def findDupID(loc_obj,temp,dup):
    #acceptable list names
    list_names = ["subComponents","defects","nodes","points","meshElements"]

    #recursively looks through object

    #if ID is specified
    if loc_obj.ID != None:

        #if ID already exists in temp, duplicate was found
        if loc_obj.ID in temp:
            #if ID already in dup add counter
            if loc_obj.ID in dup[:,0]:
                for i in range(0,np.size(dup,0)):
                    if loc_obj.ID == dup[i,0]:
                        dup[i,1] == dup[i,1] + 1
            #if ID not in dup, add new row
            else:
                dup = np.concatenate((dup,np.asarray([[loc_obj.ID,2]])),axis = 0)
        #if ID doesnt exist in TEMP, add it, and look inside
        else:
            temp.append(loc_obj.ID)

            #specific lists accepted only for housing more nested objects
            for any_atr in dir(loc_obj):
                if any_atr in list_names:
                    new_obj = getattr(loc_obj,any_atr)
                    if new_obj != None:
                        for o in new_obj:
                            temp, dup = findDupID(o,temp,dup)
    #if ID is not specified
    else: 
        
        for any_atr in dir(loc_obj):
            if any_atr in list_names:
                new_obj = getattr(loc_obj,any_atr)
                if new_obj != None:
                    for o in new_obj:
                        temp, dup = findDupID(o,temp,dup)
            
    return(temp,dup)

def reLinkRec(D,o,f,i,nestS,nestN,NS_c,NN_c):
    #acceptable list names
    list_names = ["subComponents","defects","nodes","points","meshElements"]

    #f is the number of copies that still need to be identified
    if f > 0:
        #this is the ID I know is duplicated
        if i == o.ID:
            #if this is the first instance of ID - make a note of object to copy
            if NS_c == []:
                NS_c = copy.deepcopy(nestS)
                NN_c = copy.deepcopy(nestN)
                f = f - 1
            #if object is stored in for_copy this object is than copied into the location of current object - to re link
            else:
                #reconstruct the reference to edit D ####

                buildF = "D"
                for ii, st in enumerate(nestS):
                    buildF += "."+st +"["+str(nestN[ii])+"]"

                buildF += " = D"
                for ii, st in enumerate(NS_c):
                    buildF += "."+st +"["+str(NN_c[ii])+"]"           

                #not the cleanest, but wasn't able to make this work with getattr
                #(feel free to rework)
                print(buildF)     
                exec(buildF)
                f = f - 1
                                
        #move to other lists
        else:
            for any_atr in dir(o):
                #if next object has any accepted list nested
                if any_atr in list_names:
                    new_obj = getattr(o,any_atr)
                    if new_obj != None:
                        for ii, oo in enumerate(new_obj):
                            #objects within are also run-through
                            nestS.append(any_atr)
                            nestN.append(ii)
                            D,f,nestS,nestN,NS_c,NN_c = reLinkRec(D,oo,f,i,nestS,nestN,NS_c,NN_c)
                            nestN = nestN[:-1]
                            nestS = nestS[:-1]

    return(D,f,nestS,nestN,NS_c,NN_c)

def reLink(D):

    #Minimal testing done so far. 

    temp = []
    #first number of dup array is ID, second is number of copies
    dup = np.asarray([[0,0]])
    if D.allComposite != None:
        for o in D.allComposite:
            temp, dup = findDupID(o,temp,dup)
    if D.allGeometry != None:
        for o in D.allGeometry: 
            temp, dup = findDupID(o,temp,dup)
    if D.allDefects != None:
        for o in D.allDefects:
            temp, dup = findDupID(o,temp,dup)
    if D.allTolerances != None:
        for o in D.allTolerances:
            temp, dup = findDupID(o,temp,dup)

    #now iterate to find the objects and re-write with copy

    #nested strings
    nestS = []
    #nested object position
    nestN = []
    #object string nest for copy
    NS_c = []
    #object number nest for copy
    NN_c = []
    
    for count, i in enumerate(dup[:,0]):
        f = dup[count,1]
        #Go through all known groups of objects that could be shared and contain IDs
        #Can definitely be streamlined.
        if D.allComposite != None:
            for ii, o in enumerate(D.allComposite):
                nestS.append("allComposite")
                nestN.append(ii)
                D,f,nestS,nestN,NS_c,NN_c = reLinkRec(D,o,f,i,nestS,nestN,NS_c,NN_c)
                nestN = nestN[:-1]
                nestS = nestS[:-1]
        if D.allGeometry != None:
            for ii, o in enumerate(D.allGeometry): 
                nestS.append("allGeometry")
                nestN.append(ii)
                D,f,nestS,nestN,NS_c,NN_c = reLinkRec(D,o,f,i,nestS,nestN,NS_c,NN_c)
                nestN = nestN[:-1]
                nestS = nestS[:-1]
        if D.allDefects != None:
            for ii, o in enumerate(D.allDefects):
                nestS.append("allDefects")
                nestN.append(ii)
                D,f,nestS,nestN,NS_c,NN_c = reLinkRec(D,o,f,i,nestS,nestN,NS_c,NN_c)
                nestN = nestN[:-1]
                nestS = nestS[:-1]
        if D.allTolerances != None:
            for ii,o in enumerate(D.allTolerances):
                nestS.append("allTolerance")
                nestN.append(ii)
                D,f,nestS,nestN,NS_c,NN_c = reLinkRec(D,o,f,i,nestS,nestN,NS_c,NN_c)
                nestN = nestN[:-1]
                nestS = nestS[:-1]

    return(D)