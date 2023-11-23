# python

# ke_slice v1.1 - Kjell Emanuelsson 2018-21
# 1.1 - Python3 fixes
# Simple addition to the Edge Slice tool.
# vertex selection:    *SPLIT* edge(s) shared between selected vertices.
# any other selection: *EDGE SLICE* tool as usual.

import lx

split_mode = False
slice_mode = False
sel_edges = []
symmetry_mode = 0

# -------------------------------------------------------------------------
# Initial scene check
# -------------------------------------------------------------------------
sel_layer = lx.eval('query layerservice layers ? selected')
sel_mode = lx.eval('query layerservice selmode ?')

if sel_mode == "vertex":

    if lx.eval('symmetry.state ?'):
        symmetry_mode = True
        lx.eval('select.symmetryState 0')

    else:
        symmetry_mode = False

    if len(lx.evalN('query layerservice verts ? selected')) >= 2:
        lx.eval('select.convert edge')
        sel_edges = lx.evalN('query layerservice edges ? selected')
        sel_count = len(sel_edges)
        if sel_count:
            split_mode = True
        else:
            sys.exit()

else:
    slice_mode = True


# -------------------------------------------------------------------------
# Run slice tool
# -------------------------------------------------------------------------

if slice_mode:
    lx.eval('tool.set poly.loopSlice on 0 false')

# -------------------------------------------------------------------------
# or Split Edges
# -------------------------------------------------------------------------

elif split_mode:

    og_verts = lx.evalN('query layerservice verts ? all')
    for e in sel_edges:
        verts = [i for i in e[1:-1].split(",")]
        v1 = int(verts[0])
        v2 = int(verts[1])

        lx.eval("tool.set edge.knife on")
        lx.eval("tool.reset")
        lx.eval("tool.attr edge.knife split 0")
        lx.eval("tool.setAttr edge.knife count 1")
        lx.eval("tool.setAttr edge.knife vert0 %s%s%s" % (sel_layer - 1, ",", v1))
        lx.eval("tool.setAttr edge.knife vert1 %s%s%s" % (sel_layer - 1, ",", v2))
        lx.eval("tool.setAttr edge.knife pos 0.5")
        lx.eval("tool.doApply")
        lx.eval("tool.set edge.knife off")

    # Select split verts
    new_verts = lx.evalN('query layerservice verts ? all')
    split_vert = [int(v) for v in new_verts if v not in og_verts]
    lx.eval('!!select.drop vertex')
    lx.eval('!!select.typeFrom vertex')
    for i in split_vert:
        lx.eval('select.element %s %s add %s' % (sel_layer, 'vertex', i))

    if symmetry_mode:
        lx.eval('select.symmetryState 1')
