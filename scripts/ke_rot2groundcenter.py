#python

# Rot2GroundCenter 1.1 - Kjell Emanuelsson 2018-21
# 1.1 Python3
# Rotate to ground and center - "Bottom" determined from first selected poly (or pre-fitted Workplane). 
# - Select additional polys to be included. (Script will use select.connect, so no need select all connected polys.)
# - Option: Select one vert to offset centered placement (origo position)
# *** Make sure no verts are selected if you dont want this ***


# variables
offset = False
wp_fitted = False
verbose = False
pos = (0, 0, 0)
# ------------------------------------------------------------------------------------
# get layer and check if WP is fitted
# ------------------------------------------------------------------------------------
sel_layer = lx.eval('query layerservice layers ? selected')
layer_index = lx.eval1('query layerservice layer.index ? {%s}' % sel_layer)
layer_ID = lx.eval1('query layerservice layer.ID ? {%s}' % sel_layer)

if verbose:
    print("sel_layer :", sel_layer, "   layer index:", layer_index, "   layer ID:", layer_ID)

if lx.eval('workPlane.state ?'):
    wp_fitted = True


# ------------------------------------------------------------------------------------
# Check verts for offset position (1st vert)
# ------------------------------------------------------------------------------------
lx.eval('select.typeFrom vertex')
sel_verts = lx.evalN('query layerservice verts ? selected')
sel_check = len(sel_verts)

if sel_check > 0:
    pos = lx.eval('query layerservice vert.wdefpos ? %s' % sel_verts[0])
    offset = True


# ------------------------------------------------------------------------------------
# Check poly selections (First poly selected) for WP rotation and the rest for connecting 
# ------------------------------------------------------------------------------------	
lx.eval('select.typeFrom polygon')
first_polys = lx.evalN('query layerservice polys ? selected')

lx.eval('select.connect')
lx.eval('select.convert polygon')

sel_polys = lx.evalN('query layerservice polys ? selected')
lx.eval('select.drop polygon')


# ------------------------------------------------------------------------------------
# Fit WP to first selected poly for rotation
# ------------------------------------------------------------------------------------

lx.eval('select.element %s %s add %s' % (sel_layer, 'polygon', first_polys[0]))
if not wp_fitted:
    lx.eval('workPlane.fitSelect')

# First vert WP offset
if offset:
    lx.eval('workplane.edit %s %s %s' % (pos[0], pos[1], pos[2]))

lx.eval('workPlane.rotate 0 180.0')  # only semi-reliable Y-inverting...better method TBD


# ------------------------------------------------------------------------------------
# Create temp layer for center -> wp fitting and ...operate
# ------------------------------------------------------------------------------------

for i in sel_polys:
    lx.eval('select.element %s %s add %s' % (sel_layer, 'polygon', i))

lx.eval('select.cut')
lx.eval('layer.new')
lx.eval('select.paste')

lx.eval('query sceneservice scene.index ? current')
mesh_item = lx.evalN('query sceneservice selection ? mesh')[0]

lx.eval('select.center {%s}' % mesh_item)
lx.eval('center.matchWorkplanePos')
lx.eval('center.matchWorkplaneRot')

lx.eval('workPlane.reset')
lx.eval('select.typeFrom item')
lx.eval('transform.reset all')

lx.eval('select.typeFrom polygon')
lx.eval('select.copy')
lx.eval('select.typeFrom item')
lx.eval('delete')

lx.eval('select.subItem {%s} set' % layer_ID)
lx.eval('select.typeFrom polygon')
lx.eval('select.paste')
