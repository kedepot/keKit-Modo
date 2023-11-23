#!/usr/bin/env python

# Purge Tlocs v 1.2 - Kjell Emanuelsson 2018-21
# originally by GwynneR I think...(from the modo forum)
# Added some print-outs and alert msg report
#
# 1.1 - Disabled the dialog popup, gets silly long. Enable with the variable below if you like.
# 1.2 - Python3

import lx
import modo
import lxu.select

enable_msg = False

scene_svc = lx.service.Scene()
scene = lxu.select.SceneSelection().current()
TEXLOC_TYPE = scene_svc.ItemTypeLookup(lx.symbol.sITYPE_TEXTURELOC)
shadeloc_graph = lx.object.ItemGraph(scene.GraphLookup(lx.symbol.sGRAPH_SHADELOC))


def get_texlocs():
    locs = []
    for x in range(scene.ItemCount(TEXLOC_TYPE)):
        locs.append(scene.ItemByIndex(TEXLOC_TYPE, x))
    return locs


texlocs = get_texlocs()
tlocs = []

if texlocs:

    print("--------Purge Unused Texture Locators---------")

    item_sel = lxu.select.ItemSelection()
    for texloc in texlocs:
        tl = modo.Item(texloc.Ident())
        tlocs.append(tl)
        if (shadeloc_graph.FwdCount(texloc) == 0) and (shadeloc_graph.RevCount(texloc) == 0):
            item_sel.select(texloc.Ident())
            lx.eval('!!item.delete')
            print(tl.name)

    if enable_msg:
        modo.dialogs.alert(title="Purge Unused Texture Locators Result",
                           message="Nr of Tlocs Removed: %s \nName: " % len(tlocs) + str([i.name for i in tlocs]))

    print("Nr. Unused Texture Locators removed: ", len(tlocs))

else:
    if enable_msg:
        modo.dialogs.alert(title="Purge Unused Texture Locators Result",
                           message="No unused texture locators found: Nothing was purged.")
    print("No unused texture locators found.")
