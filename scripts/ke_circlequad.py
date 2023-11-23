#python

# ke_circlequad 0.2 - Kjell Emanuelsson 2018-21
# 0.2 - Python3
# Bevels a subdivided circle ngon from poly selection islands (for making holes or cylindrical protrusions or sumn)
# Note: Uses radial align. In a very slow macro-ish way - expect LONG waits on large selections.
#       Also, intended for square-ish selections - may get wonky on long rectangles ( and uneven ngons).
#
# arguments : (or just change in the variable declares below)
#               eachface - Bevels each single face instead of selection islands
#               perfc    - Uses Seneca Menards "perfectcircle.pl" instead, if you have it.

import lx
import modo
import sys
from math import pi

u_args = lx.args()

ralign = True
verbose = False
eachface = False
div_count = 1

for i in range(len(u_args)):
    if "perfc" in u_args:
        ralign = False
    if "eachface" in u_args:
        eachface = True
    else: pass

# -----------------------------------------------------------------------------------
# Check selection mode
# -----------------------------------------------------------------------------------
scene = modo.scene.current()

sel_mode = lx.eval('query layerservice selmode ?')

if sel_mode != "polygon":
    sys.exit(": Reason: POLY mode only.")

# -----------------------------------------------------------------------------------
# Check Mesh Layer selection
# -----------------------------------------------------------------------------------
sel_mesh = []

sel_items = list(scene.selectedByType("mesh"))
sel_item_count = len(sel_items)

if sel_item_count == 1:
    sel_mesh = sel_items[0]

elif not sel_item_count:  # Setting active "foreground" mesh layer as active item layer
    fg_check = lx.eval('query layerservice layers ? fg')

    if type(fg_check) == tuple:
        sys.exit(":Reason:   Multiple selected layers not supported.")

    if fg_check:
        sel_id = lx.eval('query layerservice layer.id ? {%s}' % fg_check)
        lx.eval('select.item {%s} set' % sel_id)
        sel_mesh = scene.selected[0]

elif sel_item_count > 1:
    sys.exit(":Reason:   Multiple active source layers not supported.")

else:
    sys.exit(":Reason:   Item selection failed.")


# -----------------------------------------------------------------------------------
# Selection Island sorting
# -----------------------------------------------------------------------------------
sel_polys = list(sel_mesh.geometry.polygons.selected)

if not sel_polys:
    sys.exit(": Reason:   No polys selected?")

islands = []

if not eachface:

    while sel_polys:

        island = [sel_polys[0]]
        loop = 1
        for i in range(loop):

            for poly in island:
                search = [p for p in poly.neighbours if p in sel_polys]
                search = [p for p in search if p not in island]

                if search:
                    island.extend(search)
                    loop += 1

        islands.append(island)
        sel_polys = [p for p in sel_polys if p not in island]

else:
    for i in sel_polys:
        islands.append([i])

if verbose:
    print("ILANDS: ", len(islands), islands)

# -----------------------------------------------------------------------------------
# Main Op Loop
# -----------------------------------------------------------------------------------
resel_polys = []

for island in islands:
    lx.eval('select.drop edge')
    lx.eval('select.drop polygon')

    for p in island:
        p.select()

    lx.eval('select.boundary')
    e_len = 0.0
    for e in lx.evalN('query layerservice edges ? selected'):
        e_len += float(lx.evalN('query layerservice edge.length ? {%s}' % e)[0])
    inset = (e_len / pi) / 4  # TO-DO: check for long thin rectangles...
    if verbose:
        print("Island Edge Len:", e_len)

    lx.eval('select.type polygon')

    lx.eval('tool.set *.bevel on')
    lx.eval('tool.reset')
    lx.eval('tool.setAttr poly.bevel inset {%f}' % inset)
    lx.eval('tool.doApply')
    lx.eval('tool.set *.bevel off')

    if len(island) == 1:
        for d in range(div_count):
            lx.eval('poly.subdivide flat 0.0')
        lx.eval('poly.merge')
    else:
        lx.eval('poly.merge')

    lx.eval('select.drop edge')
    lx.eval('select.drop vertex')
    lx.eval('select.type polygon')
    lx.eval('select.boundary')

    if not ralign:
        lx.eval('@perfectCircle.pl')
    else:
        lx.eval('tool.set xfrm.radialAlign on')
        lx.eval('tool.reset')
        lx.eval('tool.doApply')
        lx.eval('tool.set xfrm.radialAlign off')

    lx.eval('select.type polygon')
    resel_polys.extend(sel_mesh.geometry.polygons.selected)

# re-select
if len(islands) > 1:
    for p in resel_polys:
        p.select()
