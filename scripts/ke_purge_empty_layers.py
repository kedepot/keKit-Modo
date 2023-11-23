# python
# Purge Empty Layers 1.2 - Kjell Emanuelsson 2018-21
# Simple variation of the Foundry TD SDK Example, with printout + alert msg ;)
#
# 1.1 Disabled dialogue, gets silly long.
# 1.2 Python3

import modo

msg_enable = False

scene = modo.Scene()

print("--------Purge Empty Mesh Items---------")

itemList = [item for item in scene.items(itype='mesh', superType=True) if item.geometry.internalMesh.PointCount() == 0]

if itemList:

    scene.removeItems(itemList)

    if msg_enable:
        modo.dialogs.alert(title="Purge Empty Layers Result",
                           message="Nr of Layers Removed: %s \n" % len(itemList) + str([i.name for i in itemList]))
    for i in itemList:
        print(i.name)
    print("Nr of layers removed: ", len(itemList))

else:
    if msg_enable:
        modo.dialogs.alert(title="Purge Empty Layers Result", message="No empty mesh layers found: Nothing was purged.")
    print("  No empty mesh layers found.")
