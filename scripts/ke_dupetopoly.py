#python

# DupeToPoly v1.1 - Kjell Emanuelsson 2019-2021
#
# Duplicates FIRST selected ITEM (mesh or instance) to EVERY SINGLE polygon face in the LAST selected ITEM. 
#
# Optional arguments: "border" - uses the border of polygon ISLANDS, with the workplane, to place items.
#					  "average" - uses the entire polygon ISLANDS with the workplane to place items.
#
# 1.1 - Python3 & fixes

import modo

border = False
face = True
average = False

u_args = lx.args() 

for i in range(len(u_args)):
    if "average" in u_args:
        face = False
    if "border" in u_args:
        face = False
        border = True
    else: pass

scene = modo.scene.current()
selection = list(scene.selected)	
sel_meshes = []

if not selection: 
    sys.exit(": No items selected? Select source and target mesh item.")

for item in selection:
    if item.type == "mesh" or item.type == "meshInst":
        sel_meshes.append(item)

source_item = sel_meshes[0]
target_item = sel_meshes[-1]
# print("Source: ", source_item, "Target: ", target_item)

lx.eval("select.clear item")

all_polys = list(target_item.geometry.polygons)
counter = len(all_polys)
# print("Target Polycount: ", counter)

while counter > 0:
    for i in all_polys:
        lx.eval('select.item {%s} set' % target_item.id)

        lx.eval('select.typeFrom polygon')
        target_item.geometry.polygons.select(i, replace=True)
        if not face:
            lx.eval('select.connect')

        if border:
            lx.eval('@AddBoundary.py')
            lx.eval('select.convert vertex')

        lx.eval('workPlane.reset')
        lx.eval('workPlane.fitSelect')

        if border:
            lx.eval('select.drop vertex')

        place_mesh = scene.duplicateItem(source_item, instance=False)
        lx.eval('select.item {%s} set' % place_mesh.id)
        lx.eval('item.matchWorkplanePos')
        lx.eval('item.matchWorkplaneRot')

        if not face:
            island = list(target_item.geometry.polygons.selected)

            for p in island:
                all_polys.remove(p)
            if len(all_polys) <= 0:
                counter = 0

        if face: counter -= 1

    counter -= 1


lx.eval('workPlane.reset')
lx.eval("select.clear item")

# eof