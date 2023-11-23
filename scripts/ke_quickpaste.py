#python#

# QuickPaste 1.2 - Kjell Emanuelsson 2018-21
# 1.2 - Python3 and fixes
# Update: 1.1 - (Some) Speed improvment rewrite (No longer uses Paste Tool), removed "fit" option.
#
# Select POLYS to copy and point your mouse at intended target poly to align to.
#   Source polys should be oriented "straight up" in Y axis. (or expect them to be handled as such)
# 	1. Select polys. 2. Mouse over mesh element to align to.
#
# 	WP option:       Fit workplane beforehand for destination. Also, for manual placement control, edges and what not?)
#                 	*Does not work with "target" argument*
#	Multiple layers: Paste to/on any layer
#	Sel-set:         Pasted elements are added to a selection set for quick access later.
#
#	Argument :  target  -  Will paste to the layer (under mouse) instead of source layer.

import lx
import modo
from math import ceil, radians

u_args = lx.args()

paste_to_target = False
dupe = False
wpfitted = False
verbose = False
target_mesh = None
hit_pos = modo.Vector3()
hit_rot = modo.Matrix3()

for i in range(len(u_args)):
    if "target" in u_args:
        paste_to_target = True
    else: pass


def fn_height(vertindices):
    posY = []
    for v in vertindices:
        posY.append(lx.eval('query layerservice vert.wdefpos ? %s' % v)[1])
    posY.sort()
    return posY[-1] - posY[0]


def vector_rotation(dVec=modo.Vector3(1, 0, 0), rotOrder='zxy', asDegrees=True):
    # Rotation from one vector/normal using Y up
    # **Inverted for Work plane use**
    dVec.normalize()
    upVec = modo.Vector3(0, 1, 0)

    # Check for parallell vectors
    if dVec.dot(upVec) < -0.99:
        upVec = modo.Vector3(1, 0, 0)

    nVec = dVec.cross(upVec).normal()
    upVec = nVec.cross(dVec).normal()
    matrix = modo.Matrix4((nVec.values, dVec.values, upVec.values))

    xAlignMatrix = modo.Matrix4.fromEuler((0, radians(180.0), 0))
    matrix = xAlignMatrix * matrix.inverted()

    return matrix.asEuler(degrees=asDegrees, order=rotOrder)


if verbose:
    print("------------------\n", "QuickPaste Output:")


# --------------------------------------------------------------------
# Check selections
# --------------------------------------------------------------------	
wp_fitted = lx.eval1('workPlane.state ?')
if wp_fitted and paste_to_target: paste_to_target = False

lx.eval('select.typeFrom polygon')

scene = modo.scene.current()


# Grabbing first mesh with poly selection (to not require active item selection)
og_mesh, vert_list, sel_poly, psel = [], [], [], []

for mesh in scene.meshes:
    psel = mesh.geometry.polygons.selected
    if len(psel) != 0:
        og_mesh = mesh
        break

if og_mesh: scene.select(og_mesh)
else: sys.exit(": --- Selection error: No polys selected ? ---")

if dupe:  # non-api large poly# iteration is slow,so...
    lx.eval('select.copy')
    temp_mesh = scene.addMesh()
    scene.select(temp_mesh)
    lx.eval('select.paste')
    sel_poly = temp_mesh.geometry.polygons.selected

else:
    sel_poly = psel
    temp_mesh = None


# Get height(y) offset for Paste Tool placement	
for p in sel_poly:
    for i in p.vertices:
        vert_list.append(i.index)

vert_list = set(vert_list)
y_offset = fn_height(vert_list) / 2
y_offset = ceil(y_offset * 1000.0) / 1000.0

if verbose:
    print("Polys:", len(sel_poly), sel_poly, "\nVerts:", len(vert_list), vert_list, "\nOffset:", y_offset)


# --------------------------------------------------------------------
# Get mouse over element for WP fitting / OR use existing fitted WP
# --------------------------------------------------------------------

if not wp_fitted:

    try:
        hit_normal = lx.eval('query view3dservice mouse.hitNrm ?')
        hit_pos = lx.eval('query view3dservice mouse.hitPos ?')
        if verbose: print("Hit normal:", hit_normal)
        hit_rot = vector_rotation(modo.Vector3(hit_normal))

    except Exception as e:
        sys.exit(": --- Could not find appropriate mesh layer under mouse. Aborting. ---\n", e)

    if paste_to_target:

        lx.eval('select.typeFrom item')
        try: lx.eval('select.3DElementUnderMouse set')
        except Exception as e:
            print(e)
            paste_to_target = False

        if paste_to_target:

            target_mesh = scene.selectedByType("mesh")[0]
            if target_mesh == og_mesh: paste_to_target = False
            if verbose: print("Target Mesh:", target_mesh)


if wp_fitted:

    chan_read = lx.object.ChannelRead(scene.Channels(None, 0.0))
    hit_pos = scene.WorkPlanePosition(chan_read)
    hit_rot = scene.WorkPlaneRotation(chan_read)
    hit_rot = modo.Matrix3(hit_rot)
    hit_rot = hit_rot.asEuler(degrees=True, order='yxz')

if verbose:
    print("hit pos,rot:", hit_pos, hit_rot, "\nPaste To Target:", paste_to_target)

# --------------------------------------------------------------------	
# Paste selection using paste tool
# --------------------------------------------------------------------

# Set WP for Paste Tool placement
if not wp_fitted:
    lx.eval('workplane.fitSelect')
    lx.eval('workplane.edit %s %s %s %s %s %s' %
            (hit_pos[0], hit_pos[1], hit_pos[2], hit_rot[0], hit_rot[1], hit_rot[2]))

lx.eval('workPlane.offset 1 {%s}' % y_offset)

if dupe:
    scene.select(temp_mesh)
    lx.eval('select.typeFrom polygon')
    lx.eval('select.all')

else: lx.eval('select.typeFrom polygon')

# Transform operation
# Using the "one axis at a time" method for rot for now
lx.eval('tool.set actr.auto on')
lx.eval('tool.set xfrm.rotate on')
lx.eval('tool.reset')
# rot Y
lx.eval('tool.setAttr axis.auto axisY 1')
lx.eval('tool.setAttr axis.auto axis 1')
lx.eval('tool.setAttr xfrm.rotate angle {%s}' % hit_rot[1])
lx.eval('tool.doApply')
# rot X 
lx.eval('tool.setAttr axis.auto axisX 1')
lx.eval('tool.setAttr axis.auto axis 0')
lx.eval('tool.setAttr xfrm.rotate angle {%s}' % hit_rot[0])
lx.eval('tool.doApply')
# rot Z
lx.eval('tool.setAttr axis.auto axisZ 1')
lx.eval('tool.setAttr axis.auto axis 2')
lx.eval('tool.setAttr xfrm.rotate angle {%s}' % hit_rot[2])
lx.eval('tool.doApply')
lx.eval('tool.set xfrm.rotate off')
lx.eval('tool.set actr.auto off')

lx.eval('vert.center all')

if dupe:
    lx.eval('select.copy')
    if paste_to_target: scene.select(target_mesh)
    else: scene.select(og_mesh)
    lx.eval('select.paste')
    scene.removeItems(temp_mesh)


lx.eval('workPlane.reset')

# add to selset
lx.eval('select.editSet keQuickPastePolys add keQuickPastePolys')

if paste_to_target:
    scene.select(og_mesh)

# reselect og poly selection for further operations
og_mesh.geometry.polygons.select(psel, replace=True)

#eof	