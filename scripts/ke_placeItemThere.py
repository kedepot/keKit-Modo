#python

# placeItemThere 1.2 - Kjell Emanuelsson 2018-21
#
# 1.2 - Python3 fixes
# Update 1.1 - Fixed dupe & instance arguments
#
# Places & rotates selected item to another mesh surface at mouse position. Or fitted WP, if active.  
# Useful for placing texture locators for example, but works for ---any item with a transform---. probably.
#
# Argument : dupe	  - Duplicates selected item 
#			 instance - Instances selected item		


import lx
import modo
from math import radians

u_args = lx.args()

dupe = False
instance = False
is_instance = False
orphaned = False
verbose = True
parent = None
hit_pos = modo.Vector3()
hit_rot = modo.Matrix3()

if verbose:
    print("........\n", "PlaceItemThere Output:")

for i in range(len(u_args)):
    if "dupe" in u_args:
        dupe = True
    if "instance" in u_args:
        instance = True


def vector_rotation(dVec=modo.Vector3(1, 0, 0), rotOrder='zxy', asDegrees=True):
    # Rotation from one vector/normal using Y up
    dVec.normalize()
    upVec = modo.Vector3(0, 1, 0)

    # Check for parallell vectors
    if dVec.dot(upVec) < -0.99:
        upVec = modo.Vector3(1, 0, 0)

    nVec = dVec.cross(upVec).normal()
    upVec = nVec.cross(dVec).normal()
    matrix = modo.Matrix4((nVec.values, dVec.values, upVec.values))

    xAlignMatrix = modo.Matrix4.fromEuler((0, radians(180.0), 0))
    matrix = xAlignMatrix * matrix

    return matrix.asEuler(degrees=asDegrees, order=rotOrder)


#------------------------------------------------------------
# Get first selected ITEM with suitable transform, and selected image if active (for tloc moving)
#------------------------------------------------------------

# item mode only
if lx.eval('query layerservice selmode ?') != "item":
    lx.eval('select.typeFrom item')

# Check scene for appropriate items	
scene = modo.scene.current()
images, items, item_M = [], [], []

for item in scene.selected:

    if item.type == 'imageMap':
        images.append(item)

    if item.channel('worldMatrix'):
        items.append(item)
    # item_M.append( modo.Matrix4( item.channel('worldMatrix').get() ) )


# Check selections
if len(items) > 0:

    if items[0].isAnInstance: is_instance = True

    if dupe: sel_item = scene.duplicateItem(items[0])
    elif instance: sel_item = scene.duplicateItem(items[0], instance=True)
    else: sel_item = items[0]

    # Check parents & Temp-Orphaning (for now)
    parents = items[0].parents

    if parents:
        if is_instance:
            if parents[0].type == 'mesh':
                parent = parents[0]
            else:
                parent = items[0]

        elif instance: parent = items[0]
        else: parent = parents[0]

        lx.eval('item.parent {%s} {%s} 0 inPlace:1' % (sel_item.id, "None"))
        orphaned = True
        if verbose:
            print("Parents:", parents, "   Orphaned:", orphaned)

else:
    sys.exit(": --- Selection error. Item not selected? ---")


if len(images) > 0:
    sel_image = images
else:
    sel_image = False

# if len(item_M) > 0 :
# matrix = item_M[0]
# else : matrix = False	

if verbose:
    print("Selected Item:", sel_item)


#------------------------------------------------------------
# Get placement transform
#------------------------------------------------------------

wp_fitted = lx.eval1('workPlane.state ?')

if not wp_fitted:

    try:
        hit_normal = lx.eval('query view3dservice mouse.hitNrm ?')
        hit_pos = lx.eval('query view3dservice mouse.hitPos ?')
        if verbose:
            print("hit normal:", hit_normal)
        hit_rot = vector_rotation(modo.Vector3(hit_normal))
    except Exception as e:
        sys.exit(": --- Could not find appropriate mesh layer under mouse. Aborting. ---\n", e)


elif wp_fitted:
    chan_read = lx.object.ChannelRead(scene.Channels(None, 0.0))
    hit_pos = scene.WorkPlanePosition(chan_read)
    hit_rot = scene.WorkPlaneRotation(chan_read)
    hit_rot = modo.Matrix3(hit_rot)
    hit_rot = hit_rot.asEuler(degrees=True, order='zxy')

if verbose:
    print("hit pos,rot:", hit_pos, hit_rot)


#------------------------------------------------------------
# Place item (Set transform)
#------------------------------------------------------------

if dupe or instance:  # or viewport wont update until clicking screen...
    lx.eval('select.item {%s} set' % sel_item.id)

if instance or is_instance:
    modo.LocatorSuperType(sel_item).position.set(hit_pos)
    modo.LocatorSuperType(sel_item).rotation.set(hit_rot, degrees=True)

    if orphaned:
        lx.eval('item.parent {%s} {%s} 0 inPlace:1' % (sel_item.id, parent.id))

    elif instance:
        lx.eval('item.parent {%s} {%s} 0 inPlace:1' % (sel_item.id, items[0].id))

else:
    sel_item.position.set(hit_pos)
    sel_item.rotation.set(hit_rot, degrees=True)
    if orphaned:
        lx.eval('item.parent {%s} {%s} 0 inPlace:1' % (sel_item.id, parent.id))

# Re-selecting active image layers if any
if sel_image:
    for img in sel_image:
        img.select()
