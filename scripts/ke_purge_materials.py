# python
# PurgeMaterials 1.1 - Kjell Emanuelsson 2018
# Removes unused materials (nothing using the tag) with a nice report print out + alert msg
#
# 1.1 - Disabled dialogue - gets too long

import modo
import lx

msg_enable = False

scene = modo.Scene()

print("--------Purge Empty Materials---------")

# og_mats = scene.items(itype='advancedMaterial', superType=True)  # meh not that important?
og_tags = [mat.channel('ptag').get() for mat in scene.iterItems(lx.symbol.sITYPE_MASK)
           if mat.channel('ptyp').get() == 'Material']
og_tags = list(set(og_tags))

# zap
lx.eval('!!material.purge')

# After
tags = [mat.channel('ptag').get() for mat in scene.iterItems(lx.symbol.sITYPE_MASK)
        if mat.channel('ptyp').get() == 'Material']
tags = list(set(tags))

removed = [tag for tag in og_tags if tag not in tags]

if removed:
    if msg_enable:
        modo.dialogs.alert(title="Purge Unused Materials Result",
                           message="Nr of Materials Removed: %s \nName: " % len(removed) + str([i for i in removed]))

    for i in removed:
        print(i)
    print("Nr. Unused Materials removed: ", len(removed))

else:
    if msg_enable:
        modo.dialogs.alert(title="Purge Unused Materials Result",
                           message="No unused materials found: Nothing was purged.")
    print("  No unused materials found.")
