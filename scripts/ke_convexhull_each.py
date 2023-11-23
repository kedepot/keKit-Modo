# python
# Convex Hull Each 1.0 - Kjell Emanuelsson 2019.
# Handler script for my "Convex Hull" script - QnD processing of all selected items, one at a time...

import modo

scene = modo.scene.current()
sel_mode = lx.eval('query layerservice selmode ?')

if sel_mode == "item":
    sel_items = list(scene.selectedByType("mesh")) + list(scene.selectedByType("meshInst"))
    sel_count = len(sel_items)
else:
    sys.exit(": --- Invalid Selection Mode Error. Item selection only for this mode. Aborting script. --- ")

if sel_count:
    for item in sel_items:
        lx.eval('select.drop item')
        scene.select(item)
        lx.eval('@ke_convexhull.py')
else:
    sys.exit(": --- Selection Error. (Mesh layers must be selected) Aborting script. --- ")

lx.eval('select.drop item')
