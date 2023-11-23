# python

# ke_fit2grid v1.3 - Kjell Emanuelsson 2019-21
#
# Snaps every selected vert from element selection (or all verts, if in item mode) to nearest grid position as specified
# Meant for low poly use, a few verts at a time - will be very very slow on 1k+ vert selections.
# note: - Verts already on the specified grid will not be fit to grid.
#       - See the count of fitted verts in the event log.
#       - Fitted verts will be selected. ( set "select_fitted" variable below to False to skip. )
#       - Could be useful just to check if you are actually on grid...
#       - Assuming metric units used (meters: just convert the arguments (yourself!) in the pie cfg if needed;>)
#
# Update 1.1 - Added user value prompt (argument) for custom grid size
#        1.2 - Fixed input value bug & added micrometer fix + pie menu
#        1.3 - Python3 fixes

import lx
import modo

select_fitted = True
user_spec = False
grid = 0.01

# Setting grid size
u_arg = lx.args()
if u_arg:
    try:
        grid = float(u_arg[0])
    except Exception as e:
        print(e)
        grid = 0.1
    if "user_spec" in u_arg:
        user_spec = True

if user_spec:
    lx.eval('user.defNew fit2grid.userValue distance momentary')
    lx.eval('user.def fit2grid.userValue dialogname {Fit 2 Grid}')
    lx.eval('user.def fit2grid.userValue username {Grid Spacing}')
    try:
        lx.eval('user.value fit2grid.userValue')
        grid = lx.eval('user.value fit2grid.userValue ?')
    except Exception as e:
        print(e)
        sys.exit(" Fit 2 Grid - User Aborted Script ")

print(" -------------- Fit 2 Grid ------------------------------")
print(" --- Fitting to grid using grid size:", grid)


def fit_to_grid(xyz):
    x, y, z = round(xyz[0] / grid) * grid, round(xyz[1] / grid) * grid, round(xyz[2] / grid) * grid
    return round(x, 4), round(y, 4), round(z, 4)


# -------------------------------------------------------------------------
# Initial scene check
# -------------------------------------------------------------------------
sel_layer = lx.eval('query layerservice layers ? selected')
layer_ID = lx.eval1('query layerservice layer.ID ? {%s}' % sel_layer)
sel_mode = lx.eval('query layerservice selmode ?')
scene = modo.scene.current()

wp_fitted = lx.eval1('workPlane.state ?')

if lx.eval('symmetry.state ?'):
    lx.eval('select.symmetryState 0')
    symmetry_on = True
else:
    symmetry_on = False

# Make sure item is selected
scene.select(layer_ID)

# Make sure item is mesh
sel_mesh = scene.selectedByType("mesh")
if not sel_mesh:
    sys.exit(": ---> Item not selected? <--- ")
else:
    sel_mesh = sel_mesh[0]

mesh = modo.Mesh()


# -------------------------------------------------------------------------
# Snap-fit verts to grid
# -------------------------------------------------------------------------
if sel_mode != "vertex":
    lx.eval('select.convert vertex')

sel_verts = mesh.geometry.vertices.selected
if not sel_verts:
    sel_verts = [i for i in mesh.geometry.vertices]

fitted_verts = []

for i in sel_verts:
    vert = i.index
    old_coords = lx.evalN('query layerservice vert.wdefpos ? {%s}' % vert)
    coords = fit_to_grid(old_coords)
    old_coords = tuple([round(i, 4) for i in old_coords])

    if coords != old_coords:
        lx.eval('select.element %s %s set %s' % (sel_layer, 'vertex', vert))
        lx.eval('vert.set x {%s} worldSpace:true' % coords[0])
        lx.eval('vert.set y {%s} worldSpace:true' % coords[1])
        lx.eval('vert.set z {%s} worldSpace:true' % coords[2])
        fitted_verts.append(vert)


# -------------------------------------------------------------------------
# Clean up
# -------------------------------------------------------------------------

# report !
print(" --- Nr of Fitted Verts:", len(fitted_verts))

if select_fitted:
    lx.eval('!!select.drop vertex')
    for i in fitted_verts:
        lx.eval('select.element %s %s add %s' % (sel_layer, 'vertex', i))

else:
    lx.eval('!!select.drop vertex')
    lx.eval('!!select.typeFrom {%s}' % sel_mode)

if symmetry_on:
    lx.eval('select.symmetryState 1')
