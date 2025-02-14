from CompoST import CompositeStandard as cs
from jsonic import serialize, deserialize


#THIS CURRENTLY DOES NOT WORK #TODO
#it is intended to help users move old CompoST data to new versions

#from utils import reLink

def class_list():
    #initiate empty list
    #class_names = [name for name, obj in globals().items() if isinstance(obj, type)]
    class_types = [obj for name, obj in globals().items() if isinstance(obj, type)]

    csList = []
    for c in class_types:
        if 'CompositeStandard' in str(c):
            csList.append(c)
    #print(csList)
    return(csList)


def updateFileVersion(CompoST):

    #load old CompoST file as D
    with open(CompoST,"r") as in_file:
        json_str = in_file.read()

    #open old CompoST as dictionary
    import json
    D = json.loads(json_str)

    #re-link - if relevant
    #D = reLink(D)
    #TODO instructions to use-reLink after the adjustments, but re-link is separate from version update

    #For comparison up to date list (NOTE - need to have up-to-date CompositeStanard in this repo)
    csList = class_list()

    #recursively loop through all objects and lists 

    D = checkDictionary(D,csList)

    #print(D)

    #breakhere

    #D = deserialize(str(D),string_input=True)


    return(CompoST)

def get_class_fields(cls):
    # Extract fields and their default values
    fields = {}
    
    # Check for class annotations (e.g., Pydantic or dataclass fields)
    if hasattr(cls, "__annotations__"):
        for field_name, field_type in cls.__annotations__.items():
            default_value = getattr(cls, field_name, None)  # Get default value if available
            fields[field_name] = {"type": field_type, "default": default_value}
    
    return fields
    

def checkDictionary(D,csList):

    #listExt = ['subComponetns']

    #if this is an composite stnadard object
    changes = 0

    if 'CompositeStandard' in D['_serialized_type']:

            class_name = D['_serialized_type']

                #cls = globals().get(class_name)
            for cls in csList:

                if str(cls.__name__) in class_name:
                    intended_parameters = get_class_fields(cls)


            forDeletion = []
            for key, value in D.items():
                
                if key in csList:

                    if type(value) == dict:
                        if 'CompositeStandard' in value['_serialized_type']:

                            available = False
                            for CS in csList:

                                if key.lower() in str(CS).lower():
                                    available = True
                                    break
                            
                            #print(available)
                            if available == True:
                                D = checkDictionary(value,csList)

                            else:
                                print("The object "+str(key)+" is no longer supported."+ 
                                    "If this held important information this will need to be migrated to new object structure by user")
                                forDeletion.append(key)
                                #del D[key]  
                                changes += 1

                        #TODO
                        #if object but not CompositeStandard object
                        #this is not core, as this is only needed if external object already poluted original CompoST file

                    elif type(value) == list:
                        value = checkList(value,csList)

                else:
                    print("Parameter key: "+str(key)+" is not supposed to exist in new version, it is deleted.")
                    print("The delted values is:"+str(value))
                    forDeletion.append(key)
                    #del D[key]
                    changes += 1

            print(forDeletion)
            for kdel in forDeletion:
                del D[kdel]

            if len(D.keys()) < len(intended_parameters):
                #Add missing keys
                for k in intended_parameters:
                    if k not in D.keys():
                        #Add empty value to new field
                        D[k] = None
                        print("Added "+str(k)+" with None value")
                        changes += 1

            elif len(D.keys()) > len(intended_parameters):
                #this should no longer be the case
                print("Script error, there should not be more parameters in object now than in intended now.")
            


            #TODO what to do if parameter not available in old object that is in new
            #and vice versa ... so far only objects implemented 




    return(D)


def checkList(D,csList):

    #to distinguish between list nesting and object nesting
    for m in D:

        if type(m) == list:
            m = checkList(m,csList)

        if type(m) == dict:
            m = checkDictionary(m,csList)

    return(D)



updateFileVersion("D:\\CAD_library_sampling\\CompoST_examples\\NO_IP_v067\\x_test_141.json")



#TODO

#TO CHECK
#check that subcomponents are iterated thorugh
#make sure deletion print-outs are working
