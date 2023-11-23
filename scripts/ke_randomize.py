# python

# Randomize v1.1 - Kjell Emanuelsson 2019-21
# 1.1 - Python3 fixes
# Will randomize selected items based on menu settings. Pretty self-explanatory!

import modo
import random
from math import ceil, degrees

verbose = True
use_group = False
group_only = False
deselect_only = False
randomize_value = 0
uniform_pos = False
uniform_scl = False
uniform_rot = False
skip_scale = True
sel_group_items = []

u_args = lx.args()

for i in range(len(u_args)):
    if "deselect" in u_args:
        deselect_only = True
    elif "group" in u_args:
        group_only = True
        use_group = True

# Import values from config
randomize_value = lx.eval('user.value ke_randomize.selection ?')
uniform_pos = lx.eval('user.value ke_randomize.uniform.pos ?')
uniform_rot = lx.eval('user.value ke_randomize.uniform.rot ?')
uniform_scl = lx.eval('user.value ke_randomize.uniform.scl ?')
pos_xmin = lx.eval('user.value ke_randomize.pos.x.min ?')
pos_xmax = lx.eval('user.value ke_randomize.pos.x.max ?')
pos_ymin = lx.eval('user.value ke_randomize.pos.y.min ?')
pos_ymax = lx.eval('user.value ke_randomize.pos.y.max ?')
pos_zmin = lx.eval('user.value ke_randomize.pos.z.min ?')
pos_zmax = lx.eval('user.value ke_randomize.pos.z.max ?')
rot_xmin = lx.eval('user.value ke_randomize.rot.x.min ?')
rot_xmax = lx.eval('user.value ke_randomize.rot.x.max ?')
rot_ymin = lx.eval('user.value ke_randomize.rot.y.min ?')
rot_ymax = lx.eval('user.value ke_randomize.rot.y.max ?')
rot_zmin = lx.eval('user.value ke_randomize.rot.z.min ?')
rot_zmax = lx.eval('user.value ke_randomize.rot.z.max ?')
# scale uses multiply, so cant be 0
scl_xmin = lx.eval('user.value ke_randomize.scl.x.min ?')
if scl_xmin == 0: scl_xmin = 1.0
scl_xmax = lx.eval('user.value ke_randomize.scl.x.max ?')
if scl_xmax == 0: scl_xmax = 1.0
scl_ymin = lx.eval('user.value ke_randomize.scl.y.min ?')
if scl_ymin == 0: scl_ymin = 1.0
scl_ymax = lx.eval('user.value ke_randomize.scl.y.max ?')
if scl_ymax == 0: scl_ymax = 1.0
scl_zmin = lx.eval('user.value ke_randomize.scl.z.min ?')
if scl_zmin == 0: scl_zmin = 1.0
scl_zmax = lx.eval('user.value ke_randomize.scl.z.max ?')
if scl_zmax == 0: scl_zmax = 1.0

for i in (scl_xmin, scl_xmax, scl_ymin, scl_ymax, scl_zmin, scl_zmax):
    if i != 1.0:
        skip_scale = False
        break

if lx.eval('user.value ke_randomize.use_group ?') == "on":
    use_group = True


# set any uniform toggle to X values
if uniform_pos == "on":
    pos_ymin, pos_zmin = pos_xmin, pos_xmin
    pos_ymax, pos_zmax = pos_xmax, pos_xmax

if uniform_rot == "on":
    rot_ymin, rot_zmin = rot_xmin, rot_xmin
    rot_ymax, rot_zmax = rot_xmax, rot_xmax

if uniform_scl == "on":
    scl_ymin, scl_zmin = scl_xmin, scl_xmin
    scl_ymax, scl_zmax = scl_xmax, scl_xmax


def normalize_angles(vtuple):
    return [a % 360 for a in vtuple]


def radian_to_degrees(values):
    return [degrees(angle) for angle in values]


if verbose:
    print("==================== Randomize =========================")
    print("Randomize Deselect: ", randomize_value)
    print("Uniform Pos/Rot/Scl: ", uniform_pos, uniform_rot, uniform_scl)
    # print("Using Pos/Rot/Scl: ", use_pos, use_rot, use_scl)
    print("X :", pos_xmin, pos_xmax, rot_xmin, rot_xmax, scl_xmin, scl_xmax)
    print("Y :", pos_ymin, pos_ymax, rot_ymin, rot_ymax, scl_ymin, scl_ymax)
    print("Z :", pos_zmin, pos_zmax, rot_zmin, rot_zmax, scl_zmin, scl_zmax)
    print("Using random group items: ", use_group)


# Selections ------------------------------------------------------------------------------------------
scene = modo.scene.current()
allowed_types = ['mesh', 'meshInst', 'groupLocator', 'camera', 'locator', 'portal', 'meshLight',
                 'polyRender', 'sunLight', 'photometryLight', 'pointLight', 'spotLight', 'areaLight',
                 'cylinderLight', 'domeLight']

sel_items = []
selection = scene.selected

for item in selection:
    if item.type in allowed_types:
        sel_items.append(item)

if not sel_items: sys.exit(": No valid items selected? ")


# Prepare to Replace items with group items if option is toggled
if use_group:

    sel_group = scene.selectedByType('group')

    if sel_group:
        sel_group = sel_group[0]
        sel_group_items = list(sel_group.items)

        if sel_group_items:
            # Make sure there is enough elements in the group list
            if len(sel_group_items) < len(sel_items):
                new_group, ecount = divmod(len(sel_items), len(sel_group_items))
                new_group *= sel_group_items + sel_group_items[:ecount]
                sel_group_items = new_group
            # randomize these too
            random.shuffle(sel_group_items)

        else:
            use_group = False
            print("No Group was found / Group was empty - Skipping random group replacements.")


# Random De-Selection ----------------------------------------------------------------------------------
if randomize_value:
    random.shuffle(sel_items)
    new_sel_count = int(ceil(len(sel_items) * randomize_value))
    sel_items = sel_items[:new_sel_count]
    scene.select(sel_items)

if deselect_only:
    sys.exit()

# Randomize ! ------------------------------------------------------------------------------------------
grp_count = 0

for item in sel_items:

    locator = modo.LocatorSuperType(item)
    old_pos = modo.Vector3(locator.position.get())
    old_scl = modo.Vector3(locator.scale.get())
    old_rot = locator.rotation.get(degrees=True)
    old_rot = modo.Vector3(normalize_angles(old_rot))

    if use_group and sel_group_items:
        new_item = scene.duplicateItem(sel_group_items[grp_count])
        locator = modo.LocatorSuperType(new_item)
        scene.removeItems(item)
        grp_count += 1

        if group_only:
            locator.position.set(old_pos)
            locator.rotation.set(old_rot, degrees=True)
            locator.scale.set(old_scl)

    if not group_only:
        # position
        rnd_posx = random.uniform(pos_xmin, pos_xmax)
        rnd_posy = random.uniform(pos_ymin, pos_ymax)
        rnd_posz = random.uniform(pos_zmin, pos_zmax)
        rnd_pos = modo.Vector3(rnd_posx, rnd_posy, rnd_posz) + old_pos
        locator.position.set(rnd_pos)

        # rotation
        rnd_rotx = random.uniform(rot_xmin, rot_xmax)
        rnd_roty = random.uniform(rot_ymin, rot_ymax)
        rnd_rotz = random.uniform(rot_zmin, rot_zmax)
        rnd_rot = modo.Vector3(rnd_rotx, rnd_roty, rnd_rotz)
        rnd_rot = radian_to_degrees(rnd_rot)
        locator.rotation.set(rnd_rot, degrees=True)

        # scale
        if not skip_scale:
            pick = [random.uniform(scl_xmin, 1), random.uniform(scl_xmax, 1)]
            rnd_sclx = random.choice(pick)
            pick = [random.uniform(scl_ymin, 1), random.uniform(scl_ymax, 1)]
            rnd_scly = random.choice(pick)
            pick = [random.uniform(scl_zmin, 1), random.uniform(scl_zmax, 1)]
            rnd_sclz = random.choice(pick)
            rnd_scl = modo.Vector3(rnd_sclx, rnd_scly, rnd_sclz) * old_scl
            locator.scale.set(rnd_scl)
