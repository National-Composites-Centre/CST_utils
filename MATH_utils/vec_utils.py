import numpy as np 
import scipy as sc

def anyNormal(vector,vector2= None):

    #vector 2 is optional reference vector - random none-parallel is created if not provided
    if vector2 is None:
        if abs(vector[0]) < abs(vector[1]) and abs(vector[0]) < abs(vector[2]):
            vector2 = np.array([1, 0, 0])
        elif abs(vector[1]) < abs(vector[2]):
            vector2 = np.array([0, 1, 0])
        else:
            vector2 = np.array([0, 0, 1])

    v3 = np.cross(vector,vector2)
    v3 = v3/(np.sqrt(v3[0]**2+v3[1]**2+v3[2]**2))

    return(v3)