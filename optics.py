import numpy as np
from scipy import spatial
from math import sqrt, radians, cos, sin, asin, atan2
import pdb
import get_data
import AutomaticClustering as AutoC
import matplotlib.pyplot as plt
import f
import scipy
import itertools
def haversine(A, B):
    """	Args:  A and B are Lon/Lat point.  Returns distance between
        A and B in kilometers """
    lon1, lat1 = A
    lon2, lat2 = B
    R = 6372.8  # Earth radius in kilometers
    dLat = radians(lat2 - lat1)
    dLon = radians(lon2 - lon1)
    lat1 = radians(lat1)
    lat2 = radians(lat2)
    a = sin(dLat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dLon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return R * c


def update(core_dist_pt, distance_mat, point, seeds):
    """ For each "point" neighbor list calculate a vector of distance between
        that point and each of its' neighbors. 
        If the distance  (the reachability) to it's
        neighbors is greater then the core distance retain the 
        reachability.. If the neighbors distances is then the core distance 
        set it's value to the core distance """
    cd_vector = np.ones(len(seeds)) * core_dist_pt
    reach_vector = distance_mat[point][seeds]
    temp = np.column_stack((cd_vector, reach_vector))
    # pdb.set_trace()
    maxtemp = np.max(temp, axis=1)
    return maxtemp


def dist_mat(points, metric):
    if metric == 'haversine':
        distance_mat = spatial.distance.pdist(
            points, lambda u, v: haversine(u, v))
    else:
        distance_mat = spatial.distance.pdist(points, metric)
    return spatial.distance.squareform(distance_mat)


def optics(points, min_cluster_size, metric):
    # setup variables
    """ The optics algorithm.  The optics algorithm tries overcome the
        limitation of the DBSCAN algorithms.  The main limitation of the DBSCAB
        alogrithm is that it requires having a idea of the density of the clusters.
       """
    #  Constant values
    m, n = points.shape
    rd = np.ones(m) * 100000000
#    cd = {i: -1 for i in range(m)}
    cd = np.ones(m) * -1
    ordered = []

   # calculate the distance between all points (n^2) calculation
   # uses the scipy.spatial package
    try:
        distance_mat = np.load("dist_mat.npy")
    except:
        print 'Creating new dist_mat'
        distance_mat = dist_mat(np.array(X), metric)
        np.save("dist_mat", distance_mat)
    tmp = np.zeros((m, m)) - 1

    # calculate core distance.  The core distance
    # is the distance from a point to its nth-neighbor
    for point in xrange(m):
        try:
            # get neighbor list in sorted order (closest to farthest)
            # get the nth (e.g. min_cluster_size) values
            nbr_list = sorted([i for i in distance_mat[point] if i > 0])
            if len(nbr_list) > min_cluster_size - 1:
                cd[point] = nbr_list[min_cluster_size - 1]
        except:
            cd[point] = -1

    # calculate the reachability
    processed = []
    index = 0
    # loop through all the points (called the seeds)
    seeds = np.array([i for i in range(0, m)])
    while len(seeds) != 1:
        seed_trial = seeds[index]
        # mark this seed a s processed
        processed.append(seed_trial)
        # this loop decrements the number of seeds
        seed_indexes = np.where(seeds != seed_trial)
        seeds = seeds[seed_indexes]
        # compare reachability vector this point..   
        rd_temp = update(cd[seed_trial], distance_mat, seed_trial, seeds)
        # compare the current reachability matrix with an updated rd
        # if the updata rd is less then the rd
        rd_index = np.where(rd[seeds] > rd_temp)[0]
        # pdb.set_trace()
        rd[seeds[rd_index]] = rd_temp[rd_index]
        index = np.argmin(rd[seeds])
    processed.append(seeds[0])
    rd[0] = 0
    return rd, cd, processed

if __name__ == '__main__':
        #X = np.load("zhang2.dat.npy")
    min_cluster_size = 100 
    X = np.array(get_data.get_data()[14000:21000])
    rd, cd, processed = optics(np.array(X), min_cluster_size, "haversine")
   
    ## create 2 plots 
    RPlot = []
    RPoints = []
    for item in processed:
        RPlot.append(rd[item])  # Reachability Plot
        RPoints.append([X[item][0], X[item][1]])
    
    ## create some plot
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(X[:, 0], X[:, 1], 'b.', ms=2)
    ax.set_title('Crime in SF (March 2012)')
    plt.savefig('Graph.png', dpi=None, facecolor='w', edgecolor='w',
                orientation='portrait', papertype=None, format=None,
                transparent=False, bbox_inches=None, pad_inches=0.1)
    plt.show()
    rootNode = AutoC.automaticCluster(RPlot, RPoints)
    AutoC.graphTree(rootNode, RPlot)
    # get only the leaves of the tree
    leaves = AutoC.getLeaves(rootNode, [])
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.set_title('Clusters (March 2012) min size = 100') 
    ax.plot(X[:, 0], X[:, 1], 'b.', ms=2)
    colors = itertools.cycle('rgmckwygmrcmkwy')
    for item, c in zip(leaves, colors):
        print item, c
        node = []
        for v in range(item.start, item.end):
            node.append(RPoints[v])
        node = np.array(node)
	try:
		hull=spatial.ConvexHull(node)
		#pdb.set_trace()	
		x = np.append(hull.vertices,[hull.vertices[0]])
		#ax.plot(node[x,0],node[x,1],c, lw=2.5)
	except:
		print 'Error creating convex hull'	
		pass;  
        ax.plot(node[:, 0], node[:, 1], c + 'o', ms=2)


plt.savefig('Graph2.png', dpi=None, facecolor='w', edgecolor='w',
            orientation='portrait', papertype=None, format=None,
            transparent=False, bbox_inches=None, pad_inches=0.1)
plt.show()
