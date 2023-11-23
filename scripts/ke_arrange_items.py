# python

# Arrange Items 1.1 Kjell Emanuelsson 2019-21
# 1.1 - Python3
# Line up selected items using the gui options set in the kit.

import modo
import lx
from math import ceil

# Center handling
use_item_center = False
# BBox modes : Temporarily place center to selected bbox point
use_bbox_corner = False
use_bbox_center = False
use_bbox_ground = False
# Set new center pos
new_center = False
new_corner = False
new_ground = False

instance_mode = False
bbox_axislen = 1.0
pos = modo.Vector3()
bb_points = []
cpos = modo.Vector3()
wp_pos = modo.Vector3()
wp_rot = modo.Matrix3()

verbose = True
if verbose:
    print("==================== Arrange Items =========================")

# =================================================================================
# UserValue checks
# =================================================================================

# Axis and perpendicular axis (for rows)
row = 0.0  # starting at origo
row_spacing = []  # storing largest bbox for row spacing
item_count = 0
new_row = 0.0

axis = int(lx.eval('user.value ke_arrange_items.axis ?'))

if axis == 0:
    row_axis = 2
else:
    row_axis = 0

if lx.eval('user.value ke_arrange_items.neg ?') == "on": neg = True
else: neg = False

lencap = float(lx.eval('user.value ke_arrange_items.length ?'))
rowcap = int(lx.eval('user.value ke_arrange_items.row ?'))
grid = float(lx.eval('user.value ke_arrange_items.grid ?'))

if lx.eval('user.value ke_arrange_items.rot ?') == "on": no_rot = True
else: no_rot = False

centermode = lx.eval('user.value ke_arrange_items.center ?')
if centermode == "bbcorner":
    use_bbox_corner = True
elif centermode == "itemcenter":
    use_item_center = True
elif centermode == "bbcenter":
    use_bbox_center = True
elif centermode == "bbground":
    use_bbox_ground = True
elif centermode == "newcenter":
    new_center = True
elif centermode == "newground":
    new_ground = True
elif centermode == "newcorner":
    new_corner = True
else:
    use_item_center = True

if verbose:
    print("Axis, Lencap, Rowcap, Grid, Centermode, Rot: ", axis, lencap, rowcap, grid, centermode, no_rot)
    print("--------------------------------------------------")


# Funcs ===========================================================================
def getaxispoints(bbx, item_matrix):
    bb1 = modo.Vector3(bbx[0])
    bb2 = modo.Vector3(bbx[1])
    bb1.mulByMatrixAsPoint(item_matrix)
    bb2.mulByMatrixAsPoint(item_matrix)
    return bb1, bb2


def msg_selection_error():
    print("Invalid selection? - Aborting script.")
    modo.dialogs.alert(title="Selection Error", message=" Invalid Selection? ")


# =================================================================================
# Scene check / setup
# =================================================================================
scene = modo.scene.current()
chan_read = lx.object.ChannelRead(scene.Channels(None, 0.0))

# Symmetry check
if lx.eval('symmetry.state ?'):
    symmetry_mode = True
    lx.eval('select.symmetryState 0')
else:
    symmetry_mode = False

# Workplane check
if lx.eval1('workPlane.state ?'):
    wp_pos = scene.WorkPlanePosition(chan_read)
    wprot = scene.WorkPlaneRotation(chan_read)
    wp_rot = modo.Matrix3(wprot)
    wp_rot = wp_rot.asEuler(degrees=True, order='zxy')
    lx.eval('workPlane.reset')
    wp_mode = True
else:
    wp_mode = False


# =================================================================================
# Process Selection
# =================================================================================
selection = list(scene.selectedByType('mesh')) + list(scene.selectedByType('meshInst')) + \
      list(scene.selectedByType('groupLocator'))

if not selection: msg_selection_error()

# Nuking rotations - just not worth the hassle
if not no_rot: lx.eval('transform.reset rotation')

# Get item & Bounding Box info
for item in selection:

    if item.type == "mesh":
        matrix = modo.Matrix4(item.channel('worldMatrix').get())
        bb = item.geometry.boundingBox
        bb_points = getaxispoints(bb, matrix)

    elif item.type == "meshInst":
        inst_src = item.itemGraph(graphType='source').forward()[0]
        matrix = modo.Matrix4(item.channel('worldMatrix').get())
        bb = inst_src.geometry.boundingBox
        bb_points = getaxispoints(bb, matrix)
        instance_mode = True

    elif item.type == "groupLocator":
        bbox = []
        group_mesh = list(item.children(recursive=True, itemType="mesh"))
        group_inst = list(item.children(recursive=True, itemType="meshInst"))

        if group_inst:
            for inst in group_inst:
                inst_src = inst.itemGraph(graphType='source').forward()[0]
                matrix = modo.Matrix4(inst.channel('worldMatrix').get())
                bb = inst_src.geometry.boundingBox
                bb_points = getaxispoints(bb, matrix)
                bbox.extend(bb_points)

        if group_mesh:
            for mesh in group_mesh:
                matrix = modo.Matrix4(mesh.channel('worldMatrix').get())
                bb = mesh.geometry.boundingBox
                bb_points = getaxispoints(bb, matrix)
                bbox.extend(bb_points)

        bb_points = bbox

        if verbose:
            print("Group Item:", item, "  Group Children:", len(group_mesh) + len(group_inst))

    # ----------------------------------------------------------------------------------------------------
    # Center placement
    # ----------------------------------------------------------------------------------------------------
    # Making sure bbox is correctly sorted...
    bbox_x = sorted(bb_points, key=lambda e: e[0])
    bbox_y = sorted(bb_points, key=lambda e: e[1])
    bbox_z = sorted(bb_points, key=lambda e: e[2])
    bbox_cen = (bbox_x[0][0], bbox_y[0][1], bbox_z[0][2]), (bbox_x[-1][0], bbox_y[-1][1], bbox_z[-1][2])

    if use_bbox_corner or new_corner:
        cpos = bbox_cen[0]
    elif use_bbox_center or new_center:
        v1, v2 = (modo.Vector3(v) for v in bbox_cen)
        cpos = v1.lerp(v2, 0.5)
    elif use_bbox_ground or new_ground:
        v1, v2 = (modo.Vector3(v) for v in bbox_cen)
        cpos = v1.lerp(v2, 0.5)
        cpos[1] = bbox_cen[0][1]
    elif use_item_center:
        pass  # using pos from previous loop / starting with origo
    else:
        msg_selection_error()

    # storing row_axis values for largest bbox
    row_spacing.append(ceil(bbox_cen[1][row_axis] - bbox_cen[0][row_axis]))
    item_count += 1

    if rowcap and item_count > rowcap or lencap and pos[axis] > lencap:
        pos[axis] = 0.0
        new_row = ceil(sorted(row_spacing)[-1] * 2)
        pos[row_axis] = row + new_row
        row += new_row
        item_count = 1

    # Setting new center pos / locator
    locator = modo.LocatorSuperType(item)

    if new_corner or new_center or new_ground and not instance_mode:
        lx.eval('select.center {%s}' % locator.id)
        lx.eval('center.setPosition {%s} {%s} {%s} mode:world' % (cpos[0], cpos[1], cpos[2]))

    locator_pos = modo.Vector3(locator.position.get())

    # Compensate for pos offset
    if not use_item_center:
        bbox_center = modo.Vector3(cpos)
        offset = bbox_center - locator_pos
        pos -= offset

    locator.position.set(pos)

    # ----------------------------------
    # Prepare position for next item
    # ----------------------------------
    bbox_width = bb_points[-1][axis] - bb_points[0][axis]

    if not grid:
        if use_item_center:
            bkp_pos = pos[axis] + (bbox_cen[-1][axis] - locator_pos[axis])
        else:
            bkp_pos = pos[axis] + (bbox_cen[-1][axis] - locator_pos[axis])
    else:
        bkp_pos = ceil(pos[axis] + (bbox_cen[-1][axis] - locator_pos[axis]))

    pos = modo.Vector3(0.0, 0.0, 0.0)
    pos[row_axis] = row
    pos[axis] += abs(bkp_pos + grid)

    if verbose:
        print("Item:", item)
        print("BB width: ", bbox_width, "   BBox: ", bbox_cen)
        print("AxisBkpPos:", bkp_pos, " Row Pos: ", row, " Row Spacing: ", row_spacing)
        print("--------------------------------------------------")

# ----------------------------------------------------------------------------------------------------
# Cleanup & Finish
# ----------------------------------------------------------------------------------------------------
if new_center or new_corner or new_ground:
    lx.eval('select.type item')

if wp_mode:
    lx.eval('workplane.edit %s %s %s %s %s %s' % (wp_pos[0], wp_pos[1], wp_pos[2], wp_rot[0], wp_rot[1], wp_rot[2]))

if symmetry_mode:
    lx.eval('select.symmetryState 1')
