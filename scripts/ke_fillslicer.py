# python

# FillSlicer v0.3B - Kjell Emanuelsson 2018-21
# 0.3 - Python3 + fixes
# Another contextual script!
# Use:
# VERTS selected - Uses the default *POLY SPLIT* command to split polygons between verts
# 1 EDGE seleceted - *SPLITS* the edge wit a vert in the middle
# EDGES ("Connected") selected - (Edges sharing continous polygons) *EDGE SLICE CONNECTED* is run
# EDGES ("Disconnected") selected - (Edges not sharing all polygons, gap in row/side loop) *EDGE SLICE* (normal) is run
# BORDER EDGES (looping) selected - *MAKE POLYGON* is run
# BORDER EDGES (not looping) selected  - Tries to run *BRIDGE TOOL*. Please make bridge-appropriate selection ;>
# POLYGON(S) selected - ke_triplesplitspin is run to *TRIPLE* or *SPINQUAD* (if already tripled))

import lx
import modo


# -------------------------------------------------------------------------
# Initial scene check
# -------------------------------------------------------------------------
sel_layer = lx.eval('query layerservice layers ? selected')
sel_mode = lx.eval('query layerservice selmode ?')
scene = modo.scene.current()
mesh = modo.Mesh()

# if lx.eval('symmetry.state ?'):
#     symmetry_mode = True
#     symmetry_axis = lx.eval('symmetry.axis ?')
# else:
#     symmetry_mode = False


# -------------------------------------------------------------------------
# vertex mode
# -------------------------------------------------------------------------
if sel_mode == "vertex":
    lx.eval('poly.split')


# -------------------------------------------------------------------------
# edge mode
# -------------------------------------------------------------------------
elif sel_mode == "edge":

    border_edge = False
    sel_edges = lx.evalN('query layerservice edges ? selected')
    sel_count = len(sel_edges)

    if sel_count == 1:
        og_verts = lx.evalN('query layerservice verts ? all')
        sel_edges = lx.eval('query layerservice edges ? selected')
        verts = [i for i in sel_edges[1:-1].split(",")]
        v1 = int(verts[0])
        v2 = int(verts[1])
        lx.eval("tool.set edge.knife on")
        lx.eval("tool.reset")
        lx.eval("tool.attr edge.knife split 0")
        lx.eval("tool.setAttr edge.knife count 1")
        lx.eval("tool.setAttr edge.knife vert0 %s%s%s" % (sel_layer-1, ", ", v1))
        lx.eval("tool.setAttr edge.knife vert1 %s%s%s" % (sel_layer-1, ", ", v2))
        lx.eval("tool.setAttr edge.knife pos 0.5")
        lx.eval("tool.doApply")
        lx.eval("tool.set edge.knife off")

        new_verts = lx.evalN('query layerservice verts ? all')
        split_vert = [int(v) for v in new_verts if v not in og_verts]
        if split_vert:
            lx.eval('!!select.typeFrom vertex')
            lx.eval('select.element %s %s set %s' % (sel_layer, 'vertex', split_vert))

    if sel_count >= 2:
        edges = []
        rows = []
        connected_polys = []
        slice_connected = False
        all_border_edges = False
        border_edge_count = 0
        islands = False

        # Check for border edges (and collect edge polys )
        for i in sel_edges:
            edge_polys = lx.eval('query layerservice edge.polyList ? {%s}' % i)
            if type(edge_polys) == int:
                border_edge = True
                border_edge_count += 1
                connected_polys.append(edge_polys)
            else:
                connected_polys.extend(edge_polys)

        # Check for connected polys to "slice connected" (using edge poly check)
        island_check = list(set(connected_polys))
        if len(connected_polys) != len(island_check):
            slice_connected = True

        if border_edge_count == sel_count:
            all_border_edges = True

        # for i in island_poly:
            # print i.getIsland()
        # print len(island_poly[0].getIsland())

        # Check for continous edge loop (used for hole selection)
        for i in sel_edges:
            indices = i[1:-1]
            indices = indices.split(',')
            edges.append(indices)

        loop_edges = list(edges)

        while (len(loop_edges) - 1) > 0:
            vert_row = [loop_edges[0][0], loop_edges[0][1]]
            loop_edges.pop(0)
            rows.append(vert_row)

            for n in range(0, len(edges)):
                i = 0
                for edgeverts in loop_edges:
                    if vert_row[0] == edgeverts[0]:
                        vert_row.insert(0, edgeverts[1])
                        loop_edges.pop(i)
                        break
                    elif vert_row[0] == edgeverts[1]:
                        vert_row.insert(0, edgeverts[0])
                        loop_edges.pop(i)
                        break
                    elif vert_row[-1] == edgeverts[0]:
                        vert_row.append(edgeverts[1])
                        loop_edges.pop(i)
                        break
                    elif vert_row[-1] == edgeverts[1]:
                        vert_row.append(edgeverts[0])
                        loop_edges.pop(i)
                        break
                    else:
                        i = i + 1

        row_count = len(rows)
        # print(row_count)

        if row_count > 2:
            print("Too many edgeloops selected. Quitting...")
            sys.exit()

        if rows[0][0] == rows[0][-1] and border_edge:

            if row_count == 1:
                print("Single Edge-loop detected, making a poly...")
                lx.eval('!!poly.make auto')
                sys.exit()

            elif row_count == 2:
                # Check if edgeloops are on connected poly islands
                island1 = lx.eval('query layerservice vert.polyList ? {%s}' % rows[0][0])
                island2 = lx.eval('query layerservice vert.polyList ? {%s}' % rows[1][0])
                island_polys = [i for i in mesh.geometry.polygons.iterByIndices(island2)]
                island_poly_check = [i.index for i in island_polys[0].getIsland()]
                if island1[0] not in island_poly_check:
                    islands = True

        if not islands and not all_border_edges:
            lx.eval('tool.set poly.loopSlice on')
            lx.eval('tool.reset')
            if slice_connected:
                lx.eval('tool.attr poly.loopSlice select true')
            else:
                lx.eval('tool.attr poly.loopSlice select false')
            lx.eval("tool.doApply")
            lx.eval('tool.set poly.loopSlice off')

        # elif  and not islands:
        elif border_edge:
            print("Trying to Bridge...")
            lx.eval('tool.set edge.bridge on')
            lx.eval('tool.setAttr edge.bridge segments 0')
            lx.eval('tool.attr edge.bridge continuous true')
            lx.eval('tool.attr edge.bridge connect true')
            lx.eval('tool.attr edge.bridge mode curve')
            lx.eval('tool.attr edge.bridge remove true')

            # --- commenting out these 2 to just activate bridge tool (to adjust settings) - click LMB
            # lx.eval('tool.doApply')
            # lx.eval('tool.set edge.bridge off')

        print(islands, border_edge, all_border_edges)

# -------------------------------------------------------------------------
# poly mode ?
# -------------------------------------------------------------------------
elif sel_mode == "polygon":
    lx.eval('@ke_triplesplitspin.py')
else: pass
