# python

# Retube 1.1 Kjell Emanuelsson 2018-21
# 1.1 - Python3
# Reconstructs tubes (and similar) geo. Use existing tube as basis or specify new custom settings in the menu.
# POLY Selection: Select any polygon per tube. Values for sides etc sampled from the end-rings (border edges or ngons)
# EDGE Selection: Values are sampled from the selected ring(s) in edge mode. Note: Not-ring edge selection will
# be like random poly selection. + If you select a ring edge inside the tube (not ends) - it will cut the tube off at
# that point. (which side gets cut off can be random tho) Each tube will be autodetected if it has an ngon cap or
# open cap. Note: Closed Tubes without ends are not detected automatically. New settings Menu: Overrides the values
# for selected tube(s).

import lx
import modo
from math import sqrt

user_args = lx.args()

mesh_type = "face"
new_item_mode = False
select_result = False
rad_override = False
replace = False
closed = False
segments = 1
user_mode = False
cap = False
verbose = False
first_edge_sel_vert = 0
first_ring_vert = 0
# new_item
mon = lx.Monitor()
mon.init(100)
start = 0
sides = []
rad = 1

if verbose:
    print("--------ReTuber---------")
    import time
    start = time.time()

# UserValue checks
if lx.eval('user.value ke_retube.control ?') != "selection":
    user_mode = True

if user_mode:
    sides = lx.eval('user.value ke_retube.sides ?')
    segments = lx.eval('user.value ke_retube.seg ?')
    rad = lx.eval('user.value ke_retube.rad ?')
    cap = lx.eval('user.value ke_retube.cap ?')

    if sides < 3 or segments < 1 or rad == 0.0:
        sys.exit(": --- Invalid user settings. Aborting. ---")

# Options checks
if lx.eval('user.value ke_retube.replace ?') == "on":
    replace = True
if lx.eval('user.value ke_retube.newitem ?') == "on":
    new_item_mode = True
if lx.eval('user.value ke_retube.closed ?') == "on":
    closed = True
if lx.eval('user.value ke_retube.select ?') == "on":
    select_result = True
if lx.eval('user.value ke_retube.cap ?') == "on":
    cap = True
if lx.eval('user.value ke_retube.radover ?') == "on":
    rad_override = True

twist_length = lx.eval('user.value ke_retube.length ?')
twist_degrees = lx.eval('user.value ke_retube.degrees ?')

usrval_mesh = lx.eval('user.value ke_retube.mesh ?')
if usrval_mesh == "subd":
    mesh_type = "subpatch"
elif usrval_mesh == "psubd":
    mesh_type = "psubdiv"
else: pass

if verbose and user_mode:
    print("User Values:")
    print("Sides, Segments, Radius, Cap: ", sides, segments, rad, cap)


def sort_edges(loopEdges):
    rowList = []
    vertRow = []

    while (len(loopEdges) - 1) > 0:
        vertRow = [loopEdges[0][0], loopEdges[0][1]]
        loopEdges.pop(0)
        rowList.append(vertRow)

        for n in range(0, len(loopEdges)):
            i = 0
            for edgeverts in loopEdges:
                if vertRow[0] == edgeverts[0]:
                    vertRow.insert(0, edgeverts[1])
                    loopEdges.pop(i)
                    break
                elif vertRow[0] == edgeverts[1]:
                    vertRow.insert(0, edgeverts[0])
                    loopEdges.pop(i)
                    break
                elif vertRow[-1] == edgeverts[0]:
                    vertRow.append(edgeverts[1])
                    loopEdges.pop(i)
                    break
                elif vertRow[-1] == edgeverts[1]:
                    vertRow.append(edgeverts[0])
                    loopEdges.pop(i)
                    break
                else:
                    i = i + 1
    return rowList


def edge_index_filter(ls_edges):
    edges = []
    for edge in ls_edges:
        indices = edge[1:-1]
        indices = indices.split(',')
        indices = [int(i) for i in indices]
        edges.append(indices)
    return edges


def avg_pos(verts):
    vPos = []
    for v in verts:
        vPos.append(lx.evalN('query layerservice vert.wdefpos ? %s' % v))
    vPos = [sum(pos) / len(pos) for pos in zip(*cen)]
    return vPos


def tube_tool(centers, sides, rad, cap):
    tubeSegNr = 1
    lx.eval('tool.set prim.tube on')
    lx.eval('tool.reset')
    lx.eval('tool.setAttr prim.tube mode add')
    lx.eval('tool.setAttr prim.tube sides %s' % sides)
    lx.eval('tool.setAttr prim.tube segments %s' % segments)
    lx.eval('tool.setAttr prim.tube radius %s' % rad)
    lx.eval('tool.attr prim.tube closed %s' % closed)
    if not closed: lx.eval('tool.attr prim.tube caps %s' % cap)
    lx.eval('tool.attr prim.tube twist %s' % twist_degrees)
    for c in centers:
        lx.eval('tool.setAttr prim.tube number %s' % tubeSegNr)
        tubeSegNr += 1
        lx.eval('tool.setAttr prim.tube ptX %s' % c[0])
        lx.eval('tool.setAttr prim.tube ptY %s' % c[1])
        lx.eval('tool.setAttr prim.tube ptZ %s' % c[2])
    lx.eval('tool.doApply')
    lx.eval('tool.set prim.tube off')


def msg_selection_error():
    modo.dialogs.alert(title="Selection Error", message=" Invalid Selection ? ")
    sys.exit("Invalid selection? - Aborting script.")


def msg_gen_error():
    modo.dialogs.alert(title="Geometry/Unknown Error", message="Unexpected - Bad or non-uniform geo?")
    sys.exit("Unexpected - Bad or non-uniform geo? - Aborting script.")


# =================================================================================
# Scene check / setup
# =================================================================================
layer_index = lx.eval('query layerservice layers ? selected')
layer_ID = lx.eval1('query layerservice layer.ID ? {%s}' % layer_index)
lx.eval('select.subItem {%s} set' % layer_ID)

scene = modo.scene.current()
mesh = scene.selectedByType('mesh')

if mesh:
    mesh = mesh[0]
    geo = mesh.geometry

    # check for visibility
    mesh_vis = mesh.channel("visible").get()
    if mesh_vis == "off" or "allOff":
        mesh.channel("visible").set("default")

else:
    sys.exit(": --- Selection Error : Valid mesh item not selected? ---")

lx.eval('workPlane.reset')

# symmetry check
if lx.eval('symmetry.state ?'):
    symmetry_mode = True
    lx.eval('select.symmetryState 0')
else:
    symmetry_mode = False

sel_mode = lx.eval('query layerservice selmode ?')

if new_item_mode:
    new_item = scene.addItem(itype='mesh', name='tubeMesh')
else:
    new_item = None


# =================================================================================
# Process Selection
# =================================================================================

replace_polys = []
esel_polys = []
first_edge_sel = []

if sel_mode == "edge":

    lx.eval('select.loop')
    first_edge_sel = edge_index_filter(lx.evalN('query layerservice edges ? selected'))
    first_edge_sel_vert = int(first_edge_sel[0][0])
    first_edge_sel = sort_edges(first_edge_sel)

    edge_poly = []
    for edge in first_edge_sel:
        e = edge[0], edge[1]
        ep = lx.eval('query layerservice edge.polyList ? {%s}' % str(e))
        if type(ep) != int:
            ep = [int(p) for p in ep]
            edge_poly.extend(ep)
        else: edge_poly.append((ep))

    lx.eval('select.type polygon')
    esel_polys = geo.polygons.select(edge_poly)

    sel_mode = "polygon"

    if verbose:
        print("Edge-Mode Rings:", len(first_edge_sel))
        print("First Vert:", first_edge_sel_vert)


if sel_mode == "polygon":

    if esel_polys:
        sel_polys = list(esel_polys)
    else:
        sel_polys = list(geo.polygons.selected)

    if sel_polys:
        # Selections & island sorting  -------------------------------------------
        first_ngon_check = sel_polys[0]
        islands = []
        first_island = sel_polys[0].getIsland()
        islands.append(first_island)
        sel_polys = [i for i in sel_polys if i not in first_island]

        loop_limit = len(sel_polys) * 2  # just in case...
        loop = 0

        while sel_polys:
            loop += 1
            new_island = sel_polys[0].getIsland()
            if new_island:
                islands.append(new_island)
                sel_polys = [i for i in sel_polys if i not in new_island]
            if loop > loop_limit: break

        if verbose:
            print("Islands found: ", len(islands))

        # for reselection later
        replace_polys = [i[0] for i in islands]

        for island in islands:
            ngon = []

            if not closed:
                # Boundary edges check ----------------------------------------------
                lx.eval('select.drop edge')
                lx.eval('select.type polygon')
                geo.polygons.select(island, replace=True)
                lx.eval('select.boundary')

                # ...or ngon caps check ---------------------------------------------
                sel_edges = lx.evalN('query layerservice edges ? selected')
                if not sel_edges:
                    lx.eval('select.type polygon')
                    sel_polys = geo.polygons.selected

                    for poly in sel_polys:
                        if poly.numVertices >= 5:
                            ngon.append(poly)

                    if ngon:
                        for n in ngon:
                            if n == first_ngon_check:
                                ngon = n
                                break
                        geo.polygons.select(ngon, replace=True)
                        lx.eval('select.boundary')

                    sel_edges = lx.evalN('query layerservice edges ? selected')

            elif closed:
                sel_edges = first_edge_sel
                lx.eval('select.type edge')
            else: break

            # Sorting correct ring order ------------------------------------
            lx.eval('select.ring')
            edge_rings = edge_index_filter(lx.evalN('query layerservice edges ? selected'))
            edge_rings = sort_edges(edge_rings)

            rings_order = []
            unorder_rings = []

            for ring in edge_rings:
                unorder_rings.append([int(i) for i in ring])

            # Sort First Ring ---------------------------------------------------
            if not closed:
                first_ring = edge_index_filter(sel_edges)
                first_ring_vert = sel_edges[0].split(',')[0][1:]
                first_ring_vert = int(first_ring_vert)
            elif closed:
                first_ring_vert = first_edge_sel_vert

            if verbose:
                print("First Ring Vert: ", first_ring_vert)
                print(sel_edges)

            # Now the desired order of rings...(with special edge sel check first...)
            if first_edge_sel:
                for ring in unorder_rings:
                    if ring in first_edge_sel:
                        rings_order.append(ring)
                        unorder_rings.remove(ring)
                        break

            elif not rings_order:
                for ring in unorder_rings:
                    for vert in ring:
                        if vert == first_ring_vert:
                            rings_order.append(ring)
                            unorder_rings.remove(ring)
                            break

            if rings_order:
                # Using the limit for non-end ring selection (trim) "feature" ;) TD:split tube?
                loop_limit = len(unorder_rings[0]) * len(unorder_rings)
                loop_check = 0

                while unorder_rings:
                    mon.step()
                    loop_check += 1
                    for ring in unorder_rings:
                        prev_ring = rings_order[-1]
                        ring_verts = lx.eval('query layerservice vert.vertList ? {%s}' % ring[0])
                        for v in ring_verts:
                            if v in prev_ring:
                                rings_order.append(ring)
                                unorder_rings.remove(ring)
                                continue

                    if loop_check > loop_limit:
                        print(" -- Geo / Selection error? Cant sort edge rings - Aborting sort --")
                        break

                edge_rings = rings_order
                if verbose:
                    print("Ring sorting Loops:", loop_check, "  Limit:", loop_limit)

            # Get Material & Part
            mat_poly = str(island[0]).split(',')[0][17:]  # instead of td-sdk call...hack yeah;)
            material = lx.eval('query layerservice poly.tags ? {%s}' % mat_poly)[0]
            part = lx.eval('query layerservice poly.part ? {%s}' % mat_poly)

            # Set or calculate prefs (from first ring) and average center points --------------
            centers = []
            cen = []

            cen_ring = edge_rings[0]
            cen_ring = list(set(cen_ring))
            cen_count = len(cen_ring)

            for v in cen_ring:
                cen.append(lx.evalN('query layerservice vert.wdefpos ? %s' % v))

            cen = [sum(pos) / len(pos) for pos in zip(*cen)]
            v1_pos = lx.evalN('query layerservice vert.wdefpos ? %s' % cen_ring[0])

            if not user_mode:
                rad = sqrt(sum([(a - b) ** 2 for a, b in zip(cen, v1_pos)]))
                sides = cen_count
                if ngon: cap = True
                else:    cap = False

            elif rad_override:
                rad = sqrt(sum([(a - b) ** 2 for a, b in zip(cen, v1_pos)]))

            # Now avg centers for all the rings for the tube tool, optimized a bit--------------
            for ring in edge_rings:
                # opt!
                ring = list(set(ring))
                ring_len_check = len(ring)

                if ring_len_check > 8:
                    sliceval = int(ring_len_check / 4)
                    ring = ring[::sliceval]
                    ring = ring[:4]

                cen = []
                for v in ring:
                    cen.append(lx.evalN('query layerservice vert.wdefpos ? %s' % v))

                centers.append([sum(pos) / len(pos) for pos in zip(*cen)])

            # if not centers or not rad or not sides: msg_gen_error()
            if new_item_mode:
                scene.select(new_item)
                layer_index = lx.eval('query layerservice layers ? selected')

            # Tube tool using the avg center positions ------------------------------------------

            tube_tool(centers, sides, rad, cap)

            lx.eval('select.drop polygon')
            new_poly = lx.eval('query layerservice poly.N ? all') - 1
            lx.eval("select.element %s %s add %s" % (layer_index, 'polygon', new_poly))
            lx.eval('select.connect')
            if material != "Default":
                lx.eval('poly.setMaterial {%s}' % material)
            if part != "Default":
                lx.eval('poly.setPart {%s}' % part)
            lx.eval('select.editSet ke_tempSelSet add')

            if new_item_mode:
                scene.select(mesh)
                layer_index = lx.eval('query layerservice layers ? selected')

            mon.step()

            if verbose:
                print("Selection Mode Found:")
                print("Center positions:", len(centers))
                print("Radius:", rad)
                print("Sides:", sides)
                print("Material:", material, "  Part:", part)
                print("Cap(ngon):", ngon)

    else: msg_selection_error()

else: msg_selection_error()


# =================================================================================
# Finish & cleanup
# =================================================================================

if replace:
    if replace_polys:
        geo.polygons.select(replace_polys, replace=True)
        lx.eval('select.connect')
        lx.eval('delete')
    else:
        msg_gen_error()

if new_item_mode:
    scene.select(new_item)
    if select_result:
        lx.eval('select.type polygon')
        lx.eval('select.useSet ke_tempSelSet select')

# else:
#     if select_result:
#         lx.eval('select.useSet ke_tempSelSet select')
#     else:
#         lx.eval('select.drop polygon')
#         lx.eval('select.useSet ke_tempSelSet deselect')
#         lx.eval('select.drop edge')
#         lx.eval('select.type {%s}' % sel_mode)

if mesh_type != "face":
    lx.eval('select.type polygon')
    lx.eval('select.useSet ke_tempSelSet select')
    lx.eval('poly.convert face %s true' % mesh_type)
    if not select_result:
        lx.eval('select.drop polygon')

lx.eval('poly.renameTag ke_tempSelSet {} PICK')

if symmetry_mode:
    lx.eval('select.symmetryState 1')

if verbose:
    print(new_item_mode, replace)
    end = time.time()
    print("Time: ", (end - start))
