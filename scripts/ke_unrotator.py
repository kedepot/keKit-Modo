# python

# UNROTATOR 1.6 - Kjell Emanuelsson 2021
#
# Script to place geometry + items onto other geometry, or, just unrotate selected geo.
# (Inspired by the classic "rotate to or unrotate" script by seneca menard)
# When you point at the connected mesh (or to "space") the script Unrotates connected element selection, 
# using the selection geo as vectors to "straighten" it, OR, 
# Places connected geo on OTHER mesh surfaces you point to. OR, where an active Workplane is fitted, if any.
#
# Poly mode: First face is the new "bottom" used for vector calc. Add more to include unconnected geo.
#
# Edge/Vert mode: Have at least three verts. Use poly mode to add unconnected geo.
#                 Be sure to be in edge/vert mode for those to be used as bottom.
#                 (Also make sure to *not* have polys selected in vert/edge mode if you *dont* want them included)
#
# Item mode: Unrotates simply resets item rotation. Place by pointing at other mesh surface. 
#
# Optional modes:  Duplicate/Instance - Duplicates selection (items) when placing.
#                  Symmetry: Applies simple world mirror operation.
#                  (It checks for VISIBLE (hidden =/= invisible!) items at the mirror position. jfyi.)
#
# Additional Arguments:   wp      - Sets Workplane to the target selection (when placing)
#                         center  - Places geo at the center of the target element (face).
#                         flip    - Will invert placement (if the surface placement is inverted for some reason)
#
# Updates:  1.6  - Python3 & fixes
#           1.5  - Fixed center mode...
#           1.4  - Using mesh normals for both geo and item placement again...dont know why i didnt...
#           1.35 - Added "center" argument which places geo at the center of the target element (face).
#           1.3  - Selected element(s) only option added + more flipping improvements ;)
#           1.24 - Visibility issue fix (makes layer visible)  and "nothing selected" aborts script fixes.
#           1.23 - Improved normal check - should need the "flip" command at lot less, if at all! (prob not...)
#           1.2  - Bugfixing
#           1.21 - Quick fix for open border edge selections to reduce need of flip command.
#                  This will auto-flip when vert in edge selection is part of an open border (like a no-cap cylinder)

import sys
import math
import modo
import lx


u_args = lx.args()

verbose = False
unrotate = False
mouseoveritem = []
element_mode = False
item_mode = False
wp_fitted = False
symmetry_mode = False
symmetry_axis = 0
selected_only = False
place = False
dupe = False
instance = False
wp = False
flip = False
border_edges = False
center = False
all_verts = []
hit_rot = modo.Matrix3()
hit_pos = modo.Vector3()
wp_rot = modo.Matrix3()
first_sel = []
rem_list = []
og_verts = []
parent = []

for i in range(len(u_args)):
    if "dupe" in u_args:
        dupe = True
    elif "instance" in u_args:
        instance = True
    if "wp" in u_args:
        wp = True
    if "flip" in u_args:
        flip = True
    if "selonly" in u_args:
        selected_only = True
    if "center" in u_args:
        center = True

if verbose:
    print("------------- Unrotator Output --------------")
    print("User Arguments:", u_args)


def avgpos(poslist):
    vx, vy, vz = [], [], []
    for vi in poslist:
        vx.append(vi[0]), vy.append(vi[1]), vz.append(vi[2])
    total = len(poslist)
    return sum(vx) / total, sum(vy) / total, sum(vz) / total


def vector_rotation(d_vec=modo.Vector3(1, 0, 0), inv=False):
    d_vec.normalize()
    up_vec = modo.Vector3(0, 1, 0)

    if d_vec.dot(up_vec) <= 0.0: up_vec = modo.Vector3(1, 0, 0)

    n_vec = d_vec.cross(up_vec).normal()
    up_vec = n_vec.cross(d_vec).normal()
    matrix = modo.Matrix4((n_vec.values, d_vec.values, up_vec.values))

    if inv:
        align_matrix = modo.Matrix4.fromEuler((0, math.radians(180.0), 0))
        matrix = align_matrix * matrix
        return matrix.asEuler(degrees=True, order='zxy')
    else:
        return matrix.asEuler(degrees=True, order='yxz')


def tri_geo_unrotate(v3poslist):
    p1, p2, p3 = v3poslist[0], v3poslist[1], v3poslist[2]
    v_1 = p2 - p1
    v_2 = p3 - p1
    n_v = v_1.cross(v_2).normal()

    # check flip
    check = vertnormals_avg.dot(n_v)
    if check > 0:
        n_v = n_v.__mul__(-1)
        if verbose: print("Flipping the normal")

    if flip or border_edges: n_v = n_v.__mul__(-1)

    if verbose: print("Flip mode:", flip, " Normal Check:", check)

    u_v = n_v.cross(v_1).normal()
    d_v = n_v.cross(u_v).normal()

    matrix = modo.Matrix4((d_v.values, n_v.values, u_v.values))

    if not selected_only or border_edges:
        matrix.invert()

    return matrix.asEuler(degrees=True, order='yxz')



def avg_normal(vnormals_list):
    avg_vector = [0,0,0]
    for x, y, z in vnormals_list:
        avg_vector[0] += x
        avg_vector[1] += y
        avg_vector[2] += z
    return [vec / len(vnormals_list) for vec in avg_vector]


def desymmetrize(index_list, axis=0):
    remove_list = []
    sym_pos = []

    for index in index_list:
        vpos = lx.evalN('query layerservice vert.wdefpos ? %s' % index)
        sym_pos.append(vpos)

    if not invert_sym:
        for index, vpos in zip(index_list, sym_pos):
                if vpos[axis] <= 0:
                    remove_list.append(index)
                    index_list.remove(index)
    else:
        for index, vpos in zip(index_list, sym_pos):
                if vpos[axis] > 0:
                    remove_list.append(index)
                    index_list.remove(index)

    for ri in remove_list:
        lx.eval("select.element %s %s remove %s" % (sel_layer, 'vertex', ri))

    return index_list, remove_list


def compare_pos(pos1, pos2, axis):
    pos1, pos2 = list(pos1), list(pos2)
    pos2[axis] = pos2[axis] * -1
    if round(pos1[0], 4) == round(pos2[0], 4) and \
       round(pos1[1], 4) == round(pos2[1], 4) and \
       round(pos1[2], 4) == round(pos2[2], 4):
        return True
    else: return False


# Initial scene
scene = modo.scene.current()
chan_read = lx.object.ChannelRead(scene.Channels(None, 0.0))
sel_mode = lx.eval('query layerservice selmode ?')


# --------------------------------------------------------------------
# Mouse Hit pos/normals & Workplane check
# --------------------------------------------------------------------

wp_fitted = lx.eval1('workPlane.state ?')

if not wp_fitted:
    hit_normal = lx.eval('query view3dservice mouse.hitNrm ?')
    hit_pos = lx.eval('query view3dservice mouse.hitPos ?')

    if hit_normal:
        if sel_mode == "item":
            hit_rot = vector_rotation(modo.Vector3(hit_normal), inv=True)
        else:
            hit_rot = vector_rotation(modo.Vector3(hit_normal))
    else:
        hit_rot = None

    if verbose: print("Hit Rot, Pos: ", hit_rot, hit_pos, hit_normal)

if wp_fitted:
    hit_pos = scene.WorkPlanePosition(chan_read)
    wp_rot = scene.WorkPlaneRotation(chan_read)
    hit_rot = modo.Matrix3(wp_rot)
    if sel_mode == "item":
        hit_rot = hit_rot.asEuler(degrees=True, order='zxy')
    else:
        hit_rot = hit_rot.asEuler(degrees=True, order='yxz')
    place = True
    lx.eval('workPlane.reset')


# --------------------------------------------------------------------
# Symmetry check
# --------------------------------------------------------------------

if lx.eval('symmetry.state ?'):
    if selected_only: sys.exit(": Symmetry not supported for selected_only - currently.")
    if wp_fitted: sys.exit(":Reason:     Symmetry not supported when workplane is active.")
    symmetry_mode = True
    symmetry_axis = lx.eval('symmetry.axis ?')
    lx.eval('select.symmetryState 0')
    if verbose: print("Symmetry:", symmetry_mode, "  Axis:", symmetry_axis)

# --------------------------------------------------------------------
# Layer & Item Mode Selections
# --------------------------------------------------------------------

sel_mesh = []
check_child = []
orphaned = False
# parent = False

dupe_sym_check = []
rem_item = []

sel_items = list(scene.selectedByType("mesh")) + list(scene.selectedByType("meshInst"))
sel_item_count = len(sel_items)

if sel_mode == 'item':

    if sel_item_count > 1:
        sys.exit(":Reason:   Multiple active source layers not supported.")

    for item in sel_items:
        item_type = item.type

        if item_type == 'mesh':
            sel_mesh = item
            break
        elif item_type == 'meshInst':
            sel_mesh = item
            break

    if sel_mesh:
        item_mode = True

        # Check parents & Temp-Orphaning
        parents = sel_mesh.parents

        if parents:
            parent = parents[0]
            lx.eval('item.parent {%s} {%s} 0 inPlace:1' % (sel_mesh.id, "None"))
            orphaned = True
            if verbose: print("Parents:", parents, "	  Orphaned:", orphaned)

        # Checking for VISIBLE mirror position item
        if symmetry_mode:
            locator = modo.LocatorSuperType(sel_mesh)
            dupe_sym_check = locator.position.get()

            dupe_sym = []
            all_items = list(scene.items('meshInst')) + list(scene.items('mesh'))

            for i in all_items:  # invisible =/= hidden...
                if not chan_read.Integer(i, i.ChannelLookup(lx.symbol.sICHAN_LOCATOR_HVISIBLE)):
                    # if not lx.eval('query layerservice layer.visible ? %s' % locator.id) == 'none':  # not instances!
                    locator = modo.LocatorSuperType(i)
                    comp_pos = locator.position.get()
                    if compare_pos(comp_pos, dupe_sym_check, symmetry_axis) and i != sel_mesh:
                        dupe_sym.append(i)

            if len(dupe_sym) > 1:
                sys.exit(": Reason: Symmetry mode, found more than 1 (visible) item at mirror position.\n\
                     I dont know which one is valid - aborting.")
            else:
                if dupe or instance: rem_item = False
                else: rem_item = dupe_sym

            if verbose and dupe_sym:
                print("Duplicate-Symmetry item found. Removing it to make new dupe:", dupe_sym)

    else: sys.exit(":Reason:   Item not selected ?")


elif sel_mode == 'vertex' or sel_mode == "edge" or sel_mode == "polygon":

    if not sel_item_count:
        fg_check = lx.eval('query layerservice layers ? fg')

        if type(fg_check) == tuple:
            sys.exit(":Reason:   Multiple selected layers not supported.")

        if fg_check:
            sel_id = lx.eval('query layerservice layer.id ? {%s}' % fg_check)
            lx.eval('select.item {%s} set' % sel_id )
            sel_mesh = scene.selected[0]

    elif sel_item_count == 1:

        for item in sel_items:
            item_type = item.type

            if item_type == 'mesh':
                sel_mesh = item
                break

    else: sys.exit(":Reason:   Multiple active source layers not supported.")

    if sel_mesh:
        element_mode = True
        if instance:
            instance = False
            dupe = True

    else: sys.exit(":Reason:   Item selection failed.")

else: sys.exit(":Reason:   Not in ELEMENT or ITEM mode?")


# Set selected item layer & Matrix
sel_matrix = modo.Matrix4(sel_mesh.channel('worldMatrix').get())
sel_layer = lx.eval('query layerservice layers ? selected')

# check for visibility
mesh_vis = sel_mesh.channel("visible").get()
if mesh_vis == "off" or "allOff":
    sel_mesh.channel("visible").set("default")

if verbose:
    print("Dupe, Instance:", dupe, instance)
    print("Element Mode:", element_mode, "\nItem Mode:", item_mode)
    print("Selected Source Item:", sel_mesh)
    print("Sel Matrix:", sel_matrix)

# --------------------------------------------------------------------
# Element Mode Selection checks
# --------------------------------------------------------------------

if element_mode:

    rem_list = []
    sel_verts = []
    first_sel = []

    lx.eval('select.type {%s}' % sel_mode)

    # Grab vertex converted initial selection ------------------------

    if sel_mode == "edge":

        selected_edges = lx.evalN('query layerservice edges ? selected')

        if selected_edges:

            lx.eval('select.convert vertex')
            first_sel = lx.evalN('query layerservice verts ? selected')
            lx.eval('select.drop vertex')

            # Border Edge Check - Just flipping the normal seems to work fine most cases ;)
            for i in selected_edges:
                edge_polys = lx.eval('query layerservice edge.polyList ? {%s}' % i)
                if type(edge_polys) == int:
                    border_edges = True
                    print("Boundary Edge(s) Selected, Flipping Normal")
                    break


            for i in first_sel:
                lx.eval("select.element %s %s add %s 0 0" % (sel_layer, 'vertex', i))

            first_sel = [int(i) for i in first_sel]

        else: sys.exit(":Reason: Edge-selection mode, but no edges selected? ")


    elif sel_mode == "vertex":
        first_sel = lx.evalN('query layerservice verts ? selected')
        if not first_sel:
            sys.exit(": Nothing selected - Aborting script.")
        first_sel = [int(i) for i in first_sel]


    elif sel_mode == "polygon":
        first_sel = lx.evalN('query layerservice polys ? selected')
        if not first_sel:
            sys.exit(": Nothing selected - Aborting script.")
        first_sel = lx.eval('query layerservice poly.vertList ? %s' % first_sel[0])
        first_sel = [int(i) for i in first_sel]
        lx.eval('select.convert vertex')


    if symmetry_mode and first_sel:
        invert_sym = False
        # Check if first sel sym is neg, then turn to pos
        if lx.eval('query layerservice vert.wdefpos ? %s' % first_sel[0])[symmetry_axis] <= 0 :
            invert_sym = True

        first_sel, rem_list = desymmetrize(first_sel, axis=symmetry_axis)
        if verbose: print("Element Sym-Rem list:", rem_list)

    og_verts = first_sel  # variant stored for re-select

    if len(first_sel) > 4:  # Getting better (& valid?) angles on larger selections
        first_sel.sort(reverse=True)
        first_sel = first_sel[0], first_sel[int(len(first_sel) * .33)], first_sel[int(len(first_sel) * .66)]

    # get all connected verts ---------------------------------------------
    if not selected_only:
        pcheck = lx.evalN('query layerservice polys ? selected')

        if pcheck:
            poly_verts = []
            for i in pcheck:
                pv = lx.eval('query layerservice poly.vertList ? %s' % i)
                pv = [int(i) for i in pv]
                poly_verts.extend(pv)

            poly_verts = list(set(poly_verts))

            if symmetry_mode and poly_verts:
                poly_verts, rem_list_ap = desymmetrize(poly_verts, axis=symmetry_axis)
                rem_list += rem_list_ap

            for i in poly_verts:
                lx.eval("select.element %s %s add %s 0 0" % (sel_layer, 'vertex', i))

        if len(first_sel) < 3:
            sys.exit(":Reason: Less than 3 vertices found.")

        lx.eval('select.connect')
        all_verts = lx.evalN('query layerservice verts ? selected')
        all_verts = [int(i) for i in all_verts]
    else: all_verts = first_sel

    if verbose:
        print("First Selection:", len(first_sel), first_sel)


# --------------------------------------------------------------------
# Check if mouse is over another mesh item
# --------------------------------------------------------------------

if not wp_fitted:

    lx.eval('select.type item')
    target_mesh = []

    try:
        lx.eval('select.3DElementUnderMouse add')
        target_mesh = scene.selected[-1]
    except:
        pass

    if target_mesh:

        if sel_mesh == target_mesh:
            unrotate = True
            if sel_mode == "item":
                place = False
                dupe = False
                instance = False

        elif target_mesh != sel_mesh:
            place = True

        if sel_mode != "item":
            check_target = target_mesh.type

            if check_target == "mesh":
                # if target_mesh:  # Using wp to get target poly rotation -------- WHY?! just using mouse pos...
                lx.eval('select.type polygon')
                lx.eval1('query layerservice layer.index ? %s' % target_mesh.id)

                try:
                    lx.eval('select.3DElementUnderMouse set')
                except:
                    sys.exit(":Reason: Miss! Could not find suitable POLY under mouse pointer.")

                hit_normal = lx.eval('query view3dservice mouse.hitNrm ?')
                hit_pos = lx.eval('query view3dservice mouse.hitPos ?')

                if hit_normal:
                    hit_rot = vector_rotation(modo.Vector3(hit_normal))
                else:
                    hit_rot = None
                    unrotate = True

                if center:
                    lx.eval('workPlane.fitSelect')
                    hit_pos = scene.WorkPlanePosition(chan_read)
                    wp_rot = scene.WorkPlaneRotation(chan_read)
                    hit_rot = modo.Matrix3(wp_rot).asEuler(degrees=True, order='yxz')
                    lx.eval('workPlane.reset')

                # DblCheck unrotating or placing inside the same mesh layer -------
                if not place:
                    new_sel = lx.evalN('query layerservice polys ? selected')
                    new_verts_index = lx.eval('query layerservice poly.vertList ? {%s}' % new_sel[0])

                    if any(v in new_verts_index for v in all_verts):
                        unrotate = True
                        place = False
                        dupe = False
                        instance = False
                    else:
                        place = True
                        unrotate = False

                lx.eval('select.drop polygon')

            elif check_target == "meshInst": pass

        elif sel_mode == "item":

            if center:  # what a mess! ;D
                lx.eval('select.type polygon')
                lx.eval1('query layerservice layer.index ? %s' % target_mesh.id)
                hit_normal = lx.eval('query view3dservice mouse.hitNrm ?')
                # hit_pos = lx.eval('query view3dservice mouse.hitPos ?')

                if hit_normal:
                    hit_rot = vector_rotation(modo.Vector3(hit_normal))
                else:
                    hit_rot = None
                    unrotate = True
                try:
                    lx.eval('select.3DElementUnderMouse set')
                except:
                    sys.exit(":Reason: Miss! Could not find suitable POLY under mouse pointer.")

                lx.eval('workPlane.fitSelect')
                hit_pos = scene.WorkPlanePosition(chan_read)
                wp_rot = scene.WorkPlaneRotation(chan_read)
                hit_rot = modo.Matrix3(wp_rot).asEuler(degrees=True)
                lx.eval('workPlane.reset')

                lx.eval('select.type item')

            else:
                hit_normal = lx.eval('query view3dservice mouse.hitNrm ?')
                hit_pos = lx.eval('query view3dservice mouse.hitPos ?')
                if hit_normal:
                    hit_rot = vector_rotation(modo.Vector3(hit_normal), inv=True)
                else:
                    hit_rot = None
                    unrotate = True

        else: sys.exit(": Reason:  Invalid item type under mouse? (mesh/meshInst only)")

    else:
        target_mesh = sel_mesh
        unrotate = True
        place = False
        dupe = False
        instance = False

    if target_mesh != sel_mesh:
        lx.eval('select.item {%s} set' % sel_mesh.id)
    lx.eval1('query layerservice layer.index ? %s' % sel_mesh.id)

    if verbose:
        print("Unrotating: ", unrotate, "\nPlacing: ", place)
        print("Selected Target Item: ", target_mesh)
        print("Hit Rot: ", hit_rot, "  Hit Pos: ", hit_pos)

# #########################################################################
# MAIN OPs
# #########################################################################

# --------------------------------------------------------------------
# Item Mode
# --------------------------------------------------------------------

if item_mode:

    if rem_item:
        scene.removeItems(rem_item)

    if dupe:
        place_mesh = scene.duplicateItem(sel_mesh, instance=False)
        sel_mesh = place_mesh
        scene.select(sel_mesh)

    elif instance:
        place_mesh = scene.duplicateItem(sel_mesh, instance=True)
        sel_mesh = place_mesh
        scene.select(sel_mesh)

    if unrotate:
        lx.eval('transform.reset rotation')

    elif place:
        locator = modo.LocatorSuperType(sel_mesh)
        locator.position.set(hit_pos)
        locator.rotation.set(hit_rot, degrees=True)

# --------------------------------------------------------------------
# Element Mode
# --------------------------------------------------------------------

elif element_mode:

    lx.eval('select.type vertex')

    # Getting positions & vertex normals from first selection verts -------------------
    sel_verts_pos = []
    vnormals = []

    for v in first_sel:
        vnormals.append(lx.eval('query layerservice vert.normal ? %s' % v))
        conv_pos = modo.Vector3(lx.eval('query layerservice vert.wdefpos ? %s' % v))
        sel_verts_pos.append(conv_pos)

    vertnormals_avg = modo.Vector3(avg_normal(vnormals))

    # if place:
    #     hit_vec = modo.Vector3(hit_normal)
    #     print "HIT VEC", vertnormals_avg.dot(hit_vec)
    #     if verbose:
    #         print "Averaged vert normal: ", vertnormals_avg

    # Fit wp to get avg center pos of selection. Faster?
    lx.eval('workPlane.fitSelect')
    pos = scene.WorkPlanePosition(chan_read)
    lx.eval('workPlane.reset')

    # --------------------------------------------------------------------
    # Duplicate (If set) Note: Not actually using the new geo ;)
    # --------------------------------------------------------------------

    if dupe:
        lx.eval('select.convert polygon')
        lx.eval('select.copy')
        lx.eval('select.paste')
        lx.eval('select.drop polygon')
        lx.eval('select.type vertex')

    # --------------------------------------------------------------------
    # Main operation (QND, slow and ineffective, but hey...)
    # --------------------------------------------------------------------

    unrot = tri_geo_unrotate(sel_verts_pos)

    # Using xfrm is way faster than TD mesh edit on thousands of verts?
    lx.eval('tool.set actr.auto on')
    lx.eval('tool.set xfrm.rotate on')
    lx.eval('tool.reset')
    # rot Y
    lx.eval('tool.setAttr axis.auto axisY 1')
    lx.eval('tool.setAttr axis.auto axis 1')
    lx.eval('tool.setAttr xfrm.rotate angle {%s}' % unrot[1])
    lx.eval('tool.doApply')
    # rot X
    lx.eval('tool.setAttr axis.auto axisX 1')
    lx.eval('tool.setAttr axis.auto axis 0')
    lx.eval('tool.setAttr xfrm.rotate angle {%s}' % unrot[0])
    lx.eval('tool.doApply')
    # rot Z
    lx.eval('tool.setAttr axis.auto axisZ 1')
    lx.eval('tool.setAttr axis.auto axis 2')
    lx.eval('tool.setAttr xfrm.rotate angle {%s}' % unrot[2])
    lx.eval('tool.doApply')

    lx.eval('tool.set xfrm.rotate off')
    lx.eval('tool.set actr.auto off')


    if unrotate:
        # .. and then just wp center pos to center
        lx.eval('workPlane.edit {%s} {%s} {%s}' % (pos[0], pos[1], pos[2]))
        lx.eval('vert.center all')
        lx.eval('workPlane.reset')

    elif place:

        # Lame offset calc
        lx.eval('workPlane.fitSelect')
        chan_read = lx.object.ChannelRead(scene.Channels(None, 0.0))
        c_offset_pos = scene.WorkPlanePosition(chan_read)
        lx.eval('workPlane.reset')

        sel_verts_pos = []
        conv_pos = []
        for v in first_sel:
            sel_verts_pos.append(lx.eval('query layerservice vert.wdefpos ? %s' % v))

        bottom_pos = avgpos(sel_verts_pos)

        offset_X = c_offset_pos[0] - bottom_pos[0]
        offset_Y = c_offset_pos[1] - bottom_pos[1]
        offset_Z = c_offset_pos[2] - bottom_pos[2]

        # Rotation operation again (sigh) to align to target
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

        # And then center
        lx.eval('workPlane.edit {%s} {%s} {%s} {%s} {%s} {%s}' %
                (hit_pos[0], hit_pos[1], hit_pos[2], hit_rot[0], hit_rot[1], hit_rot[2]))
        lx.eval('vert.center all')

        # and again (sigh) with QnD offset fix using verts workplane relative position...
        lx.eval('workPlane.offset 0 {%s}' % offset_X)
        lx.eval('workPlane.offset 1 {%s}' % offset_Y)
        lx.eval('workPlane.offset 2 {%s}' % offset_Z)
        lx.eval('vert.center all')

else:
    sys.exit(": Unknown Error - Not in ELEMENT or ITEM mode?")

lx.eval('workPlane.reset')


# --------------------------------------------------------------------
# Mirror op for symmetry
# --------------------------------------------------------------------
if symmetry_mode:

    if element_mode:
        lx.eval('select.convert polygon')

    if instance:
        lx.eval('tool.set "Instance Mirror" on')
    else:
        lx.eval('tool.set *.mirror on')

    lx.eval('tool.reset')

    if item_mode and not instance:
        lx.eval('tool.attr effector.item instance false')
    elif item_mode and instance:
        lx.eval('tool.attr effector.item instance true')

    lx.eval('tool.attr gen.mirror cenX 0.0')
    lx.eval('tool.attr gen.mirror cenY 0.0')
    lx.eval('tool.attr gen.mirror cenZ 0.0')
    lx.eval('tool.attr gen.mirror angle 0.0')

    if element_mode:
        lx.eval('tool.attr effector.clone flip true')
    elif item_mode:
        lx.eval('tool.attr effector.item source active')

    lx.eval('tool.attr gen.mirror frot axis')
    lx.eval('tool.attr gen.mirror axis %s' % symmetry_axis)
    lx.eval('tool.apply')

    if instance:
        lx.eval('tool.set "Instance Mirror" off')
    else:
        lx.eval('tool.set *.mirror off')

    if element_mode and rem_list:  # prep old mirror geo in poly for delete after reselect
        lx.eval('select.drop polygon')
        lx.eval('select.type vertex')
        lx.eval('select.drop vertex')
        for i in rem_list:
            lx.eval("select.element %s %s add %s" % (sel_layer, 'vertex', i))
        lx.eval('select.connect')
        lx.eval('select.convert polygon')

    # Restore symmetry
    lx.eval('select.symmetryState 1')
    lx.eval('symmetry.axis %s' % symmetry_axis)


# --------------------------------------------------------------------
# Reselect original selection
# --------------------------------------------------------------------
if element_mode:
    # if not dupe?
    lx.eval('select.type vertex')
    lx.eval('select.drop vertex')
    for i in og_verts:
        lx.eval("select.element %s %s add %s 0 0" % (sel_layer, 'vertex', i))

    if symmetry_mode:  # Re-select & Remove old mirror geo

        for i in og_verts:
            symv = lx.eval('query layerservice vert.symmetric ? {%s}' % i)
            lx.eval("select.element %s %s add %s 0 0" % (sel_layer, 'vertex', symv))

        if rem_list:
            if not dupe:
                lx.eval('select.type polygon')
                lx.eval('select.delete')
                lx.eval('select.type vertex')

    if sel_mode == "polygon":
        lx.eval('select.convert polygon')
        lx.eval('select.drop vertex')

    elif sel_mode == "edge":
        lx.eval('select.convert edge')
        lx.eval('select.drop vertex')

    lx.eval('select.type {%s}' % sel_mode)

if orphaned:
    lx.eval('item.parent {%s} {%s} 0 inPlace:1' % (sel_mesh.id, parent.id))
# else:
#     lx.eval('item.parent {%s} {%s} 0 inPlace:1' % (sel_mesh.id, item.id))


if wp_fitted:  # restore WP
    wp_rot = modo.Matrix3(wp_rot).asEuler(degrees=True, order='xyz')
    lx.eval('workPlane.edit {%s} {%s} {%s} {%s} {%s} {%s}' %
            (hit_pos[0], hit_pos[1], hit_pos[2], wp_rot[0], wp_rot[1], wp_rot[2]))

if wp and not wp_fitted:
    # wp_rot = modo.Matrix3(wp_rot).asEuler(degrees=True, order='xyz')
    lx.eval('workPlane.edit {%s} {%s} {%s} {%s} {%s} {%s}' %
            (hit_pos[0], hit_pos[1], hit_pos[2], hit_rot[0], hit_rot[1], hit_rot[2]))
