#python

# ke_MouseFlip v1.4 - Kjell Emanuelsson 2018-2021
#
# Selection	 : Flips your selected & connected polygons based on the mouse pointer position in relation to your selection and your viewport orientation:
# 			  If viewport is X-Y with your mouse position on the left or right side of the viewport screen , the flip will be on the X world axis. Up/Down will be Y. 
# 			  If viewport is Z-Y , left/right will be Z & up/down will be Y. and so on.
# +Fitted WP : Flips your selections in the Y axis of the fitted Workplane, for more specific angles. (Ignores mouse position)			  
#
# - Requires element selection. Will select connected elements.
# - Supports *world axis* symmetry. 
# - Axis override argument ovverides, if you want unique hotkeys per axis and wp (for pie menu).
#
# Known issue: If you undo, the WP might be locked to preferred angle. you can just reset wp to unlock.
# UPDATE 1.1 : "FIXED" - undo issue (still happens, but i check for it, so the script will work. Also, resulting mesh will be unselected.
# 		 1.2 : Added Mesh Item & Mesh Instance flip support! - fixed xyz commands, some other bugs. Undo annoyance remain. (unfixable?)
#				Note: Instance flipping = replacing the old instance with the a new mirrored one, given the old one's name! ;)
#		 1.3 : Fixed various re-selection bugs & issues!
#		 1.4 : Python3 etc
# use: "@ke_MouseFlip.py"
#
# arguments:  x,y or z  : e.g: "@ke_MouseFlip.py x" to flip in x axis. (replace x with y or z for other axis.) (Ignores mouse position)


import lx, modo

axis = 9 
flip = "factX"
maxpos = False
vertlist = []
vX, vY, vZ = [], [], []
symmetry_mode = False
instance_mode = False
pos_poly = []
neg_poly = []
wpfitted = False
setFixed = False
verbose = False
noinstflip = False
symmetry_axis = 0
og_items = []
og_item = None
og_name = ""
polys = []

u_args = lx.args() 

for i in range(len(u_args)):
    if   "x" in u_args : axis = 0
    elif "y" in u_args : axis = 1
    elif "z" in u_args : axis = 2
    else: pass

# Check version
modoversion = lx.eval('query platformservice appversion ?')
if modoversion < 1200:
    noinstflip = True

# -------------------------------------------
# Check selections, screen values, mouse pos
# -------------------------------------------

scene = modo.scene.current()

sel_layer = lx.eval('query layerservice layers ? selected')	
sel_mode = lx.eval('query layerservice selmode ?')
mouse_pos = lx.eval('query view3dservice mouse.pixel ? first')

# check WP
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

# symmetry check
if lx.eval('symmetry.state ?') :
    if not wpfitted :
        symmetry_mode = True
        symmetry_axis = lx.eval('symmetry.axis ?')
        lx.eval('select.symmetryState 0')
    else :
        sys.exit(": --- Symmetry mode only supported in World Axis / Unfitted WP ---")


sel_mode = lx.eval('query layerservice selmode ?')



if sel_mode == "item":

    symmetry_mode = False

    # Get selected mesh (or instance)
    selected_items = list(scene.selectedByType('mesh')) + list(scene.selectedByType('meshInst'))
    item = selected_items[0]  # No multi selections f.n.
    if not item:
        sys.exit(": No suitable item found for item mode.")

    # Get item bounding box for mirror placement calc vs mouse pos
    item_matrix = modo.Matrix4(item.channel('worldMatrix').get())

    if item.type == 'meshInst':

        # Older versions of modo has some issue, just skippin it
        if noinstflip:
            sys.exit(": \n >>> Current Modo version not supported for Instance flipping. Req. 12+ <<<")

        og_items = scene.items("meshInst")
        og_item = item
        og_name = item.name

        # calculating new bbox from instance source (no built in fn found?)
        instance_mode = True
        instance_src = lx.eval('query sceneservice meshInst.source ? %s' % item.index)
        instance_src = modo.Mesh(instance_src)

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

        item_bb = item.geometry.boundingBox
        item_bbox = []
        for i in item_bb:
            bb = modo.Matrix4(position=i) * item_matrix
            item_bbox.append(bb.position)

        # Get item center (mesh bbox average)
        v1, v2 = (modo.Vector3(v) for v in item_bbox)
        item_center = v1.lerp(v2, 0.5)
        avgX, avgY, avgZ = item_center[0], item_center[1], item_center[2]

        lx.eval('select.convert polygon')
        sel_mode = 'polygon_item'


else:

    # ------------------------------------
    # Component Mode
    # ------------------------------------

    if sel_mode== 'polygon' or 'vertex' or 'edge':

        lx.eval('select.connect')
        lx.eval('select.convert polygon')

        polys = lx.evalN('query layerservice polys ? selected')
        if len(polys) == 0:
            sys.exit(": Selection fail: Select enough elements to convert to polygons.")

        # for i in poly :
            # lx.eval('select.element %s %s add %s' % (sel_layer, 'polygon', i) )
        lx.eval('select.editSet kepoly_ss add kepoly_ss')

    else:
        sys.exit(": Selection error: Invalid selection mode?")


    # ------------------------------------
    # symmetry workaround
    # ------------------------------------

    if symmetry_mode :

        # sort positive & negative axis sides (de-symmetrize)
        for p in polys :
            is_positive = False
            vl = []
            vp = []
            vl.extend(lx.evalN('query layerservice poly.vertList ? %s' %p))
            for j in vl:
                vp = [lx.eval('query layerservice vert.wdefpos ? %s' % j)]
            for v in vp :
                if v[symmetry_axis] >= 0:
                    is_positive = True
                    break

            if not is_positive :
                neg_poly.append(p)
            if is_positive :
                pos_poly.append(p)

        if len(neg_poly) == 0 or len(pos_poly) == 0 :
            sys.exit(": --- Symmetry Mode Active, but no symmetry polys were found on the opposite axis. Aborting. ---")

        else :
            # use temp selection sets to delete symmetry side (to avoid new/jumbled poly id's after delete)
            lx.eval('select.drop polygon')

            for i in pos_poly :
                lx.eval('select.element %s %s add %s' % (sel_layer, 'polygon', i) )
                lx.eval('select.editSet pos_poly_ss add pos_poly_ss')

            lx.eval('select.drop polygon')

            for i in neg_poly :
                lx.eval('select.element %s %s add %s' % (sel_layer, 'polygon', i) )
            lx.eval('delete')

            lx.eval('select.useSet pos_poly_ss select')

            # re-do after de-symmetry for new id's
            polys = lx.evalN('query layerservice polys ? selected')


    vl = []
    for i in polys :
        vl.extend(lx.evalN('query layerservice poly.vertList ? %s' %i))
    vertlist = list(set(vl))

    for i in vertlist :
        vp = lx.eval('query layerservice vert.wdefpos ? %s' %i )
        vX.append(vp[0])
        vY.append(vp[1])
        vZ.append(vp[2])

    total = len(vertlist)
    avgX = sum(vX) / total
    avgY = sum(vY) / total
    avgZ = sum(vZ) / total


if not wpfitted and axis == 9:

    # Get main axis : Mouse pos on WP centered on selection ("local")
    lx.eval('workPlane.edit %s %s %s' %(avgX, avgY, avgZ))
    if lx.eval('pref.value workplane.lock ?') == "unlocked" :
        lx.eval('pref.value workplane.lock locked')
        setFixed = True

    local_mouse_pos = lx.eval('query view3dservice mouse.pos ?')

    lx.eval('workPlane.reset')
    if setFixed : lx.eval('pref.value workplane.lock unlocked')

    # Get flip direction : ( "world" Mouse pos vs selection pos)
    world_mouse_pos = lx.eval('query view3dservice mouse.pos ?')

    # Sort for largest axis on 1st mouse pos for main axis
    dX = abs(local_mouse_pos[0])
    dY = abs(local_mouse_pos[1])
    dZ = abs(local_mouse_pos[2])

    axis_dic = { '0':dX, '1':dY, '2':dZ }
    pick_axis = sorted(axis_dic, key=axis_dic.__getitem__)
    axis = int(pick_axis[-1])

    if verbose :
        print("--------")
        print("dXYZ:", dX,dY,dZ, "   Axis:", axis, pick_axis,axis_dic)
        print("LMousePos:", local_mouse_pos, "   AvgXYZ:", avgX,avgY,avgZ)
        print("WMousePos:", world_mouse_pos, "    vXYZ:", vX[-1],vY[-1],vZ[-1])

# --------------------------------------------------------------------------------------
# Flip using mirror-in-place
# --------------------------------------------------------------------------------------	

lx.eval('tool.set *.mirror on')
lx.eval('tool.attr gen.mirror axis %i' % axis)
lx.eval('tool.attr gen.mirror angle 0.0')
lx.eval('tool.attr gen.mirror frot axis')

if not wpfitted:
    lx.eval('tool.attr gen.mirror cenX %s' % avgX)
    lx.eval('tool.attr gen.mirror cenY %s' % avgY)
    lx.eval('tool.attr gen.mirror cenZ %s' % avgZ)
else:
    lx.eval('tool.attr gen.mirror cenX 0.0')
    lx.eval('tool.attr gen.mirror cenY 0.0')
    lx.eval('tool.attr gen.mirror cenZ 0.0')


if sel_mode == 'item':  # mesh Instance actually

    lx.eval('tool.attr effector.item parent off')

    if instance_mode:
        lx.eval('tool.attr effector.item instance true')
    else:
        lx.eval('tool.attr effector.item instance false')

    lx.eval('tool.attr effector.item bbox false')
    lx.eval('tool.attr effector.item hierarchy false')
    lx.eval('tool.attr effector.item source active')

else:

    lx.eval('tool.attr effector.clone flip true')
    lx.eval('tool.attr effector.clone replace true')
    lx.eval('tool.attr effector.clone source active')

lx.eval('tool.doApply')
lx.eval('tool.set *.mirror off')


if sel_mode == 'item':
    # Mesh Instance crap workaround - just makes a new item...cleanup
    new_items = scene.items("meshInst")
    new_item = [item for item in new_items if item not in og_items]
    scene.removeItems(og_item)
    scene.select(new_item)
    lx.eval('item.name %s' % og_name)  # sneaky!

if wpfitted :
    lx.eval('workPlane.reset')

# and mirror tool if symmetry is on
if symmetry_mode:

    for i in polys:
        lx.eval('select.element %s %s add %s' % (sel_layer, 'polygon', i))

    lx.eval('tool.set *.mirror on')
    lx.eval('tool.attr gen.mirror axis %i' %symmetry_axis)
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
    lx.eval('select.symmetryState 1')
    lx.eval('symmetry.axis %s' %symmetry_axis )
    lx.eval('select.clearSet pos_poly_ss type:polygon')

if sel_mode == 'polygon_item' or sel_mode == 'item':
    lx.eval('select.typeFrom item')

elif sel_mode == 'polygon' or 'vertex' or 'edge':
    lx.eval('select.useSet kepoly_ss select')
    lx.eval('select.clearSet kepoly_ss type:polygon')
