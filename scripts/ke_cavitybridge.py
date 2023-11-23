# python

# CavityBridge 1.4  Kjell Emanuelsson 2019-21
#
# Lets you bridge holes while forming a "cavity" when selecting corners. Also some extra features:
# EDGE:  Two edge separate selections as you would for the bridge tool, for corners with angle: Cavity Bridge
# VERT:  One vert selected (*in a corner on a border!*) - will create a new polygon based on connected border edges.
#        Based on the "f2" blender add on. No mouse pos tracking for now tho...
# POLY:  Any selection: Will just bevel down the depth of the shortest boundary edge. Minecraft style.
#
# 1.4 - Python 3 fixes
# Update 1.3 - Made the merge-hack in f2 & bevel mode NOT try to merge verts on the entire mesh
#               (just the around the selection)
# Update 1.2  + Added simple (dont do complicated shapes ;)  minecraft mode in POLY mode...
#             + fixed multi layer selection bug - will let you know if you have more than one selected now.
#             - Disabled edge extend on continous loop as it was just confusing and you can use poly mode for that.
# Update 1.1  - Fixed very silly bug on straight boxes! oopsie!
# Update 1.15 - cleaned up some testcode
#
# Quadralate link: https://community.foundry.com/discuss/topic/138819/how-to-convert-triangles-into-quads


import lx
import modo
import math

mergehack = True
f2mode = False
edge_extend_mode = False
cavity_bridge_mode = False
cavity_bevel_mode = False
cavity_bevel_select = False
corner_fill_mode = False
verbose = True
symmetry_axis = 0
sel_vert = []
edge_islands = []
sel_edges = []
og_verts = []


def find_fourth_vert(v3_coordlist):
    a, b, c = v3_coordlist[0], v3_coordlist[1], v3_coordlist[2]
    ac = c - a
    midpoint = a + (ac / 2)
    n_midpoint = midpoint - b
    return midpoint + n_midpoint


def fn_dist(v1, v2):
    dist = [(a - b)**2 for a, b in zip(v1, v2)]
    dist = math.sqrt(sum(dist))
    return dist


def pairsplit(vertlist):
    pairs = []
    while len(vertlist) > 1:
        pair = [vertlist[0], vertlist[1]]
        vertlist.pop(0)
        pairs.append(pair)
    return pairs


def lines_intersect(coordslist):
    # Find closest point between 2 vectors (Input 4 coords). Paul Bourkes method via Seneca Menards implementation.
    p1, p2, p3, p4 = coordslist[0], coordslist[1], coordslist[2], coordslist[3]

    p13 = p1[0] - p3[0], p1[1] - p3[1], p1[2] - p3[2]
    p43 = p4[0] - p3[0], p4[1] - p3[1], p4[2] - p3[2]
    p21 = p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2]

    # eps = 0.000002
    # if abs(p43[0]) < eps and abs(p43[1]) < eps and abs(p43[2]) < eps:
    #     print("eps?", (abs(p43[0]) < eps))
    # if abs(p21[0]) < eps and abs(p21[1]) < eps and abs(p21[2]) < eps:
    #     print("eps?", (abs(p21[0]) < eps))

    d1343 = p13[0] * p43[0] + p13[1] * p43[1] + p13[2] * p43[2]
    d4321 = p43[0] * p21[0] + p43[1] * p21[1] + p43[2] * p21[2]
    d1321 = p13[0] * p21[0] + p13[1] * p21[1] + p13[2] * p21[2]
    d4343 = p43[0] * p43[0] + p43[1] * p43[1] + p43[2] * p43[2]
    d2121 = p21[0] * p21[0] + p21[1] * p21[1] + p21[2] * p21[2]

    denom = d2121 * d4343 - d4321 * d4321
    # if abs(denom) < eps:
    #     print("eps?", (abs(denom) < eps))

    numer = d1343 * d4321 - d1321 * d4343

    mua = numer / denom
    mub = (d1343 + d4321 * mua) / d4343

    pa = p1[0] + (p21[0] * mua), p1[1] + (p21[1] * mua), p1[2] + (p21[2] * mua)
    pb = p3[0] + (p43[0] * mub), p3[1] + (p43[1] * mub), p3[2] + (p43[2] * mub)
    result = (pa[0] + pb[0]) * 0.5, (pa[1] + pb[1]) * 0.5, (pa[2] + pb[2]) * 0.5

    return result


def sort_edges(loopEdges):
    rowList = []
    vertRow = []

    while (len(loopEdges) - 1) > 0:
        vertRow = [loopEdges[0][0], loopEdges[0][1]]
        loopEdges.pop(0)
        rowList.append(vertRow)

        for n in range(0, len(loopEdges)):
            i = 0
            for loopVerts in loopEdges:
                if vertRow[0] == loopVerts[0]:
                    vertRow.insert(0, loopVerts[1])
                    loopEdges.pop(i)
                    break
                elif vertRow[0] == loopVerts[1]:
                    vertRow.insert(0, loopVerts[0])
                    loopEdges.pop(i)
                    break
                elif vertRow[-1] == loopVerts[0]:
                    vertRow.append(loopVerts[1])
                    loopEdges.pop(i)
                    break
                elif vertRow[-1] == loopVerts[1]:
                    vertRow.append(loopVerts[0])
                    loopEdges.pop(i)
                    break
                else:
                    i = i + 1
    return rowList


# =================================================================================
# Scene checks
# =================================================================================
layer_index = lx.eval('query layerservice layers ? selected')
layer_ID = lx.eval1('query layerservice layer.ID ? {%s}' % layer_index)
lx.eval('select.subItem {%s} set' % layer_ID)

scene = modo.scene.current()
mesh = scene.selectedByType('mesh')

if len(mesh) > 1:
    sys.exit(": --- Selection Error : More than one item selected? ---")

if mesh:

    mesh = mesh[0]
    geo = mesh.geometry

    # check for visibility
    mesh_vis = mesh.channel("visible").get()
    if mesh_vis == "off" or "allOff":
        mesh.channel("visible").set("default")

else:
    sys.exit(": --- Selection Error : Valid mesh item not selected? ---")

# symmetry check
if lx.eval('symmetry.state ?'):
    symmetry_mode = True
    symmetry_axis = lx.eval('symmetry.axis ?')
    lx.eval('select.symmetryState 0')
else:
    symmetry_mode = False


# =================================================================================
# Selections
# =================================================================================
selmode = lx.eval('query layerservice selmode ?')

if selmode == "vertex":
    sel_vert = geo.vertices.selected

    if not symmetry_mode:
        if len(sel_vert) == 1:
            f2mode = True
    elif symmetry_mode:
        if len(sel_vert) == 2:
            f2mode = True

elif selmode == "edge":

    sel_edges = []
    sym_edges = []
    sym_islands = []
    edge_islands = []
    sel_edges_index = []
    border_edge_count = 0
    vert_count = 0

    for edge in geo.edges.selected:
        sel_edges.append(edge)
        edge_verts = edge.vertex_indices

        if len(edge.polygons) == 1:
            border_edge_count += 1

        if symmetry_mode:
            if lx.eval('query layerservice vert.wdefpos ? %s' % edge_verts[0])[symmetry_axis] >= 0:
                sym_edges.append(edge_verts)
            else:
                sel_edges_index.append(edge_verts)
        else:
            sel_edges_index.append(edge_verts)

    vert_count = len(list(set([i for j in sel_edges_index for i in j])))

    if not symmetry_mode:
        if len(sel_edges_index) != border_edge_count:
            sys.exit(": --- Selection mode error - Please select border edges only. ")

        edge_islands = sort_edges(sel_edges_index)
        if len(edge_islands) == 2:
            cavity_bridge_mode = True

        elif len(edge_islands) == 1:
            loop_vert_count = len(list(set([i for i in edge_islands[0]])))
            if vert_count == loop_vert_count:
                if edge_islands[0][0] == edge_islands[0][-1]:
                    edge_extend_mode = True
                else:
                    corner_fill_mode = True

    elif symmetry_mode:
        if len(sel_edges_index) + len(sym_edges) != border_edge_count:
            sys.exit(": --- Selection mode error - Please select border edges only. ")

        edge_islands = sort_edges(sel_edges_index)
        if sym_edges: sym_islands = sort_edges(sym_edges)
        else: symmetry_mode = False

        if len(edge_islands) == 2 and len(sym_islands) == 2:
            cavity_bridge_mode = True
            edge_islands = edge_islands + sym_islands

        if len(edge_islands) == 1 and len(sym_islands) == 1:
            loop_vert_count1 = len(list(set([i for i in edge_islands[0]])))
            loop_vert_count2 = len(list(set([i for i in sym_islands[0]])))
            if (vert_count * 2) == (loop_vert_count1 + loop_vert_count2):
                if edge_islands[0][0] == edge_islands[0][-1]:
                    edge_extend_mode = True
                else:
                    corner_fill_mode = True


elif selmode == "polygon":
    sel_polys = list(geo.polygons.selected)
    if sel_polys:
        cavity_bevel_mode = True
        og_verts = []
        for p in sel_polys:
            verts = p.vertices
            for v in verts:
                og_verts.append(v)

        lx.eval('select.all')
        lx.eval('select.editSet ke_tempss add')
        # lx.eval('select.drop polygon')
        geo.polygons.select(sel_polys, replace=True)
else:
    sys.exit(": --- Selection mode error - Please select appropriate elements. ")


# =================================================================================
# Mode Processing
# =================================================================================
if verbose:
    print("-----------CavityBridge---------------")
    print("f2mode:", f2mode)
    print("edge extend mode:", edge_extend_mode)
    print("cavity bridge mode:", cavity_bridge_mode)
    print("cavity bevel mode:", cavity_bevel_mode)
    print("corner fill mode:", corner_fill_mode)

# ---------------------------------------------------------------------------------
# F2 Mode
# ---------------------------------------------------------------------------------
if f2mode:
    # Inspired by the blender add-on thusly.
    for i in sel_vert:
        # lx.eval('select.drop edge')
        # lx.eval('select.drop vertex')
        # lx.eval('select.drop polygon')
        geo.edges.select(None)
        border_verts = []
        test_edges = []
        poslist = []

        b_point = i.index

        for iv in i.vertices:
            test_edges.append([i.index, iv.index])

        for edge in test_edges:
            lx.eval('select.element %s %s add %s %s' % (layer_index, 'edge', edge[0], edge[1]))

        for e in geo.edges.selected:
            poly_check = e.polygons
            if len(poly_check) == 1:
                border_verts.extend(e.vertex_indices)

        if not border_verts:
            sys.exit(": --- Selection Error - No border verts selected?---")

        border_verts = list(set(border_verts))
        border_verts = [i for i in border_verts if i != b_point]
        border_verts.insert(1, b_point)

        for v in geo.vertices.iterByList(border_verts):
            poslist.append(modo.Vector3(v.position))

        fourth_vert = find_fourth_vert(poslist)

        new_vert = geo.vertices.new(fourth_vert)
        geo.setMeshEdits()

        quadverts = border_verts
        quadverts.append(new_vert.index)

        geo.vertices.select(quadverts, replace=True)
        lx.eval('poly.make auto')

        geo.edges.select(None)
        geo.polygons.select(None)

    # Quick merge hack
    if mergehack:
        # select og vert, expand x2, if same pos: merge
        lx.eval('select.typeFrom vertex')
        geo.vertices.select(sel_vert)
        lx.eval('select.expand')
        lx.eval('select.expand')
        lx.eval('!!vert.merge fixed dist:0.0005 disco:false')
        lx.eval('select.drop vertex')

# ---------------------------------------------------------------------------------
# Edge Extend Mode
# ---------------------------------------------------------------------------------
elif edge_extend_mode:
    sys.exit(": --- Continous Loop? - Please select separated ends (on the angled sides) of a cavity --- ")

    # edge_lengths = []
    # edge_length = []
    #
    # for edge in sel_edges:
    #     verts = [int(i) for i in edge.vertex_indices]
    #     p1 = lx.eval('query layerservice vert.pos ? {%s}' % verts[0])
    #     p2 = lx.eval('query layerservice vert.pos ? {%s}' % verts[1])
    #     edge_lengths.append(fn_dist(p1, p2))
    #
    # edge_length = sorted(edge_lengths)[0]
    #
    # lx.eval('tool.set edge.extend on')
    # lx.eval('tool.reset')
    # lx.eval('tool.attr edge.extend inset {%s}' % edge_length)
    # lx.eval('tool.doApply')
    # lx.eval('tool.set edge.extend off')
    # lx.eval('poly.make auto')

# ---------------------------------------------------------------------------------
# Corner Fill Mode
# ---------------------------------------------------------------------------------
elif corner_fill_mode:
    sys.exit(": --- Selection not supported - Please select separated ends (on the angled sides) of a cavity --- ")


# ---------------------------------------------------------------------------------
# Cavity Bridge Mode
# ---------------------------------------------------------------------------------
elif cavity_bridge_mode:

    lx.eval('select.typeFrom vertex')
    geo.polygons.select(None)
    single_edge = 0
    new_verts = []

    for edgeverts in edge_islands:
        vertcheck = len(edgeverts)
        poslist = []

        if vertcheck == 2:
            new_verts.append(edgeverts)
            single_edge += 1

        elif vertcheck == 3:
            for v in geo.vertices.iterByList(edgeverts):
                poslist.append(modo.Vector3(v.position))

            fourth_vert = find_fourth_vert(poslist)
            new_vert = geo.vertices.new(fourth_vert)

            geo.setMeshEdits()

            new_verts.append(new_vert)
            quadverts = edgeverts
            quadverts.append(new_vert.index)

            geo.vertices.select(quadverts, replace=True)
            lx.eval('poly.make auto')

        elif vertcheck >= 4:
            for v in geo.vertices.iterByList(edgeverts):
                poslist.append(modo.Vector3(v.position))

            vectors = poslist[0], poslist[1], poslist[-2], poslist[-1]
            b_point = modo.Vector3(lines_intersect(vectors))
            coords = poslist[0], b_point, poslist[-1]
            fourth_vert = find_fourth_vert(coords)
            new_vert = geo.vertices.new(fourth_vert)

            geo.setMeshEdits()

            new_verts.append(new_vert)
            quadverts = edgeverts
            quadverts.append(new_vert.index)

            geo.vertices.select(quadverts, replace=True)
            lx.eval('poly.make auto')

    lx.eval('select.typeFrom polygon')
    lx.eval('select.convert edge')

    for e in sel_edges:
        edge = e.vertex_indices
        lx.eval('select.element %s %s remove %s %s' % (layer_index, 'edge', edge[0], edge[1]))

    if single_edge == 1:
        lx.eval('select.element %s %s add %s %s' % (layer_index, 'edge', new_verts[0][0], new_verts[0][1]))

    if symmetry_mode:
        lx.eval('select.symmetryState 1')

    # Bridge the new cavity sides
    lx.eval('tool.set edge.bridge on')
    lx.eval('tool.reset')
    lx.eval('tool.setAttr edge.bridge segments 0')
    lx.eval('tool.doApply')
    lx.eval('tool.set edge.bridge off 0')

    if not single_edge:
        lx.eval('select.drop edge')
        if not symmetry_mode:
            lx.eval('select.element %s %s add %s %s' % (layer_index, 'edge', new_verts[0].index, new_verts[1].index))
# ---------------------------------------------------------------------------------
# Cavity Bevel Mode
# ---------------------------------------------------------------------------------
elif cavity_bevel_mode:

    # Got weird results from the TD edge-vert indexes...back to good ole LS + boundary macro
    lx.eval('select.type edge')
    lx.eval('select.drop edge')
    lx.eval('select.type polygon')
    lx.eval('select.boundary')

    edge_lengths = []
    for e in geo.edges.selected:
        vp = list(e.vertex_indices)
        pair = ["(", str(vp[0]), ",", str(vp[1]), ")"]  # Modo LS expects this string format?
        edge_lengths.append(lx.eval('query layerservice edge.length ? %s' % ''.join(pair)))

    edge_length = sorted(edge_lengths)[0] * -1
    lx.eval('select.typeFrom polygon')

    lx.eval('tool.set *.bevel on')  # back-up bevel settings ? Nah ;)
    lx.eval('tool.reset')
    lx.eval('tool.attr poly.bevel shift {%s}' % edge_length)
    lx.eval('tool.doApply')
    lx.eval('tool.set poly.bevel off 0')

    # Silly cleanup (when minecrafting complex shapes...)

    lx.eval('select.typeFrom vertex')
    geo.vertices.select(og_verts)
    lx.eval('select.expand')
    lx.eval('!!vert.merge fixed dist:0.0005 disco:false')

    # Attempt to quadralate the new polys....
    lx.eval('select.typeFrom polygon')
    lx.eval('select.all')
    lx.eval('select.useSet ke_tempss deselect')

    try:
        lx.eval('!!@quadralate_seneca.pl')
    except Exception as e:
        print("Aw...tried to use senecas quadralate and couldn't find it. You should really have that one! ;)\n", e)
        pass

    lx.eval('select.clearSet ke_tempss type:polygon')
    lx.eval('select.drop vertex')
    lx.eval('select.drop polygon')

else:
    sys.exit(": --- Script aborted. Selection error? --- ")

# cleanup
if symmetry_mode:
    lx.eval('select.symmetryState 1')
