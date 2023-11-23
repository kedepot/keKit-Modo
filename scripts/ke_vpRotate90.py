#python

# ke_vpRotate v0.2 - Kjell Emanuelsson 2018-21
# 0.2 - Python3
# Rotates selected item or elements 90 degrees (clockwise on +?) depending on your viewport orientation. 
# (Perpendicular to the viewport axis facing you...)

import modo
import math

rot = -90
sX, sY, sZ = 0, 0, 0


def fn_getVieportWP():
    wpl = 2
    view_srv = lx.service.View3Dport()
    current_view = lx.object.View3D(view_srv.View(view_srv.Current()))
    view_axis = current_view.WorkPlane()[:1]
    v = int(view_axis[0])
    if v == 2:
        wpl = "view_XY"
    elif v == 1:
        wpl = "view_XZ"
    elif v == 0:
        wpl = "view_ZY"
    return wpl


def fn_avgpos(vertlist):
    vX, vY, vZ = [], [], []
    for v in vertlist:
        i = lx.eval('query layerservice vert.wdefpos ? %s' % v)
        vX.append(i[0]), vY.append(i[1]), vZ.append(i[2])
    total = len(vertlist)
    return sum(vX) / total, sum(vY) / total, sum(vZ) / total


# ---------------------------------------
# Check selections
# ---------------------------------------
slayer = lx.eval('query layerservice layers ? fg')
layerID = lx.eval1('query layerservice layer.ID ? %s' % slayer)
lx.eval('select.subItem %s add' % layerID)

selmode = lx.eval('query layerservice selmode ?')

# symmetry check	
if lx.eval1('symmetry.state ?'):
    sys.exit(": --- Aborted : Symmetry not supported ---")


lx.eval('workPlane.reset')

wp = fn_getVieportWP()

if selmode != 'item' and selmode != 'polygon':
    sys.exit(": Selection not supported : Select polygons or item.")

if selmode == 'polygon':

    p = lx.evalN('query layerservice polys ? selected')
    if len(p) != 0:
        lx.eval('select.connect')
    else:
        sys.exit(": Selection error: Nothing Selected.")

    lx.eval('select.convert vertex')
    sel_verts = lx.evalN('query layerservice verts ? selected')

    avgpos = fn_avgpos(sel_verts)

    lx.eval('workPlane.edit %s %s %s' % (avgpos[0], avgpos[1], avgpos[2]))

elif selmode == 'item':
    sX = lx.eval('transform.channel scl.X ?')
    sY = lx.eval('transform.channel scl.Y ?')
    sZ = lx.eval('transform.channel scl.Z ?')
# have to get these and re-apply (or it gets nudged)


# Rotate
lx.eval('tool.set actr.auto on')
lx.eval('tool.set xfrm.rotate on')
lx.eval('tool.reset')

if wp == "view_XY":
    lx.eval('tool.setAttr axis.auto axisZ 1')
    lx.eval('tool.setAttr axis.auto axis 2')
    lx.eval('tool.setAttr xfrm.rotate angle {%f}' % rot)
    lx.eval('tool.doApply')

elif wp == "view_XZ":
    lx.eval('tool.setAttr axis.auto axisY 1')
    lx.eval('tool.setAttr axis.auto axis 1')
    lx.eval('tool.setAttr xfrm.rotate angle {%f}' % rot)
    lx.eval('tool.doApply')

elif wp == "view_ZY":
    lx.eval('tool.setAttr axis.auto axisX 1')
    lx.eval('tool.setAttr axis.auto axis 0')
    lx.eval('tool.setAttr xfrm.rotate angle {%f}' % rot)
    lx.eval('tool.doApply')

if selmode == 'polygon':
    lx.eval('vert.center all')

lx.eval('tool.set xfrm.rotate off')
lx.eval('tool.set actr.auto off')
lx.eval('tool.doApply')


if selmode == 'polygon':
    lx.eval('workPlane.reset')

    lx.eval('select.drop vertex')
    lx.eval('select.typeFrom polygon')

elif selmode == 'item':
    lx.eval('transform.channel scl.X %s' % sX)
    lx.eval('transform.channel scl.Y %s' % sY)
    lx.eval('transform.channel scl.Z %s' % sZ)


#eof	