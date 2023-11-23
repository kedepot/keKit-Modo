# python

# SwapAlltoLast v1.2 - Kjell Emanuelsson 2019-21
#
# This will make new items out of the last selected item with the  transforms intact for the selected items.
# Useful for replacing instance-sources with old transforms unchanged.
# Including a "to first" option too,  if you prefer to work that way.
# 1.1 - fixed unparenting/instance source replacement issues + selecting result now.
# 1.2 - Python3

import modo

scl = True
rot = True
alltofirst = False
alltolast = True
orphaned = False
old_rot = modo.Matrix3()
old_scl = modo.Vector3()
u_args = lx.args()

for i in range(len(u_args)):
    if "noscale" in u_args:
        scl = False
    if "norot" in u_args:
        rot = False
    if "alltolast" in u_args:
        alltolast = True
        alltofirst = False


print("==================== Swap All To Last =========================")

scene = modo.scene.current()
allowed_types = ['mesh', 'meshInst', 'groupLocator', 'camera', 'locator', 'portal', 'meshLight',
                 'polyRender', 'sunLight', 'photometryLight', 'pointLight', 'spotLight', 'areaLight',
                 'cylinderLight', 'domeLight']

sel_items = []
selection = scene.selected

for item in selection:
    if item.type in allowed_types:
        sel_items.append(item)

if not sel_items: sys.exit(": No valid items selected? ")

src_parent = []

if alltofirst: src = sel_items[0]
else: src = sel_items[-1]

src_locator = modo.LocatorSuperType(src)
src_parents = src.parents
if src_parents:
    src_parent = src_parents[0]

if alltofirst: sel_items.pop(0)
else: sel_items.pop(-1)

print("Replacement Item: ", src_locator)

sel_new = []

for item in sel_items:

    # Need to check or modo will crash...
    if item.isAnInstance:
        inst_src = item.itemGraph(graphType='source').forward()[0]
        if src_locator == inst_src:
            sys.exit(":---> You are trying to replace an instance with its own source? <---")

    # check if you are trying to replace an instance source
    if not item.isAnInstance:
        find_inst = item.itemGraph(graphType='source').reverse()
        print("InstSource check:", find_inst)
        if find_inst:
            sys.exit(":---> You are trying to replace an instance source item. "
                     "Instances would be removed too. Aborting.) <---")

    # Check parents & Temp-Orphaning
    parents = item.parents
    parent = None

    if parents:
        parent = parents[0]
        if parent == src_parent:
            orphaned = False
        else:
            lx.eval('item.parent {%s} {%s} 0 inPlace:0' % (item.id, "None"))
            orphaned = True
        print("Parents:", parents, "	  Orphaned:", orphaned)

    # check for visibility (including this just because there was some issue (I vaguely remember) that needed it...)
    vis = item.channel("visible").get()
    if vis == "off" or "allOff":
        item.channel("visible").set("default")

    new_item = scene.duplicateItem(src_locator)
    new_locator = modo.LocatorSuperType(new_item)

    old_item = modo.LocatorSuperType(item)
    old_pos = old_item.position.get()
    if rot: old_rot = old_item.rotation.get()
    if scl: old_scl = old_item.scale.get()

    new_locator.position.set(old_pos)
    if rot: new_locator.rotation.set(old_rot)
    if scl: new_locator.scale.set(old_scl)

    sel_new.append(new_item)

    if orphaned and parent:
        lx.eval('item.parent {%s} {%s} 0 inPlace:0' % (new_item.id, parent.id))

scene.removeItems(sel_items)
scene.select(sel_new)
