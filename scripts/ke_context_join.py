# python
# ContextJoin 1.1 - Kjell Emanuelsson 2019
# 1.1 - added multilayer support

import lx
import modo

average = False
uvmerge = False
keepsingle = False

u_args = lx.args()
for arg in u_args:
    if arg == "average":
        average = True
    if arg == "uvmerge":
        uvmerge = True

scene = modo.scene.current()

sel_mode = lx.eval('query layerservice selmode ?')
fg_layers = lx.eval('query layerservice layers ? fg')

sel_layers = []
item_ids = []

if type(fg_layers) == int:
    sel_layers.append(fg_layers)
else:
    sel_layers = fg_layers

# ---------------------------------------------------------------------------------
# Process Selection
# ---------------------------------------------------------------------------------
for layer in sel_layers:

    layer_ID = lx.eval1('query layerservice layer.ID ? {%s}' % layer)
    item_ids.append(layer_ID)
    scene.select(layer_ID)

    if sel_mode == "vertex" and lx.evalN('query layerservice verts ? selected'):
        lx.eval('vert.join {%s} {%s} {%s}' % (average, keepsingle, uvmerge))

    elif sel_mode == "edge" and lx.evalN('query layerservice edges ? selected'):
        lx.eval('edge.join {%s} {%s} {%s}' % (average, keepsingle, uvmerge))

    elif sel_mode == "polygon" and lx.evalN('query layerservice polys ? selected'):
        # best in most cases vs vert join?
        lx.eval('edge.join {%s} {%s} {%s}' % (average, keepsingle, uvmerge))

# Actually select layers, not just fg
for item in item_ids:
    scene.select(item, add=True)
