# python#

# NailGun 1.2 - Kjell Emanuelsson 2018-2021
#
# Instances "loaded" item to where you point the mouse on any mesh item
#
# 1.2        - Python3 & fixes
# 1.1        - Added mode to parent instances to target mesh - use tool choice in nail gun menu and ctrl-shift to map.
# 1.0        - Enabled symmetry move. Fixed offset. Fixed selection bug with different mesh item selected.
# 0.91		 - Improved workflow - selecting instance will let you re-place the instance.
# 			   Drop item selections or click use slot to resume nailgun operation.
# Update 0.9 - Much faster, suppots world symmetry. (Note: Offset only works with workplane atm.)
#
# Use:	Requires you have used the loader script to pick item to instance. (You can load instances too) And then:
# 		Just point your mouse on any element of any mesh to instance
# 		Optionally: Fit the work plane for more specific placements beforehand.
#       Note: Symmetry only supported for world axis - just a mirror-tool macro basically.
#
# Tip : Might get confused if you're zoomed out too much - Zoom in a bit.

import lx, modo
from math import radians

verbose = True
item = []
offset = 0
orphaned = False
symmetry_mode = False
sceneitem = False
instance_reselect = False
targetparent = False
hit_rot = modo.Matrix3()
hit_pos = modo.Vector3()
hit_normal = modo.Vector3()
symmetry_axis = 0

u_args = lx.args()

for i in range(len(u_args)):
    if "targetparent" in u_args:
        targetparent = True


def vector_rotation(dVec=modo.Vector3(1, 0, 0), rotOrder='zxy', asDegrees=True):
    dVec.normalize()
    upVec = modo.Vector3(0, 1, 0)
    if dVec.dot(upVec) < -0.99: upVec = modo.Vector3(1, 0, 0)

    nVec = dVec.cross(upVec).normal()
    upVec = nVec.cross(dVec).normal()
    matrix = modo.Matrix4((nVec.values, dVec.values, upVec.values))

    xAlignMatrix = modo.Matrix4.fromEuler((0, radians(180.0), 0))
    matrix = xAlignMatrix * matrix

    return matrix.asEuler(degrees=asDegrees, order=rotOrder)


def check_slots(count):
    slot_list = []
    for nr in range(1,count+1) :
        slot = "ke_nailgun.itemSlot"+str(nr)
        slot_list.append(lx.eval('user.value {%s} ?' %slot))
    return slot_list


# Set item mode
if lx.eval('query layerservice selmode ?') != "item":
    lx.eval('select.typeFrom item')


# --------------------------------------------------------------------
# Load UserValue Item
# --------------------------------------------------------------------

try:
    item = lx.eval('!!user.value ke_nailgun.item ?')
    if item == "None":
        sys.exit(": --- Loader Error: Mesh Item not Loaded. Please use Loader to select Item for instancing. --- ")

except Exception as e:
    sys.exit(": --- Loader Error: Mesh Item not Loaded. Please use Loader to select Item for instancing. --- \n", e)

if lx.eval('query scriptsysservice userValue.isDefined ? ke_nailgun.offset'):
    offset = lx.eval('user.value ke_nailgun.offset ?')


# --------------------------------------------------------------------
# Check scene selection
# --------------------------------------------------------------------

scene = modo.scene.current()

try:
    sceneitem = scene.selected[0]
    if sceneitem == item:
        sceneitem = False
except Exception as e:
    print(e)
    pass

if sceneitem:  # checking selected item relationships for instance moving
    if sceneitem.isAnInstance:
        try:
            check_parent = sceneitem.parents[0]
        except Exception as e:
            print(e)
            check_parent = False

        if check_parent == item:
            scene.removeItems(sceneitem)
            sel_item = item
            instance_reselect = True

        elif check_parent:
            slotlist = check_slots(6)
            if check_parent.id in slotlist:
                scene.removeItems(sceneitem)
                sel_item = check_parent
                item = check_parent
                instance_reselect = True
            else:
                sel_item = item
        else:
            sel_item = item
    else:
        sel_item = item  # otherwise loaded item gets instanced


# symmetry check
if lx.eval('symmetry.state ?'):
    symmetry_mode = True
    symmetry_axis = lx.eval('symmetry.axis ?')
    lx.eval('select.symmetryState 0')


# --------------------------------------------------------------------
# Prep Item/Selections & Instance
# --------------------------------------------------------------------

item = modo.item.Item(item)
sel_item = scene.duplicateItem(item, instance=True)  # # Instance the item!

if verbose:
    print("-------------")
    print("NailGun loaded Item: ", item.name, "(%s)" % item)
    print("Offset value:", offset)

# Check parents & Temp-Orphaning
parents = item.parents
parent = None

if parents:
    if parents[0].type == 'mesh':
        parent = parents[0]
    else:
        parent = item

    lx.eval('item.parent {%s} {%s} 0 inPlace:1' % (sel_item.id, "None"))
    orphaned = True
    if verbose:
        print("Parents:", parents, "	  Orphaned:", orphaned)

# ------------------------------------------------------------
# Get placement transform
# ------------------------------------------------------------

wp_fitted = lx.eval1('workPlane.state ?')
target_mesh = []

if not wp_fitted:

    if targetparent:
        try:
            lx.eval('select.3DElementUnderMouse set')
            target_mesh = scene.selected[-1]
        except Exception as e:
            sys.exit(":Reason: Miss! Could not find suitable POLY under mouse pointer. \nException:", e)

        if target_mesh:
            lx.eval1('query layerservice layer.index ? %s' % target_mesh.id)
        else:
            sys.exit(": No valid mesh found under mouse to parent under...")

    try:
        hit_normal = lx.eval('query view3dservice mouse.hitNrm ?')
        hit_pos = lx.eval('query view3dservice mouse.hitPos ?')
        if verbose: print("hit normal:", hit_normal)
        hit_rot = vector_rotation(modo.Vector3(hit_normal))
    except Exception as e:
        sys.exit(": --- Could not find appropriate mesh layer under mouse. Aborting. --- \n", e)


elif wp_fitted:

    if offset > 0:
        lx.eval('workPlane.offset 1 {%s}' % offset)

    chan_read = lx.object.ChannelRead(scene.Channels(None, 0.0))
    hit_pos = scene.WorkPlanePosition(chan_read)
    hit_rot = scene.WorkPlaneRotation(chan_read)
    hit_rot = modo.Matrix3(hit_rot)
    hit_rot = hit_rot.asEuler(degrees=True, order='zxy')

if verbose: print("hit pos,rot:", hit_pos, hit_rot)

# ------------------------------------------------------------
# Place item (Set transform)
# ------------------------------------------------------------

lx.eval('select.item {%s} set' % sel_item.id)

if offset > 0 and not wp_fitted:
    offset_pos = modo.Vector3(hit_pos)
    offset_vec = modo.Vector3(hit_normal) * offset
    offset_pos = offset_pos + offset_vec
    hit_pos = offset_pos
    if verbose: print("Offset position:", offset_pos)


locator = modo.LocatorSuperType(sel_item)
locator.position.set(hit_pos)
locator.rotation.set(hit_rot, degrees=True)

if targetparent:
    lx.eval('item.parent {%s} {%s} 0 inPlace:1' % (sel_item.id, target_mesh.id))
else:
    if orphaned and parent is not None:
        lx.eval('item.parent {%s} {%s} 0 inPlace:1' % (sel_item.id, parent.id))
    else:
        lx.eval('item.parent {%s} {%s} 0 inPlace:1' % (sel_item.id, item.id))

if wp_fitted:
    lx.eval('workPlane.reset')

if symmetry_mode:
    lx.eval('select.item {%s} set' % sel_item.id)
    lx.eval('tool.set "Instance Mirror" on')
    lx.eval('tool.reset')
    lx.eval('tool.attr gen.mirror cenX 0.0')
    lx.eval('tool.attr gen.mirror cenY 0.0')
    lx.eval('tool.attr gen.mirror cenZ 0.0')
    lx.eval('tool.attr gen.mirror angle 0.0')
    lx.eval('tool.attr gen.mirror frot axis')
    lx.eval('tool.attr gen.mirror axis {%s}' % symmetry_axis)
    lx.eval('tool.attr effector.item source active')
    lx.eval('tool.apply')
    lx.eval('tool.set "Instance Mirror" off')
    lx.eval('select.symmetryState 1')
    lx.eval('symmetry.axis %s' % symmetry_axis)
    lx.eval('select.item {%s} set' % item.id)

if instance_reselect:
    scene.select(sel_item)
else:
    scene.select(item)