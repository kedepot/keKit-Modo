# python

# ke_MouseMirror v2.2 - Kjell Emanuelsson 2018-2021
#
# Mirrors selected mesh (select edges or polys) towards mouse pointer locally - meaning next to the bounding box (on relevant axis, as indicated by axis gizmo down left) 
# Tip: dont place mouspoint *too* close to selection, pref a bit outside selection bbox. 
# Basic world axis symmetry support.
#
# Option: Fit workplane beforehand for custom angles. (mouse placement not important)
#
# Known issue: If you undo, the WP might be locked to preferred angle. reset wp to unlock.
# 2.2 : Python3 & fixes
# 2.1 : Added "merge" argument - merges touching verts & also mirrors UVs. Fixed some bugs & optimized element mode.
# 2.0 : Functionality change : In POLY MODE now only mirrors SELECTION. VERT or EDGE selection will CONNECT.
# 1.1 : "FIXED" - undo issue (still happens, but i check for it, so the script will work. Also, resulting mesh will be unselected.
# 1.2 : Added Mesh Item & Mesh Instance flip support! - Undo annoyance remain. (unfixable?)
#
# Argument: world  - Mirrors along world axis instead of locally.


import lx, modo

axis = 9  # NEIN / mousepos axis
xmax, ymax, zmax = True, True, True
maxpos = False
world = False
wpfitted = False
symmetry_mode = False
instance_mode = False
vertlist = []
vX, vY, vZ = [], [], []
vertpos = []
og_polys = []
og_poly_sel = []
symcheck = False
verbose = False
setFixed = False
selection = False
merge = False
world_mouse_pos = modo.Vector3()
cenX, cenY, cenZ = 0, 0, 0
symmetry_axis = 0
og_items = []

u_args = lx.args()

for i in range(len(u_args)):

    if "world" in u_args:
        world = True
    if "selection" in u_args:
        selection = True
    if "merge" in u_args:
        merge = True


def fn_checksym_edges():
    if symmetry_mode:
        # shouldmaybe  just refactor these to one vert check for both...
        lx.eval('select.convert vertex')
        verts = lx.evalN('query layerservice verts ? selected')

        neg_vert = []
        pos_vert = []

        # sort positive & negative axis sides (de-symmetrize)
        for i in verts:

            is_positive = False

            v = lx.eval('query layerservice vert.pos ? %s' % i)

            if v[symmetry_axis] >= 0:
                is_positive = True

            if not is_positive:
                neg_vert.append(i)
            if is_positive:
                pos_vert.append(i)

        if len(neg_vert) == 0 or len(pos_vert) == 0:
            sys.exit(": --- Symmetry Mode Active, but no symmetry polys were found on the opposite axis. Aborting. ---")

        else:
            # use temp selection sets to delete symmetry side (to avoid new/jumbled poly id's after delete)
            lx.eval('select.drop vertex')

            for i in pos_vert:
                lx.eval('select.element %s %s add %s' % (sel_layer, 'verts', i))

        lx.eval('select.convert edge')

    else:
        pass


def fn_checksym():
    global symcheck
    polys = lx.evalN('query layerservice polys ? selected')

    if symmetry_mode:

        neg_poly = []
        pos_poly = []
        vp = []

        # sort positive & negative axis sides (de-symmetrize)
        for p in polys:
            is_positive = False
            vl = []
            vl.extend(lx.evalN('query layerservice poly.vertList ? %s' % p))
            for j in vl:
                vp = [lx.eval('query layerservice vert.wdefpos ? %s' % j)]
            for v in vp:
                if v[symmetry_axis] >= 0:
                    is_positive = True
                    break

            if not is_positive:
                neg_poly.append(p)
            if is_positive:
                pos_poly.append(p)

        if len(neg_poly) == 0 or len(pos_poly) == 0:
            sys.exit(": --- Symmetry Mode Active, but no symmetry polys were found on the opposite axis. Aborting. ---")

        else:
            # use temp selection sets to delete symmetry side (to avoid new/jumbled poly id's after delete)
            lx.eval('select.drop polygon')

            for i in pos_poly:
                lx.eval('select.element %s %s add %s' % (sel_layer, 'polygon', i))
                lx.eval('select.editSet pos_poly_ss add pos_poly_ss')

            lx.eval('select.drop polygon')

            for i in neg_poly:
                lx.eval('select.element %s %s add %s' % (sel_layer, 'polygon', i))
            lx.eval('delete')

            lx.eval('select.useSet pos_poly_ss select')

            # re-do after de-symmetry for new id's
            polys = lx.evalN('query layerservice polys ? selected')
            symcheck = True

    else:
        pass

    return polys


# ---------------------------------------
# Check selections, WP, symmetry & stuff
# ---------------------------------------

sel_layer = lx.eval('query layerservice layers ? selected')
selmode = lx.eval('query layerservice selmode ?')
scene = modo.scene.current()

# symmetry check
if lx.eval('symmetry.state ?'):
    symmetry_mode = True
    symmetry_axis = lx.eval('symmetry.axis ?')
    lx.eval('select.symmetryState 0')

if merge:
    sel_uv_map = lx.eval1('vertMap.list type:txuv ?')
    if sel_uv_map == '_____n_o_n_e_____':
        # sel_uv_map = "Texture"
        lx.eval('select.vertexMap Texture txuv replace')
        print("You dont seem to have a UV map selected - using default 'Texture' UV map. ")
    else:
        print("Using UV map", sel_uv_map)

# ---------------------------------------
# Shoving in ITEM mode right here ...
# ---------------------------------------

if selmode == 'item':
    symmetry_mode = False

    # Get selected mesh (or instance)
    selected_items = list(scene.selectedByType('mesh')) + list(scene.selectedByType('meshInst'))
    item = selected_items[0]  # No multi selections f.n.
    if not item:
        sys.exit(": No suitable item found for item mode.")

    # Get item bounding box for mirror placement calc vs mouse pos
    item_matrix = modo.Matrix4(item.channel('worldMatrix').get())

    if item.type == 'meshInst':
        og_items = scene.items("meshInst")
        # calculating new bbox from instance source (no built in fn found?)
        instance_mode = True
        instance_src = None
        src_is_mesh = False
        src_search_index = item.index

        while src_is_mesh is False:
            instance_src = lx.eval('query sceneservice meshInst.source ? %s' % src_search_index)
            instance_src = modo.item.Item(instance_src)
            if instance_src.isAnInstance:
                src_search_index = instance_src.index
            else:
                instance_src = modo.Mesh(instance_src)
                src_is_mesh = True

        vX, vY, vZ = [], [], []
        for v in instance_src.geometry.vertices:
            vpos = modo.Matrix4(position=v.position) * item_matrix
            vp = vpos.position
            vX.append(vp[0])
            vY.append(vp[1])
            vZ.append(vp[2])

        vX.sort()
        vY.sort()
        vZ.sort()

        total = len(vX)
        avgX = sum(vX) / total
        avgY = sum(vY) / total
        avgZ = sum(vZ) / total


    else:  # Default Mesh Item mode
        og_items = scene.items("mesh")

        vX, vY, vZ = [], [], []
        for v in item.geometry.vertices:
            vpos = modo.Matrix4(position=v.position) * item_matrix
            vp = vpos.position
            vX.append(vp[0])
            vY.append(vp[1])
            vZ.append(vp[2])

        vX.sort()
        vY.sort()
        vZ.sort()

        total = len(vX)
        avgX = sum(vX) / total
        avgY = sum(vY) / total
        avgZ = sum(vZ) / total

    # Get main axis - Mouse pos on WP centered on selection ("local")
    lx.eval('workPlane.edit %s %s %s' % (avgX, avgY, avgZ))
    if lx.eval('pref.value workplane.lock ?') == "unlocked":
        lx.eval('pref.value workplane.lock locked')
        setFixed = True

    local_mouse_pos = lx.eval('query view3dservice mouse.pos ?')

    lx.eval('workPlane.reset')
    if setFixed: lx.eval('pref.value workplane.lock unlocked')

    # Get flip direction : ( "world" Mouse pos vs selection pos)
    world_mouse_pos = lx.eval('query view3dservice mouse.pos ?')

    # Sort for largest axis on 1st mouse pos for main axis
    dX = abs(local_mouse_pos[0])
    dY = abs(local_mouse_pos[1])
    dZ = abs(local_mouse_pos[2])

    axis_dic = {'0': dX, '1': dY, '2': dZ}
    pick_axis = sorted(axis_dic, key=axis_dic.__getitem__)
    axis = int(pick_axis[-1])

    if verbose:
        print("dXYZ:", dX, dY, dZ, "   Axis:", axis, pick_axis, axis_dic)

    # set flip direction based on 2nd mouse sample ("world")
    if not world:
        if axis == 0:
            cenY = vY[0]
            cenZ = vZ[0]
            if world_mouse_pos[0] >= vX[-1]:
                cenX = vX[-1]
            else:
                cenX = vX[0]

        elif axis == 1:
            cenX = vX[0]
            cenZ = vZ[0]
            if world_mouse_pos[1] >= vY[-1]:
                cenY = vY[-1]
            else:
                cenY = vY[0]

        elif axis == 2:
            cenY = vY[0]
            cenX = vX[0]
            if world_mouse_pos[2] >= vZ[-1]:
                cenZ = vZ[-1]
            else:
                cenZ = vZ[0]
    else:
        cenX, cenY, cenZ = 0, 0, 0


else:
    # ---------------------------------------
    # Component Mode
    # ---------------------------------------
    og_polys = lx.evalN('query layerservice polys ? all')

    # WP check
    if lx.eval('workPlane.state ?'):
        # If you undo after the script, WP will still be active but at origo, so this checks for that
        wp_pos = [0, 0, 0]
        wp_pos[0] = lx.eval("workplane.edit ? 0 0 0 0 0")
        wp_pos[1] = lx.eval("workplane.edit 0 ? 0 0 0 0")
        wp_pos[2] = lx.eval("workplane.edit 0 0 ? 0 0 0")
        if abs(sum(wp_pos)) > 0:
            wpfitted = True
            axis = 1
        else:
            wpfitted = False
            lx.eval('workPlane.reset')

    if selmode == 'vertex' or selmode == 'edge':
        lx.eval('select.connect')
        lx.eval('select.convert polygon')

    p = lx.evalN('query layerservice polys ? selected')
    if len(p) == 0:
        sys.exit(": Selection fail: Select enough elements to convert to polygons.")

    if not world:
        og_poly_sel = fn_checksym()
        p = og_poly_sel


    # --------------------------------------------------------------------------------------
    # get axis/mirror directions
    # --------------------------------------------------------------------------------------
    if not wpfitted:

        vl = []
        for i in p:
            vl.extend(lx.evalN('query layerservice poly.vertList ? %s' % i))
        vertlist = list(set(vl))

        for i in vertlist:
            vp = lx.eval('query layerservice vert.wdefpos ? %s' % i)
            vX.append(vp[0])
            vY.append(vp[1])
            vZ.append(vp[2])

        if axis == 9:  # if axis is NEIN; set axis by mouse_pos (2 querys)
            total = len(vertlist)
            avgX = sum(vX) / total
            avgY = sum(vY) / total
            avgZ = sum(vZ) / total

            # Get main axis - Mouse pos on WP centered on selection ("local")
            # NOTE : I think this causes the WP being re-activated bug when undoing after running.
            # If i could get a proper mousepos-to-3dpos to work ... i would ;>
            lx.eval('workPlane.edit %s %s %s' % (avgX, avgY, avgZ))
            if lx.eval('pref.value workplane.lock ?') == "unlocked":
                lx.eval('pref.value workplane.lock locked')
                setFixed = True

            local_mouse_pos = lx.eval('query view3dservice mouse.pos ?')

            lx.eval('workPlane.reset')
            if setFixed: lx.eval('pref.value workplane.lock unlocked')

            # Get flip direction : ( "world" Mouse pos vs selection pos)
            world_mouse_pos = lx.eval('query view3dservice mouse.pos ?')

            # Sort for largest axis on 1st mouse pos for main axis
            dX = abs(local_mouse_pos[0])
            dY = abs(local_mouse_pos[1])
            dZ = abs(local_mouse_pos[2])

            axis_dic = {'0': dX, '1': dY, '2': dZ}
            pick_axis = sorted(axis_dic, key=axis_dic.__getitem__)
            axis = int(pick_axis[-1])

            if verbose:
                print("--------")
                print("dXYZ:", dX, dY, dZ, "   Axis:", axis, pick_axis, axis_dic)
                print("LMousePos:", local_mouse_pos, "	 AvgXYZ:", avgX, avgY, avgZ)
                print("WMousePos:", world_mouse_pos, "	  vXYZ:", vX[-1], vY[-1], vZ[-1])

        vX.sort()
        vY.sort()
        vZ.sort()

        # set flip direction based on 2nd mouse sample ("world")
        if not world:
            if axis == 0:
                cenY = vY[0]
                cenZ = vZ[0]
                if world_mouse_pos[0] >= vX[-1]:
                    cenX = vX[-1]
                else:
                    cenX = vX[0]

            elif axis == 1:
                cenX = vX[0]
                cenZ = vZ[0]
                if world_mouse_pos[1] >= vY[-1]:
                    cenY = vY[-1]
                else:
                    cenY = vY[0]

            elif axis == 2:
                cenY = vY[0]
                cenX = vX[0]
                if world_mouse_pos[2] >= vZ[-1]:
                    cenZ = vZ[-1]
                else:
                    cenZ = vZ[0]

# -----------------------------
# Run mirror tool
# -----------------------------		

lx.eval('tool.set *.mirror on')
lx.eval('tool.attr gen.mirror axis %i' % axis)
lx.eval('tool.attr gen.mirror angle 0.0')
lx.eval('tool.attr gen.mirror frot axis')

if not wpfitted:
    lx.eval('tool.attr gen.mirror cenX %s' % cenX)
    lx.eval('tool.attr gen.mirror cenY %s' % cenY)
    lx.eval('tool.attr gen.mirror cenZ %s' % cenZ)
else:
    lx.eval('tool.attr gen.mirror cenX 0.0')
    lx.eval('tool.attr gen.mirror cenY 0.0')
    lx.eval('tool.attr gen.mirror cenZ 0.0')


if selmode == 'item':

    lx.eval('tool.attr effector.item parent off')

    if instance_mode:
        lx.eval('tool.attr effector.item instance true')
    else:
        lx.eval('tool.attr effector.item instance false')

    lx.eval('tool.attr effector.item bbox false')
    lx.eval('tool.attr effector.item hierarchy false')
    lx.eval('tool.attr effector.item source active')

    lx.eval('tool.doApply')
    lx.eval('tool.set *.mirror off')


else:

    lx.eval('tool.attr effector.clone flip true')
    lx.eval('tool.attr effector.clone replace false')
    if merge:
        lx.eval('tool.attr effector.clone merge true')
    else:
        lx.eval('tool.attr effector.clone merge false')
    lx.eval('tool.attr effector.clone source active')

    lx.eval('tool.doApply')
    lx.eval('tool.set *.mirror off')

    # select mirrored polys
    lx.eval('select.drop polygon')
    all_polys = lx.evalN('query layerservice polys ? all')
    new_polys = [i for i in all_polys if i not in og_polys]
    for i in new_polys:
        lx.eval('select.element %s %s add %s' % (sel_layer, 'polygon', i))

    if symcheck:
        lx.eval('select.useSet pos_poly_ss select')

    if merge:
        lx.eval('hide.unsel')
        lx.eval('tool.xfrmDisco true')  # should let uv.mirror tear away the uvs; works on my (modo12)machine(tm)
        lx.eval('uv.mirror u 1.1')
        lx.eval('tool.xfrmDisco false')
        lx.eval('unhide')

if symmetry_mode and not world:
    # Run mirror tool...again!
    lx.eval('tool.set *.mirror on')
    lx.eval('tool.attr gen.mirror axis %i' % symmetry_axis)
    lx.eval('tool.attr gen.mirror angle 0.0')
    lx.eval('tool.attr gen.mirror frot axis')

    lx.eval('tool.attr gen.mirror cenX 0.0')
    lx.eval('tool.attr gen.mirror cenY 0.0')
    lx.eval('tool.attr gen.mirror cenZ 0.0')

    lx.eval('tool.attr effector.clone flip true')
    lx.eval('tool.attr effector.clone replace false')
    lx.eval('tool.attr effector.clone merge false')
    lx.eval('tool.attr effector.clone source active')

    lx.eval('tool.doApply')
    lx.eval('tool.set *.mirror off')

    lx.eval('select.drop polygon')

if symmetry_mode:
    lx.eval('select.symmetryState 1')
    lx.eval('symmetry.axis %s' % symmetry_axis)
    lx.eval('select.clearSet pos_poly_ss type:polygon')

lx.eval('workPlane.reset')

# Select new items
if selmode == 'item':
    if instance_mode:
        new_items = scene.items("meshInst")
    else:
        new_items = scene.items("mesh")

    new_item = [item for item in new_items if item not in og_items]
    scene.select(new_item)
