#mts- mesh-to-spline conversion

from utils import  method_reverse_lookup
from STL.file_utils import import_stl_v1
from CATIA.CATIA_utils import bug_fixing, CAT_points
import numpy as np
import math
from sympy import Plane, Point, Point3D 


#from numpy import sqrt, dot, cross                       
#from numpy.linalg import norm
# Find the intersection of three spheres                 
# P1,P2,P3 are the centers, r1,r2,r3 are the radii       
# Implementaton based on Wikipedia Trilateration article.                              
def trilaterate(P1,P2,P3,r1,r2,r3):                      
    temp1 = P2-P1                                        
    e_x = temp1/np.linalg.norm(temp1)                              
    temp2 = P3-P1                                        
    i = np.dot(e_x,temp2)                                   
    temp3 = temp2 - i*e_x                                
    e_y = temp3/np.linalg.norm(temp3)                              
    e_z = np.cross(e_x,e_y)                                 
    d = np.linalg.norm(P2-P1)                                      
    j = np.dot(e_y,temp2)                                   
    x = (r1*r1 - r2*r2 + d*d) / (2*d)                    
    y = (r1*r1 - r3*r3 -2*i*x + i*i + j*j) / (2*j)       
    temp4 = r1*r1 - x*x - y*y                            
    if temp4<0:                                          
        raise Exception("The three spheres do not intersect!")
    z = np.sqrt(temp4)                                      
    p_12_a = P1 + x*e_x + y*e_y + z*e_z                  
    p_12_b = P1 + x*e_x + y*e_y - z*e_z                  
    return p_12_a,p_12_b 

def Average(lst): 
    return sum(lst) / len(lst) 


def NEL(node,e,scale):
    #node in elemeent 
    #check if node "node", is inside element "e" if projected on plane of e

    A = e.nodes[0]
    B = e.nodes[1]
    C = e.nodes[2]

    AB = [B.x-A.x,B.y-A.y,B.z-A.z]
    AC = [C.x-A.x,C.y-A.y,C.z-A.z]
    NO = np.cross(AB,AC)

    #unit vector
    NO = NO/(np.sqrt(NO[0]**2+NO[1]**2+NO[2]**2))

    UV = np.asarray([NO[0],NO[1],NO[2]])

    #project node on plane
    p = Point3D(float(node[0]),float(node[1]),float(node[2]))
    p1 = Plane(Point3D(float(e.nodes[0].x),float(e.nodes[0].y),float(e.nodes[0].z)),normal_vector = (float(UV[0]),float(UV[1]),float(UV[2])))
    #projected node
    try:  
        pN = p1.projection(p)
    except:
        ("projection failed, if this happens a lot, address")
        pN = p

    #is node withing element if projected on plane
    dmax = 0
    for n in e.nodes[:]:
        dist = np.sqrt((float(n.x)-float(pN[0]))**2+(float(n.y)-float(pN[1]))**2+(float(n.z)-float(pN[2]))**2)
        if dist > dmax:
            dmax = dist
            A = n
    BnC = []
    for n in e.nodes[:]:
        if A != n:
            BnC.append(n)

    BC =  np.asarray([BnC[0].x-BnC[1].x,BnC[0].y-BnC[1].y,BnC[0].z-BnC[1].z])

    i = 0
    inc = BC/20
    min_dist = 9999999
    while i <20:
        PT = np.asarray([BnC[1].x,BnC[1].y,BnC[1].z])+inc*i
        dist = np.sqrt((float(pN[0])-PT[0])**2+(float(pN[1])-PT[1])**2+(float(pN[2])-PT[2])**2)
        if dist < min_dist:
            min_dist = dist
            minPT = PT

        i = i + 1
    
    #edge to A distance
    ref_dist = np.sqrt((A.x-minPT[0])**2+(A.y-minPT[1])**2+(A.z-minPT[2])**2)

    #adjustment for points close to edge
    #th = scale/20
    #if ref_dist < 0.1*th:
    #    th = 0.5*ref_dist

    if ref_dist > dmax:
        #node inside element
        is_el = True

    else:
        #node is not inside element
        is_el = False

    return(is_el)
def MTS(AM):
    #this mesh to spline method only works for very uniform meshes with predictable number of connections

    #limit connections - minimum number of connected elements required for inside nodes
    lc = 5

    #check for edge points by point connections instead
    nodes = []
    counts = []
    for el in AM.meshElements:
        for pt in el.nodes:
            #if this node has not been encountered yet
            if pt not in nodes:
                counts.append(1)
                nodes.append(pt)
            #if node already recorded, add record of another element
            if pt in nodes:
                for i,n in enumerate(nodes):
                    if n == pt:
                        counts[i] = counts[i]+1
    #list of nodes that are considered on edge
    edge_nodes = []
    for i,n in enumerate(nodes):
        if counts[i] < lc:
            edge_nodes.append(n)

    return(edge_nodes)

def meshToSpline(AM):
    #This is not perfect but it is rather accurate with only some nodes picked up on accident, and minimum nodes missing.
    #The main issue is the runtime, for large meshes this can take hours.

    #checked points
    cp = []

    #for all nodes
    edge_points = []
    for i, EL in enumerate(AM.meshElements):
        print("el",i)
        for pt in EL.nodes:
            
            #check if touched
            pt_str = str(pt.x) +","+str(pt.y)+","+str(pt.z)
            if pt_str in cp:
                pass
            else:
                cp.append(pt_str)

                #create a local list of elements
                loc_elem = []
                for EL2 in AM.meshElements:
                    for pt2 in EL2.nodes:
                        if pt2 == pt:
                            loc_elem.append(EL2)

                #for all elements that reference this node
                unit_vectors = np.zeros([len(loc_elem),3])
                for i,e in enumerate(loc_elem):
                    #A is root point
                    #average normal (check direction of normals consistent?)
                    A = e.nodes[0]
                    B = e.nodes[1]
                    C = e.nodes[2]

                    AB = [B.x-A.x,B.y-A.y,B.z-A.z]
                    AC = [C.x-A.x,C.y-A.y,C.z-A.z]
                    NO = np.cross(AB,AC)

                    #unit vector
                    NO = NO/(np.sqrt(NO[0]**2+NO[1]**2+NO[2]**2))
                    if i == 0:
                        unit_vectors[i,:] = np.asarray([NO[0],NO[1],NO[2]])

                    else:
                        #check if vector same direction

                        dot_product = np.dot(unit_vectors[0,:], NO)
                        angle = np.arccos(dot_product)*180/math.pi #angle in deg
                        if angle > 90:
                            NO = NO * -1
                        unit_vectors[i,:] = np.asarray([NO[0],NO[1],NO[2]])

                av_vec = [Average(unit_vectors[:,0]),Average(unit_vectors[:,1]),Average(unit_vectors[:,2])]

                #create cirecle in that plane

                if loc_elem[0].nodes[0] == pt:
                    ref2 = loc_elem[0].nodes[1]
                else:
                    ref2 = loc_elem[0].nodes[0]

                #project any other element point on plane
                p = Point3D(ref2.x,ref2.y,ref2.z)
                p1 = Plane(Point3D(float(pt.x),float(pt.y),float(pt.z)),normal_vector = (float(av_vec[0]),float(av_vec[1]),float(av_vec[2])))
                projectP1 = p1.projection(p)

        
                vec_2 = [projectP1[0]-pt.x,projectP1[1]-pt.y,projectP1[2]-pt.z]   
                tt = vec_2[0]**2+vec_2[1]**2+vec_2[2]**2
                vec_2 = vec_2/np.sqrt(float(tt))

                scale = 0.2

                vec_2 = vec_2*scale # scale to fit within elements
                ref_pt = np.asarray([pt.x,pt.y,pt.z])+vec_2

                # create a matrix of point + distance -- 2 distance fixed around circle
                #three_point = np.asarray([[x1,y1,z1,d1],[x2,y2,z2,d2],[...]])
                #first point is point 0 on circle
                #second point is root point
                #third point is 1mm up in normal direction from second
                three_point = np.asarray([[float(ref_pt[0]),float(ref_pt[1]),float(ref_pt[2]),0],
                                        [float(pt.x),float(pt.y),float(pt.z),scale],
                                        [float(pt.x+av_vec[0]),float(pt.y+av_vec[1]),float(pt.z+av_vec[2]),(1+scale**2)**(1/2)]])


                #make increment so mirror points dont exist, below calcs wont work at 180 deg
                inc = 20
                a = inc
                c_pt = [np.asarray([float(ref_pt[0]),float(ref_pt[1]),float(ref_pt[2])])]
                while a < 90:
                                    
                    O = math.sin(a*math.pi/180)*scale

                    three_point[0,3] = O*2
                    try:
                        P1, P2 = trilaterate(three_point[0,0:3],three_point[1,0:3],three_point[2,0:3],three_point[0,3],three_point[1,3],three_point[2,3])
                    except:
                        print("trilaterate didnt work",three_point[0,0:3],three_point[1,0:3],three_point[2,0:3],three_point[0,3],three_point[1,3],three_point[2,3])
                        break
                    c_pt.append(P1)
                    c_pt.append(P2)

                    a = a + inc

                #check if all circle points in linked elements
                #for circle point
                nodes_out_of_elem = 0
                #print("len c_pt",len(c_pt))
                #For every node on the circle
                for c in c_pt:
                    node_in_el = False
                    #The node needs to belong to 1 element
                    for EL2 in loc_elem:
                        bl = NEL(c,EL2,scale)
                        if bl == True:
                            #This node belongs to this element
                            node_in_el = True
                            break
                    #print(bl)

                    if node_in_el == False:

                        nodes_out_of_elem += 1
                        if nodes_out_of_elem == 2:
                            break
                if nodes_out_of_elem == 2:
                    edge_points.append(pt)
           

    #order nodes in edge_spline (by neighbour distance)

    #add to JSON
    return(edge_points)

#AreaMesh = import_stl_v1("source_files\\WO4502_MD_14_only.stl")
#meshToSpline(AreaMesh)


