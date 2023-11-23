# python
# Convex Hull 1.0 - Kjell Emanuelsson 2019
# (Core process code by Swapnil Das (see MIT license below))
#
# 1.0 - release
# 1.1 - 220620 Fixed element mode errors
#
# MIT License
# Copyright (c) 2017 Swapnil Das
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import modo
from math import ceil, floor, sqrt
import math

# import sys
m = lx.Monitor()
mon_step = 1
m.init(100)


def avgpos(poslist):
    vx, vy, vz = [], [], []
    for vi in poslist:
        vx.append(vi[0]), vy.append(vi[1]), vz.append(vi[2])
    total = len(poslist)
    return sum(vx) / total, sum(vy) / total, sum(vz) / total


def set_correct_normal(possible_internal_points, plane):  # Make the orientation of Normal correct
    for point in possible_internal_points:
        dist = dotProduct(plane.normal, point - plane.pointA)
        if (dist != 0):
            if (dist > 10 ** -10):
                plane.normal.x = -1 * plane.normal.x
                plane.normal.y = -1 * plane.normal.y
                plane.normal.z = -1 * plane.normal.z
                return


def printV(vec):  # Print points
    print(vec.x, vec.y, vec.z)


def cross(pointA, pointB):  # Cross product
    x = (pointA.y * pointB.z) - (pointA.z * pointB.y)
    y = (pointA.z * pointB.x) - (pointA.x * pointB.z)
    z = (pointA.x * pointB.y) - (pointA.y * pointB.x)
    return Point(x, y, z)


def dotProduct(pointA, pointB):  # Dot product
    return (pointA.x * pointB.x + pointA.y * pointB.y + pointA.z * pointB.z)


def checker_plane(a, b):  # Check if two planes are equal or not

    if ((a.pointA.x == b.pointA.x) and (a.pointA.y == b.pointA.y) and (a.pointA.z == b.pointA.z)):
        if ((a.pointB.x == b.pointB.x) and (a.pointB.y == b.pointB.y) and (a.pointB.z == b.pointB.z)):
            if ((a.pointC.x == b.pointC.x) and (a.pointC.y == b.pointC.y) and (a.pointC.z == b.pointC.z)):
                return True

        elif ((a.pointB.x == b.pointC.x) and (a.pointB.y == b.pointC.y) and (a.pointB.z == b.pointC.z)):
            if ((a.pointC.x == b.pointB.x) and (a.pointC.y == b.pointB.y) and (a.pointC.z == b.pointB.z)):
                return True

    if ((a.pointA.x == b.pointB.x) and (a.pointA.y == b.pointB.y) and (a.pointA.z == b.pointB.z)):
        if ((a.pointB.x == b.pointA.x) and (a.pointB.y == b.pointA.y) and (a.pointB.z == b.pointA.z)):
            if ((a.pointC.x == b.pointC.x) and (a.pointC.y == b.pointC.y) and (a.pointC.z == b.pointC.z)):
                return True

        elif ((a.pointB.x == b.pointC.x) and (a.pointB.y == b.pointC.y) and (a.pointB.z == b.pointC.z)):
            if ((a.pointC.x == b.pointA.x) and (a.pointC.y == b.pointA.y) and (a.pointC.z == b.pointA.z)):
                return True

    if ((a.pointA.x == b.pointC.x) and (a.pointA.y == b.pointC.y) and (a.pointA.z == b.pointC.z)):
        if ((a.pointB.x == b.pointA.x) and (a.pointB.y == b.pointA.y) and (a.pointB.z == b.pointA.z)):
            if ((a.pointC.x == b.pointB.x) and (a.pointC.y == b.pointB.y) and (a.pointC.z == b.pointB.z)):
                return True

        elif ((a.pointB.x == b.pointC.x) and (a.pointB.y == b.pointC.y) and (a.pointB.z == b.pointC.z)):
            if ((a.pointC.x == b.pointB.x) and (a.pointC.y == b.pointB.y) and (a.pointC.z == b.pointB.z)):
                return True

    return False


def checker_edge(a, b):  # Check if 2 edges have same 2 vertices

    if ((a.pointA == b.pointA) and (a.pointB == b.pointB)) or ((a.pointB == b.pointA) and (a.pointA == b.pointB)):
        return True

    return False


class Edge:  # Make a object of type Edge which have two points denoting the vertices of the edges
    def __init__(self, pointA, pointB):
        self.pointA = pointA
        self.pointB = pointB

    def __str__(self):
        string = "Edge"
        string += "\n\tA: " + str(self.pointA.x) + "," + str(self.pointA.y) + "," + str(self.pointA.z)
        string += "\n\tB: " + str(self.pointB.x) + "," + str(self.pointB.y) + "," + str(self.pointB.z)
        return string

    def __hash__(self):
        return hash((self.pointA, self.pointB))

    def __eq__(self, other):
        # print "comparing Edges"
        return checker_edge(self, other)


class Point:  # Point class denoting the points in the space
    def __init__(self, x=None, y=None, z=None):
        self.x = x
        self.y = y
        self.z = z

    def __sub__(self, pointX):
        return Point(self.x - pointX.x, self.y - pointX.y, self.z - pointX.z)

    def __add__(self, pointX):
        return Point(self.x + pointX.x, self.y + pointX.y, self.z + pointX.z)

    def length(self):
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

    def __str__(self):
        return str(self.x) + "," + str(self.y) + "," + str(self.z)

    def __hash__(self):
        return hash((self.x, self.y, self.z))

    def __eq__(self, other):
        # print "Checking equality of Point"
        return (self.x == other.x) and (self.y == other.y) and (self.z == other.z)


class Plane:  # Plane class having 3 points for a triangle
    def __init__(self, pointA, pointB, pointC):
        self.pointA = pointA
        self.pointB = pointB
        self.pointC = pointC
        self.normal = None
        self.distance = None
        self.calcNorm()
        self.to_do = set()
        self.edge1 = Edge(pointA, pointB)
        self.edge2 = Edge(pointB, pointC)
        self.edge3 = Edge(pointC, pointA)

    def calcNorm(self):
        point1 = self.pointA - self.pointB
        point2 = self.pointB - self.pointC
        normVector = cross(point1, point2)
        length = normVector.length()
        normVector.x = normVector.x / length
        normVector.y = normVector.y / length
        normVector.z = normVector.z / length
        self.normal = normVector
        self.distance = dotProduct(self.normal, self.pointA)

    def dist(self, pointX):
        return (dotProduct(self.normal, pointX - self.pointA))

    def get_edges(self):
        return [self.edge1, self.edge2, self.edge3]

    def calculate_to_do(self, temp=None):
        if (temp != None):
            for p in temp:
                dist = self.dist(p)
                if dist > 10 ** (-10):
                    self.to_do.add(p)

        else:
            for p in points:
                dist = self.dist(p)
                if dist > 10 ** (-10):
                    self.to_do.add(p)

    def __eq__(self, other):
        # print 'Checking Plane Equality'
        return checker_plane(self, other)

    def __str__(self):
        string = "Plane : "
        string += "\n\tX: " + str(self.pointA.x) + "," + str(self.pointA.y) + "," + str(self.pointA.z)
        string += "\n\tY: " + str(self.pointB.x) + "," + str(self.pointB.y) + "," + str(self.pointB.z)
        string += "\n\tZ: " + str(self.pointC.x) + "," + str(self.pointC.y) + "," + str(self.pointC.z)
        string += "\n\tNormal: " + str(self.normal.x) + "," + str(self.normal.y) + "," + str(self.normal.z)
        return string

    def __hash__(self):
        return hash((self.pointA, self.pointB, self.pointC))


def calc_horizon(visited_planes, plane, eye_point, edge_list):  # Calculating the horizon for an eye to make new faces
    if (plane.dist(eye_point) > 10 ** -10):
        visited_planes.append(plane)
        edges = plane.get_edges()
        for edge in edges:
            neighbour = adjacent_plane(plane, edge)
            if (neighbour not in visited_planes):
                result = calc_horizon(visited_planes, neighbour, eye_point, edge_list)
                if (result == 0):
                    edge_list.add(edge)

        return 1

    else:
        return 0


def adjacent_plane(main_plane, edge):  # Finding adjacent planes to an edge
    for plane in list_of_planes:
        edges = plane.get_edges()
        if (plane != main_plane) and (edge in edges):
            return plane


def distLine(pointA, pointB, pointX):  # Calculate the distance of a point from a line
    vec1 = pointX - pointA
    vec2 = pointX - pointB
    vec3 = pointB - pointA
    vec4 = cross(vec1, vec2)
    if vec2.length() == 0:
        return None

    else:
        return vec4.length() / vec2.length()


def max_dist_line_point(pointA, pointB):  # Calculate the maximum distant point from a line for initial simplex
    maxDist = 0
    for point in points:
        if (pointA != point) and (pointB != point):
            dist = abs(distLine(pointA, pointB, point))
            if dist > maxDist:
                maxDistPoint = point
                maxDist = dist

    return maxDistPoint


def max_dist_plane_point(plane):  # Calculate the maximum distance from the plane
    maxDist = 0

    for point in points:
        dist = abs(plane.dist(point))
        if (dist > maxDist):
            maxDist = dist
            maxDistPoint = point

    return maxDistPoint


def find_eye_point(plane, to_do_list):  # Calculate the maximum distance from the plane
    maxDist = 0
    for point in to_do_list:
        dist = plane.dist(point)
        if (dist > maxDist):
            maxDist = dist
            maxDistPoint = point

    return maxDistPoint


def initial_dis(p, q):  # Gives the Euclidean distance
    return math.sqrt((p.x - q.x) ** 2 + (p.y - q.y) ** 2 + (p.z - q.z) ** 2)


def initial_max(now):  # From the extreme points calculate the 2 most distant points
    maxi = -1
    found = [[], []]
    for i in range(6):
        for j in range(i + 1, 6):
            dist = initial_dis(now[i], now[j])
            if dist > maxi:
                found = [now[i], now[j]]

    return found


def initial():  # To calculate the extreme points to make the initial simplex

    x_min_temp = 10 ** 9
    x_max_temp = -10 ** 9
    y_min_temp = 10 ** 9
    y_max_temp = -10 ** 9
    z_min_temp = 10 ** 9
    z_max_temp = -10 ** 9
    for i in range(num_points):
        if points[i].x > x_max_temp:
            x_max_temp = points[i].x
            x_max = points[i]

        if points[i].x < x_min_temp:
            x_min_temp = points[i].x
            x_min = points[i]

        if points[i].y > y_max_temp:
            y_max_temp = points[i].y
            y_max = points[i]

        if points[i].y < y_min_temp:
            y_min_temp = points[i].y
            y_min = points[i]

        if points[i].z > z_max_temp:
            z_max_temp = points[i].z
            z_max = points[i]

        if points[i].z < z_min_temp:
            z_min_temp = points[i].z
            z_min = points[i]

    return (x_max, x_min, y_max, y_min, z_max, z_min)


# ---------------------------------------------------------------------------------------------------------------------
# SETUP
# ---------------------------------------------------------------------------------------------------------------------
points = []  # List to store the points

scene = modo.scene.current()
sel_mode = lx.eval('query layerservice selmode ?')

sel_items = list(scene.selectedByType("mesh")) + list(scene.selectedByType("meshInst"))
sel_count = len(sel_items)
element_mode = False

if sel_mode == "vertex" or sel_mode == "edge" or sel_mode == "polygon":
    lx.eval('select.convert vertex')
    element_mode = True

if sel_count:

    convex_mesh_name = str(sel_items[0].name) + "_convexhull"

    if element_mode:

        # symmetry check
        symmetry_mode = False
        if lx.eval('symmetry.state ?') == True :
            symmetry_mode = True
            lx.eval('select.symmetryState 0')

        sel_layer = lx.eval('query layerservice layers ? selected')
        layers_check = lx.eval('query layerservice layers ? fg')

        if type(layers_check) == tuple :
            layers = [i for i in layers_check]
        else:
            layers = [layers_check]


        for layer in layers :

            index = lx.eval1('query layerservice layer.index ? %s' %layer)
            # making sure the damn layers are selected
            layer_id = lx.eval('query layerservice layer.id ? %s' %layer)
            lx.eval('select.item %s add' %layer_id)

            v = lx.evalN('query layerservice verts ? selected')

            if v:
                if symmetry_mode:
                    v = v[0::2]

                for i in v :
                    vpos = lx.eval('query layerservice vert.wdefpos ? %s' %i )
                    points.append(Point(vpos[0], vpos[1], vpos[2]))

    else:
        for item in sel_items:
            m.step(mon_step)
            vis = item.channel("visible").get()
            if vis == "off" or "allOff":
                item.channel("visible").set("default")

            item_mtx = modo.Matrix4(item.channel('worldMatrix').get())

            if item.isAnInstance:
                inst_src = item.itemGraph(graphType='source').forward()[0]
                for v in inst_src.geometry.vertices:
                    vpos_mtx = modo.Matrix4(position=v.position) * item_mtx
                    vpos = vpos_mtx.position
                    points.append(Point(vpos[0], vpos[1], vpos[2]))

            elif sel_mode == "item":
                for v in item.geometry.vertices:
                    vpos_mtx = modo.Matrix4(position=v.position) * item_mtx
                    vpos = vpos_mtx.position
                    points.append(Point(vpos[0], vpos[1], vpos[2]))
            else:
                sys.exit(": --- Invalid Selection Mode Error. Aborting script. --- ")

else:
    sys.exit(": --- Selection Error. (Mesh layers must be selected) Aborting script. --- ")

num_points = len(points)

if num_points < 3:
    sys.exit(": --- Not enough points found. Selection Error? --- ")

print(num_points, points)
#sys.exit()

# ---------------------------------------------------------------------------------------------------------------------
# Calculate Hull
# ---------------------------------------------------------------------------------------------------------------------
try:
    extremes = initial()  # calculate the extreme points for every axis.
    initial_line = initial_max(extremes)  # Make the initial line by joining farthest 2 points
    third_point = max_dist_line_point(initial_line[0], initial_line[1])  # Calculate the 3rd point to make a plane
    first_plane = Plane(initial_line[0], initial_line[1],
                        third_point)  # Make the initial plane by joining 3rd point to the line

    fourth_point = max_dist_plane_point(first_plane)  # Make the fourth plane to make a tetrahedron
except:
    sys.exit(": --- Something went wrong. Not enough points for a hull? Aborting script. ---")

m.step(mon_step)

possible_internal_points = [initial_line[0], initial_line[1], third_point,
                            fourth_point]  # List that helps in calculating orientation of point

second_plane = Plane(initial_line[0], initial_line[1], fourth_point)  # The other planes of the tetrahedron
third_plane = Plane(initial_line[0], fourth_point, third_point)
fourth_plane = Plane(initial_line[1], third_point, fourth_point)

set_correct_normal(possible_internal_points, first_plane)  # Setting the orientation of normal correct
set_correct_normal(possible_internal_points, second_plane)
set_correct_normal(possible_internal_points, third_plane)
set_correct_normal(possible_internal_points, fourth_plane)

first_plane.calculate_to_do()  # Calculating the to_do list which stores the point for which  eye_point have to be found
second_plane.calculate_to_do()
third_plane.calculate_to_do()
fourth_plane.calculate_to_do()

list_of_planes = []  # List containing all the planes
list_of_planes.append(first_plane)
list_of_planes.append(second_plane)
list_of_planes.append(third_plane)
list_of_planes.append(fourth_plane)

any_left = True  # Checking if planes with to do list is over

while any_left:
    any_left = False
    for working_plane in list_of_planes:

        if len(working_plane.to_do) > 0:
            m.step(mon_step)

            any_left = True
            eye_point = find_eye_point(working_plane, working_plane.to_do)  # Calculate the eye point of the face

            edge_list = set()
            visited_planes = []

            calc_horizon(visited_planes, working_plane, eye_point, edge_list)  # Calculate the horizon

            for internal_plane in visited_planes:  # Remove the internal planes
                list_of_planes.remove(internal_plane)

            for edge in edge_list:  # Make new planes
                new_plane = Plane(edge.pointA, edge.pointB, eye_point)
                set_correct_normal(possible_internal_points, new_plane)

                temp_to_do = set()
                for internal_plane in visited_planes:
                    temp_to_do = temp_to_do.union(internal_plane.to_do)

                new_plane.calculate_to_do(temp_to_do)
                list_of_planes.append(new_plane)

final_vertices = set()
tris = []

for plane in list_of_planes:
    final_vertices.add(plane.pointA)
    final_vertices.add(plane.pointB)
    final_vertices.add(plane.pointC)
    tri_a = plane.pointA.x, plane.pointA.y, plane.pointA.z
    tri_b = plane.pointB.x, plane.pointB.y, plane.pointB.z
    tri_c = plane.pointC.x, plane.pointC.y, plane.pointC.z
    tri = tri_a, tri_b, tri_c
    tris.append(tri)

# ---------------------------------------------------------------------------------------------------------------------
# Create Hull
# ---------------------------------------------------------------------------------------------------------------------
m.step(mon_step)

convex_mesh = scene.addMesh(convex_mesh_name)
lx.eval('select.drop item')
scene.select(convex_mesh)


# Yeah. Quite quick n dirty... but hey, seems to work, mostly ;>
for tri in tris:
    v1 = convex_mesh.geometry.vertices.new(tri[0])
    v2 = convex_mesh.geometry.vertices.new(tri[1])
    v3 = convex_mesh.geometry.vertices.new(tri[2])
    convex_mesh.geometry.polygons.new((v1, v2, v3))

convex_mesh.geometry.setMeshEdits()

lx.eval('!!mesh.cleanup true true true true true true true true true true true')
lx.eval('!!poly.align')

# Checking for inverted face normal...and flipping if it seems necessary
# set center pos
cpos_p = initial_line[1] - initial_line[0]
cpos = cpos_p.x, cpos_p.y, cpos_p.z
cpos = modo.Vector3(cpos)

p_count = convex_mesh.geometry.numPolygons
# I hoped I'd just need the one triangle to dotproduct check - no, but this seems to catch 'em all...most
neg_dp_count = 0
for p in convex_mesh.geometry.polygons:
    p_normal = modo.Vector3(p.normal)
    v_normal = modo.Vector3(p.vertices[0].position) - cpos
    dot_product = p_normal.dot(v_normal)
    if dot_product < 0:
        neg_dp_count += 1

if neg_dp_count >= (p_count / 2):
    lx.eval('poly.flip')
