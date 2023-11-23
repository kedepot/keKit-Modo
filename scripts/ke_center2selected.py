# python#

# Center2Selected v1.3 - Kjell Emanuelsson 2018-21
# Places the item center to the average position of selected elements. (+ transform move tool)
#       1.3 - Python3
#   	1.2 - Added average normal mode: fits a wp and sets rotation and position there. Use with "avgnormal" argument
# 			  or "invert"  (TOO! ("ke_centerselected.py avgnormal invert" ) for an inverted variant.
# 		1.1 - Now works in item mode (and material mode) too...


import modo
import lx


u_args = lx.args()
poslist = []
avgnormal = False
invert = False
restore_wp = False
hit_pos, hit_rot = [], []
pos = modo.Vector3()

for i in range(len(u_args)):
    if "avgnormal" in u_args:
        avgnormal = True
        if "invert" in u_args:
            invert = True


def fn_avgpos(poslist):
    vX, vY, vZ = [], [], []
    for i in poslist:
        vX.append(i[0]), vY.append(i[1]), vZ.append(i[2])
    total = len(poslist)
    return sum(vX) / total, sum(vY) / total, sum(vZ) / total


scene = modo.scene.current()
# chan_read = lx.object.ChannelRead(scene.Channels(None, 0.0))
sel_mode = lx.eval1('query layerservice selmode ?')

if avgnormal:
    wp_fitted = lx.eval1('workPlane.state ?')
    if not wp_fitted:
        lx.eval('workPlane.fitSelect')

# Try to set Vertex selection
if sel_mode == 'edge' or sel_mode == 'polygon':
    lx.eval('select.convert vertex')

elif sel_mode == 'item':
    lx.eval('!!select.typeFrom vertex')
    lx.eval('select.all')

else:
    try:
        lx.eval('select.convert vertex')
    except Exception as e:
        print("--- Selection Error : Please select vertex|edge|polygon|item|material ---\n", e)
        sys.exit()


# make sure layer is selected, not just active
layer_index = lx.eval('query layerservice layers ? selected')
layer_ID = lx.eval1('query layerservice layer.ID ? {%s}' % layer_index)
lx.eval('select.subItem {%s} set' % layer_ID)
mesh = scene.selectedByType("mesh")[0]


# check for visibility
mesh_vis = mesh.channel("visible").get()
if mesh_vis == "off" or "allOff":
    mesh.channel("visible").set("default")

if not avgnormal:
    # Calculate center of selected verts and center
    sel_verts = lx.evalN('query layerservice verts ? selected')

    if not sel_verts:
        lx.eval('select.all')

    selverts = mesh.geometry.vertices.selected
    for i in selverts:
        poslist.append(modo.Vector3(i.position))
    pos = fn_avgpos(poslist)

lx.eval('select.drop vertex')


# set rot & pos
lx.eval('select.center {%s} set' % layer_ID)

if avgnormal:
    lx.eval('center.matchWorkplanePos')
    if invert:
        lx.eval('workPlane.rotate 0 180.0')
    lx.eval('center.matchWorkplaneRot')

else:
    lx.eval('center.setPosition {%s} {%s} {%s}' % (pos[0], pos[1], pos[2]))

lx.eval('select.item {%s}' % layer_ID)


# Wrap up, set transform tool
lx.eval('tool.set TransformMoveItem on')

if avgnormal:
    lx.eval('tool.set actr.local on')
    lx.eval('workPlane.reset')

else:
    lx.eval('tool.set actr.auto on')
