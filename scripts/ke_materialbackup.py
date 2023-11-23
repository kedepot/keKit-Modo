# python
# MaterialBackup 1.1 - Kjell Emanuelsson 2019-21
# 1.1 - Python3
# Groups the materials of the UN-selected items in your scene.
# Useful when you are not sure what materials to keep, and dont want to delete anything - you can at least clean it up;)
# Select ITEMS that have materials you want to keep as-is in the shadertree - All other materials will be grouped.
# + the group will default to visibility OFF, as that is probably intended anyway.

import modo
import lx

scene = modo.scene.current()
mat = None
print("--------Group Unselected Items Materials---------")

# Get all the tags
all_tags = [mat.channel('ptag').get() for mat in scene.iterItems(lx.symbol.sITYPE_MASK)
            if mat.channel('ptyp').get() == 'Material']
all_tags = list(set(all_tags))

# Get the tags used in the selection
sel_tags = []
for item in scene.selected:
    item_tags = []
    try:
        item_tags = set([polygon.materialTag for polygon in item.geometry.polygons])
    except Exception as e:
        print(e)
        pass
    if item_tags:
        sel_tags.extend(item_tags)

if sel_tags:
    sel_tags = [i for i in sel_tags]
else:
    sys.exit(": No tags found in selection - Selection Error ?  ")

# Get the tags/materials outside the selection to group them
group_tags = [i for i in all_tags if i not in sel_tags]
group_mats = []
for mat in scene.items(mat.type):
    current_tag = mat.channel('ptag').get()
    if current_tag in group_tags:
        group_mats.append(mat)

# scene.select(group_mats)
group = scene.addItem('mask', name="material_backup_group")
group.setParent(scene.renderItem, index=1)
for mat in group_mats:
    mat.setParent(group)
lx.eval('shader.setVisible {%s} false' % group.id)
print("Grouped Materials(tags): ", group_tags)
