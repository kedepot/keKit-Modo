# python

# Purge Images 1.0 Kjell Emanuelsson 2019. Variant of the TD-SDK example by Ivo Grigull.
# Note: It will not remove clips accidentally parented to a material layer (it happens & wont show)

import modo
import lx

scene = modo.scene.current()

print("---------------- Purge Images -------------------")

selection = list(scene.items(itype=lx.symbol.sITYPE_VIDEOSTILL))

if not selection:
    sys.exit(" No Images found / Invalid Selection ? ")

count = 0

for image in selection:
    graph = image.itemGraph('shadeLoc')

    if len(graph.forward()) is 0 and len(graph.reverse()) is 0:
        count += 1
        print(image.name)
        scene.removeItems(image)

print("Nr. of Images/Clips deleted: ", count)
