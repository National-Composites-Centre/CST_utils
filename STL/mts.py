#mts- mesh-to-spline conversion

from utils import  method_reverse_lookup
from STL.file_utils import import_stl_v1
from MATH_utils.vec_utils import anyNormal
#from CATIA.CATIA_utils import bug_fixing, CAT_points
import numpy as np
import open3d as o3d

import math
from sympy import Plane, Point, Point3D 
import CompositeStandard as cs


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

    #is node within element if projected on plane
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

def MTS_np(AM):
    #CURRENTLY BROKEN - TOO SIMPLE LOGIC FOR TOO COMPLEX MESH
    
    #first translation
    mat_mesh = np.asarray([[0,0,0,0]])
    for i,el in enumerate(AM.meshElements):
        for pt in el.nodes:
            mat_mesh = np.concatenate((mat_mesh,np.asarray([[i,pt.x,pt.y,pt.z]])),axis=0)
    mat_mesh = np.delete(mat_mesh,0,axis=0)



    nodes = np.asarray([[0,0,0,0]]) #x,y,z,count
    #re-order mat_mesh according to x
    mat_mesh = mat_mesh[mat_mesh[:,1].argsort()]

    for i in range(0,np.size(mat_mesh,0)):
        if ((nodes[np.size(nodes,0)-1,0] == mat_mesh[i,1]) and
           (nodes[np.size(nodes,0)-1,1] == mat_mesh[i,2]) and
           (nodes[np.size(nodes,0)-1,2] == mat_mesh[i,3])):
            #if same node, increase count
            nodes[np.size(nodes,0)-1,3] += 1
        else:
            nodes = np.concatenate((nodes,np.asarray([[mat_mesh[i,1],mat_mesh[i,2],mat_mesh[i,3],1]])),axis=0)
        
    nodes = np.delete(nodes,0,axis=0)

    #limit connections - minimum number of connected elements required for inside nodes
    lc = 4
    #now generate nodes list
    print("generating nodes list")
    edge_nodes = []
    for i in range(0,np.size(nodes,0)):
        print(nodes[i,3],"lc")
        if nodes[i,3] < lc:
            edge_nodes.append(cs.Point(x=nodes[i,0],y=nodes[i,1],z=nodes[i,2]))


    return(edge_nodes)

def meshToSpline_np(AM):
    #As of 25/11/2024 the most promissing method for reliable spline generation from STL meshes
    #Issues still exist:
    #   1. Relies on continous mesh
    #   2. internal windows/gaps in mesh cause issues
    #   3. Still very slow for large meshes
    #   4. if Aspect ratios of border elements vary massively, the checks for node ordering will break

    #first translation from objects to Numpy - marginal performance improvemnet
    mat_mesh = np.asarray([[0,0,0,0]])
    for i,el in enumerate(AM.meshElements):
        for pt in el.nodes:
            mat_mesh = np.concatenate((mat_mesh,np.asarray([[i,pt.x,pt.y,pt.z]])),axis=0)
    mat_mesh = np.delete(mat_mesh,0,axis=0)

    #checked points - Point below has to be unlikely 
    #CP is only used to prevent re-checking the same points
    cp = np.asarray([[0.5,0.00005,999999]])

    #for all nodes
    edge_points = []
    for i in range(0,np.size(mat_mesh,0)):

            #avoids re-checkign points already triggered by other element
            checked = False
            if np.size(cp,0) != 1:
                for ii in range(0,np.size(cp,0)):
                    if ((cp[ii,0] == mat_mesh[i,1]) and
                        (cp[ii,1] == mat_mesh[i,2]) and
                        (cp[ii,2] == mat_mesh[i,3])):
                        checked = True

            if checked == True:
                pass
            else:

                #add points to check points lists 
                cp = np. concatenate((cp,np.asarray([[mat_mesh[i,1],mat_mesh[i,2],mat_mesh[i,3]]])),axis=0)

                #create a local list of elements - elements touching current node 
                #If this is internal nodes, all the nodes generated in circle around central node will fall on one of these elements
                #This method is slow but reasonably robust.
                unit_vectors = np.asarray([[0,0,0]])
                linked_elements = []

                #Assume always 3 nodes per elment for now!!
                for iii in range(0,np.size(mat_mesh,0)):
                    
                    if ((mat_mesh[iii,1] == mat_mesh[i,1]) and
                    (mat_mesh[iii,2] == mat_mesh[i,2]) and
                    (mat_mesh[iii,3] == mat_mesh[i,3])):
                        #A is root point
                        #average normal (check direction of normals consistent?)
                        #Identify neighbouring points belonging to the same element
                        A = mat_mesh[iii,:]
                        if iii%3 == 0:
                            B = mat_mesh[iii+1,:]
                            C = mat_mesh[iii+2,:]
                        elif iii%3 ==1:
                            B = mat_mesh[iii-1,:]
                            C = mat_mesh[iii+1,:]
                        elif iii%3 == 2:
                            B = mat_mesh[iii-2,:]
                            C = mat_mesh[iii-1,:]

                        linked_elements.append(np.asarray([A,B,C]))
                        AB = np.asarray([B[1]-A[1],B[2]-A[2],B[3]-A[3]])
                        AC = np.asarray([C[1]-A[1],C[2]-A[2],C[3]-A[3]])

                        NO = np.cross(AB,AC)
                        #print("NO",NO)
                        tt = NO[0]**2+NO[1]**2+NO[2]**2
                        NO = NO/np.sqrt(float(tt))
                        #print("unit NO",NO)

                        if np.size(unit_vectors,0) == 1:
                            #print(unit_vectors, "TEST")
                            unit_vectors = np.concatenate((unit_vectors,np.asarray([[NO[0],NO[1],NO[2]]])),axis=0)
                        else:
                            #check if vector same direction

                            t1 = math.sqrt(((unit_vectors[1,0]+NO[0])/2)**2+((unit_vectors[1,1]+NO[1])/2)**2+((unit_vectors[1,2]+NO[2])/2)**2)
                            t0 = math.sqrt((unit_vectors[1,0]**2)+(unit_vectors[1,1]**2)+(unit_vectors[1,2]**2))
                            #print("pre-change",NO)
                            if t1 < t0*0.5: # adjust later - reasonably 2 vectors in same direction should not avarage into this
                                NO = NO * -1
                            unit_vectors = np.concatenate((unit_vectors,np.asarray([[NO[0],NO[1],NO[2]]])),axis=0)
                            #print("post-change",NO)

                unit_vectors = np.delete(unit_vectors,0,axis=0)
                #print("unit_vectors")
                #print(unit_vectors)
                av_vec = [Average(unit_vectors[:,0]),Average(unit_vectors[:,1]),Average(unit_vectors[:,2])]
                #print("average vec",av_vec)

                #if only two elements neighbour, than its at the edge...
                if np.size(unit_vectors,0) <3:
                    edge_points.append(cs.Point(x=mat_mesh[i,1],y=mat_mesh[i,2],z=mat_mesh[i,3]))
                
                else:
                #create cirecle in that plane



                    #project any other element point on plane
                    p = Point3D(B[1],B[2],B[3])
                    p1 = Plane(Point3D(A[1],A[2],A[3]),normal_vector = (float(av_vec[0]),float(av_vec[1]),float(av_vec[2])))
                    projectP1 = p1.projection(p)

            
                    vec_2 = np.asarray([projectP1[0]-A[1],projectP1[1]-A[2],projectP1[2]-A[3]])   
                    tt = vec_2[0]**2+vec_2[1]**2+vec_2[2]**2
                    vec_2 = vec_2/(tt**(1/2))

                    scale = 0.2

                    vec_2 = vec_2*scale # scale to fit within elements
                    ref_pt = np.asarray([A[1],A[2],A[3]])+vec_2

                    # create a matrix of point + distance -- 2 distance fixed around circle
                    #three_point = np.asarray([[x1,y1,z1,d1],[x2,y2,z2,d2],[...]])
                    #first point is point 0 on circle
                    #second point is root point
                    #third point is 1mm up in normal direction from second
                    three_point = np.asarray([[float(ref_pt[0]),float(ref_pt[1]),float(ref_pt[2]),0],
                                            [A[1],A[2],A[3],scale],
                                            [A[1]+av_vec[0],A[2]+av_vec[1],A[3]+av_vec[2],(1+scale**2)**(1/2)]])


                    #make increment so mirror points dont exist, below calcs wont work at 180 deg
                    inc = 20
                    a = inc
                    c_pt = [np.asarray([ref_pt[0],ref_pt[1],ref_pt[2]])]
                    #print("cp_t_1")
                    #print(c_pt)
                    while a < 90:
                                        
                        O = math.sin(0.5*a*math.pi/180)*scale

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
                    #print("c_pt")
                    #print(c_pt)
                    for c in c_pt:
                        node_in_el = False
                        #The node needs to belong to 1 element
                        for E in linked_elements:

                            #TODO , extra translation , if this works out to be efficient, remove cs.Element from NEL
                            EL2 = cs.MeshElement(nodes=[cs.Point(x=E[0,1],y=E[0,2],z=E[0,3]),
                                                    cs.Point(x=E[1,1],y=E[1,2],z=E[1,3]),
                                                    cs.Point(x=E[2,1],y=E[2,2],z=E[2,3])])

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
                        edge_points.append(cs.Point(x=mat_mesh[i,1],y=mat_mesh[i,2],z=mat_mesh[i,3]))
           

    #order nodes in edge_spline (by neighbour distance)

    #distance of nodes should mostly work, but also check that the next distance is not vastly different than prev dist, if it is, place node between existent points
    ordered_points = [edge_points[0]]
    prev_max_dist = 999999
    while len(ordered_points) != len(edge_points):
        #add the point that is closes to last added point 
        maxDist = 999999
        for pt0 in edge_points:
            if pt0 not in ordered_points:
                dist = np.sqrt((pt0.x-ordered_points[len(ordered_points)-1].x
                                )**2+(pt0.y-ordered_points[len(ordered_points)-1].y
                                )**2+(pt0.z-ordered_points[len(ordered_points)-1].z
                                )**2)
                if maxDist > dist:
                    maxDist = dist
                    pt1 = pt0
        
        if maxDist > 3*prev_max_dist:
            #if the gap is suspiciously large, it instead goes through existent points and plugs in where it fits the most
            maxFix = 99999
            dist1 = 0
            for i, pt3 in enumerate(ordered_points):
                dist2 = dist1
                dist1 = np.sqrt((pt3.x-pt1.x
                                )**2+(pt3.y-pt1.y
                                )**2+(pt3.z-pt1.z
                                )**2)
                if i > 1:
                    #no point comparing the total distance to only 1 point dist
                    totDist = dist1+dist2
                    if totDist < maxFix:
                        maxFix = totDist
                        ID_pos = i
                    
            ordered_points.insert(ID_pos,pt1)

        if maxDist > 1.6*prev_max_dist:
            #this should deal with singular sharp element sticking out, with 2 next nodes being swapped
            #check total distances as it stands, if this is shorter with re-ordered nodes, re-order nodes
            dist1 = maxDist
            dist2 = prev_max_dist
            dist3 = np.sqrt((ordered_points[len(ordered_points)-3].x-ordered_points[len(ordered_points)-2].x
                                )**2+(ordered_points[len(ordered_points)-3].y-ordered_points[len(ordered_points)-2].y
                                )**2+(ordered_points[len(ordered_points)-3].z-ordered_points[len(ordered_points)-2].z
                                )**2)

            rDist1 = np.sqrt((pt1.x-ordered_points[len(ordered_points)-2].x
                                )**2+(pt1.y-ordered_points[len(ordered_points)-2].y
                                )**2+(pt1.z-ordered_points[len(ordered_points)-2].z
                                )**2)
            rDist2 =  np.sqrt((ordered_points[len(ordered_points)-1].x-ordered_points[len(ordered_points)-2].x
                                )**2+(ordered_points[len(ordered_points)-1].y-ordered_points[len(ordered_points)-2].y
                                )**2+(ordered_points[len(ordered_points)-1].z-ordered_points[len(ordered_points)-2].z
                                )**2)
            rDist3 = np.sqrt((ordered_points[len(ordered_points)-1].x-ordered_points[len(ordered_points)-3].x
                                )**2+(ordered_points[len(ordered_points)-1].y-ordered_points[len(ordered_points)-3].y
                                )**2+(ordered_points[len(ordered_points)-1].z-ordered_points[len(ordered_points)-3].z
                                )**2)
            #yes, this needs sketch for illustration... ^^ 

            if (rDist1+rDist2+rDist3) < (dist1+dist2+dist3):
                #re-order previous 2 nodes
                ordered_points[len(ordered_points)-2],ordered_points[len(ordered_points)-1] =ordered_points[len(ordered_points)-1],ordered_points[len(ordered_points)-2]
                print("swap happened!!!")
            #either way add the point
            ordered_points.append(pt1)

        else:

            ordered_points.append(pt1)

        prev_max_dist = maxDist

    

    #print("op",len(ordered_points))
    #print("ep",len(edge_points))

    #add to JSON
    return(ordered_points)

def meshToSpline(AM):
    #THIS IS SUPERECEEDED BY THE FUNCTION ABOVE WHICH USES NP FOR MOST PROCESSING (and has few more functionalities)

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


def meshToSpline_o3d(MeshFile):
    # Imports

    #TODO 
    #mains suspected issue is duplication of nodes (node coincidence)
    #the node list would need to be filtered so that overlapping nodes +-0.01mm are the same node
    #these than need to be re-referenced in elements 
    #it is not 100% this is the only issue, but without resolving this it will be impossible to troubleshoot further

    # Loading mesh
    mesh = o3d.io.read_triangle_mesh(MeshFile)

    # Extracting trinagles and reshaping to edges
    triangles = np.asarray(mesh.triangles)
    print("triangles",triangles)
    edges = np.vstack([triangles[:, [0, 1]], triangles[:, [1, 2]], triangles[:, [2,0]],])
    print("edges",edges)
    # Sorting edges
    edges = np.sort(edges, axis=1)

    # Finding unique edges
    edges_unique, edges_counts = np.unique(edges, axis=0, return_counts=True)
    print(edges_counts,"edge_counts")

    # Boundary edges
    boundary_edges = edges_unique[edges_counts==1]

    print(boundary_edges)


    print("size 1", np.size(edges,0))
    print("size 2", np.size(boundary_edges,0))

    POINTS = np.asarray(mesh.vertices)

    print("size Points",np.size(np.asarray(mesh.vertices),0))

    print(np.asarray(mesh.vertices))

    #TODO figure out why the filtering above doesnt work -- way too many points are stored (potentially the sort not working and 1-2 being not same as 2-1)

    edge_points = []
    saved = []
    for i in range(0,np.size(boundary_edges,0)-1):

        if int(boundary_edges[i,0]) not in saved:
            point= cs.Point(x = POINTS[boundary_edges[i,0]-1,0],y = POINTS[boundary_edges[i,0]-1,1],z = POINTS[boundary_edges[i,0]-1,2])
            edge_points.append(point)
            saved.append(int(boundary_edges[i,0]))

        if int(boundary_edges[i,1]) not in saved:
            point= cs.Point(x = POINTS[boundary_edges[i,1]-1,0],y = POINTS[boundary_edges[i,1]-1,1],z = POINTS[boundary_edges[i,1]-1,2])
            edge_points.append(point)
            saved.append(int(boundary_edges[i,1]))

    #TODO AVOID DUPLICATION



    return(edge_points)

from scipy.spatial import distance_matrix
import random
def mtSimple(MeshFile):

    mesh = o3d.io.read_triangle_mesh(MeshFile)

    tria = np.asarray(mesh.triangles)
    #print(tria)
    #sample of X elements
    i = 0
    sample = np.asarray([[0,0,0]])
    while i < 20:
        rs = random.randint(0,np.size(tria,0)-1)
        sample = np.concatenate((sample,np.asarray([tria[rs,:]])),axis=0)
        i += 1
    sample = np.delete(sample,0,axis=0)

    POINTS = np.asarray(mesh.vertices)

    normals = np.asarray([[0,0,0]])
    for i in range(0,np.size(sample,0)):

        v1 = POINTS[sample[i,0],:]-POINTS[sample[i,1],:]
        v2 = POINTS[sample[i,0],:]-POINTS[sample[i,2],:]

        #v3 is local normal
        v3 = np.cross(v1,v2)
        
        if np.size(normals,0) > 1:
            #average distance will be close to 0 if oposite direction
            t1 = math.sqrt(((normals[1,0]+v3[0])/2)**2+((normals[1,1]+v3[1])/2)**2+((normals[1,2]+v3[2])/2)**2)
            t0 = math.sqrt((normals[1,0]**2)+(normals[1,1]**2)+(normals[1,2]**2))
            #print("pre-change",NO)
            if t1 < t0*0.5: # adjust later - reasonably 2 vectors in same direction should not avarage into this
                v3 = v3 * -1
        normals = np.concatenate((normals,np.asarray([v3])),axis=0)

        #find normal to two vectors
    normals = np.delete(normals,0,axis=0)

    #average the normals (make sure same direction first)
    normal = np.mean(normals,axis=0)


    #this gives overall plane
    #any point from mesh
    center = POINTS[int(np.size(POINTS,0)/2),:]

    dVec = anyNormal(normal) #unit vector

    dVec2 = anyNormal(normal,dVec) # perpendicular to both

    scale = 99999
    #create points on large circle in this new plane
    #not quite circle, but distance does not matter as long as significantly larger than defect

    #first point
    CP = np.asarray([center+scale*dVec])
    
    #TODO this circle point gen can  be simpler .... 
    m = 4
    i = 1
    while i < m:
        CP = np.concatenate((CP,np.asarray([center+scale*((m-i)*dVec+(i)*dVec2)/m])),axis=0)
        i += i


    CP = np.concatenate((CP,np.asarray([center+scale*dVec2])),axis=0)

    m = 4
    i = 1
    while i < m:
        CP = np.concatenate((CP,np.asarray([center+scale*((m-i)*dVec2-(i)*dVec)/m])),axis=0)
        i += i
                                         
    CP = np.concatenate((CP,np.asarray([center-scale*dVec])),axis=0)

    m = 4
    i = 1
    while i < m:
        CP = np.concatenate((CP,np.asarray([center+scale*(-(m-i)*dVec-(i)*dVec2)/m])),axis=0)
        i += i

    CP = np.concatenate((CP,np.asarray([center-scale*dVec2])),axis=0)

    m = 4
    i = 1
    while i < m:
        CP = np.concatenate((CP,np.asarray([center+scale*(-(m-i)*dVec2+(i)*dVec)/m])),axis=0)
        i += i


    #find the closest point to each of circle points, these are the edge points

    edge_points = []
    for i in range(0,np.size(CP,0)):
        B = np.asarray([CP[i,:]])
        C = distance_matrix(POINTS,B)
        min_index = np.argmin(C)
        edge_points.append(cs.Point(x=POINTS[min_index,0],y=POINTS[min_index,1],z=POINTS[min_index,2]))

    #prevent point duplication
    dist = 99999
    #this makes sure process is repated if anything was deleted
    e = True
    while e == True:
        e = False
        for i, ep in enumerate(edge_points):
            if i != 0:
                dist = np.sqrt((ep.x-edge_points[i-1].x)**2+(ep.y-edge_points[i-1].y)**2+(ep.z-edge_points[i-1].z)**2)
            if dist < 0.01: #0.2mm threshold for now
                edge_points.pop(i)
                e = True
    brk = []
    curDif = 0
    for i, ep in enumerate(edge_points):
        if i != 0:
            prevDif = curDif
            curDif = np.sqrt((ep.x-prev.x)**2+(ep.y-prev.y)**2+(ep.z-prev.z)**2)
        if i > 1:
            if (curDif/prevDif > 10) or (prevDif/curDif > 10):
                brk.append(i)
        prev = ep
    return(edge_points,brk)
#AreaMesh = import_stl_v1("source_files\\WO4502_MD_14_only.stl")
#meshToSpline(AreaMesh)


