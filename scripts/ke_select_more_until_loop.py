# python
# select_more_until_loop v1.0  2019 Kjell Emanuelsson, from the classic script by Seneca Menard
# Why bother? For some reason the old perl-script is really slow in some cases - this is faster in those cases.
# Though not as fast as I'd like...

import modo

mon = lx.Monitor()
mon.init(20)

# Scene & Selections
layer_index = lx.eval('query layerservice layers ? selected')
layer_ID = lx.eval1('query layerservice layer.ID ? {%s}' % layer_index)
lx.eval('select.subItem {%s} set' % layer_ID)

scene = modo.scene.current()
mesh = scene.selectedByType('mesh')[0]
geo = mesh.geometry

sel_mode = lx.eval('query layerservice selmode ?')

sel = []
if sel_mode == "vertex":
    sel = geo.vertices.selected
elif sel_mode == "edge":
    sel = geo.edges.selected
elif sel_mode == "polygon":
    sel = geo.polygons.selected
else:
    sys.exit(": Invalid Selecttion. Please select vertices, edges or polys. ")
if not sel: sys.exit(": Invalid Selecttion. Please select vertices, edges or polys. ")

sel_count = len(sel)
new_count = sel_count
loop_count = 0
loop_max = 1024

# Select!
while new_count >= sel_count:
    mon.step()

    try:
        lx.eval('select.more')
    except Exception as e:
        print(e)
        break

    new_count = lx.eval('select.count %s ?' % sel_mode)
    if new_count == sel_count:
        break
    else:
        sel_count = new_count

    # Just in case...
    loop_count += 1
    if loop_count >= loop_max:
        break
