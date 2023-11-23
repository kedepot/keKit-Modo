# python

# EdgeSplit v1.1 - Kjell Emanuelsson 2018-21
# 1.1 Python3 + fix
# Splits the edge(s) shared by two selected verts in the middle and selects the resulting vert(s)

import lx
import modo

# -------------------------------------------------------------------------
# Initial scene check
# -------------------------------------------------------------------------
sel_layer = lx.eval('query layerservice layers ? selected')
sel_mode = lx.eval('query layerservice selmode ?')
sel_edges = lx.evalN('query layerservice edges ? selected')
sel_count = len(sel_edges)

if sel_mode != "edge" or sel_count == 0:
    print("Quitting - only works on edge selecion")
    sys.exit()

if lx.eval('symmetry.state ?'):
    symmetry_mode = True
    lx.eval('select.symmetryState 0')

else:
    symmetry_mode = False

# -------------------------------------------------------------------------
# Split Edges
# -------------------------------------------------------------------------
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
