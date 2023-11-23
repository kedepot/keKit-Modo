# python

# Swap Places v1.0 - Kjell Emanuelsson 2019
#
# Simple script that swaps position and rotation of the first and last selected item.
# + optional user command also swaps scale.
# + optional user command that skips rotation swap.

import modo

scl = False
rot = True
tgt_rot = modo.Matrix3()
tgt_scl = modo.Vector3()
src_rot = modo.Matrix3()
src_scl = modo.Vector3()

u_args = lx.args()

for i in range(len(u_args)):
    if "scale" in u_args:
        scl = True
    if "norot" in u_args:
        rot = False

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

# Get transforms
src_locator = modo.LocatorSuperType(sel_items[0])
src_pos = src_locator.position.get()
if rot: src_rot = src_locator.rotation.get()
if scl: src_scl = src_locator.scale.get()

tgt_locator = modo.LocatorSuperType(sel_items[-1])
tgt_pos = tgt_locator.position.get()
if rot: tgt_rot = tgt_locator.rotation.get()
if scl: tgt_scl = tgt_locator.scale.get()

# Switch transforms
src_locator.position.set(tgt_pos)
if rot: src_locator.rotation.set(tgt_rot)
if scl: src_locator.scale.set(tgt_scl)

tgt_locator.position.set(src_pos)
if rot: tgt_locator.rotation.set(src_rot)
if scl: tgt_locator.scale.set(src_scl)
