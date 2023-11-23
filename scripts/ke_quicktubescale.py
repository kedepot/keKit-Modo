# python

# QuickTubeScale 1.0 Kjell Emanuelsson 2018
# Activated appropriate scaling tool for selected tube(s) IF the selected tube(s) has border edges or ngon caps.
# Select ring edge(s) OR any polygon(s) on the tube(s).

import lx
import modo

layer_index = lx.eval('query layerservice layers ? selected')
layer_ID = lx.eval1('query layerservice layer.ID ? {%s}' % layer_index)
lx.eval('select.subItem {%s} set' % layer_ID)

scene = modo.scene.current()
mesh = scene.selectedByType('mesh')

if mesh:
    mesh = mesh[0]
    geo = mesh.geometry

    # check for visibility
    mesh_vis = mesh.channel("visible").get()
    if mesh_vis == "off" or "allOff":
        mesh.channel("visible").set("default")

else:
    modo.dialogs.alert(title="Script Aborted", message="Selection Error : Valid mesh item not selected?.")
    sys.exit(": --- Selection Error : Valid mesh item not selected? ---")

sel_mode = lx.eval('query layerservice selmode ?')

if sel_mode == "edge" and geo.edges.selected:
    lx.eval('select.loop')
    lx.eval('select.ring')
    lx.eval('tool.set actr.local on')
    lx.eval('tool.set TransformScale on')

elif sel_mode == "polygon":
    sel_polys = list(geo.polygons.selected)

    if sel_polys:

        islands = []
        first_island = sel_polys[0].getIsland()
        islands.append(first_island)
        sel_polys = [i for i in sel_polys if i not in first_island]

        maxloop, loop = len(sel_polys)*2, 0  # just in case...

        while sel_polys:
            loop += 1
            new_island = sel_polys[0].getIsland()
            if new_island:
                islands.append(new_island)
                sel_polys = [i for i in sel_polys if i not in new_island]
            if loop > maxloop: break

        for island in islands:

            # Boundary edges check --------------------------------------------------
            lx.eval('select.drop edge')
            lx.eval('select.type polygon')
            geo.polygons.select(island, replace=True)
            lx.eval('select.boundary')

            # ...or ngon caps check ------------------------------------------------
            if not geo.edges.selected:
                lx.eval('select.type polygon')
                sel_polys = geo.polygons.selected

                ngon = []
                for poly in sel_polys:
                    if poly.numVertices >= 5:
                        ngon.append(poly)
                if ngon:
                    geo.polygons.select(ngon, replace=True)
                    lx.eval('select.boundary')

            lx.eval('select.editSet ke_tempSelSet add')

        lx.eval('select.drop polygon')
        lx.eval('select.type edge')
        lx.eval('select.useSet ke_tempSelSet select')
        lx.eval('select.ring')
        lx.eval('tool.set actr.local on')
        lx.eval('tool.set TransformScale on')

else:
    modo.dialogs.alert(title="Script Aborted", message="Selection Error : Not poly/edge mode?.")

lx.eval('vertMap.deleteByName EPCK ke_tempSelSet')
