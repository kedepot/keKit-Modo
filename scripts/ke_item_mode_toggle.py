# python
# EditModeToggle 1.0 Kjell Emanuelsson 2020
# 1.1 - 2021 Python3 Fixes etc
# Toggles between item and element mode, and remembers which mode you were in. (As in blender, for example)

sel_mode = lx.eval('query layerservice selmode ?')

if not lx.eval('query scriptsysservice userValue.isDefined ? ke.selmode'):
    user_mode = 'polygon'
else:
    user_mode = lx.eval('user.value ke.selmode ?')

if sel_mode == 'item' :
    if user_mode == 'edge':
        lx.eval('select.typeFrom edge')
    elif user_mode == 'vertex':
        lx.eval('select.typeFrom vertex')
    else:
        lx.eval('select.typeFrom polygon')

elif sel_mode == 'polygon' or sel_mode == 'edge' or sel_mode == 'vertex':
    if not lx.eval('query scriptsysservice userValue.isDefined ? ke.selmode'):
        lx.eval('user.defNew ke.selmode string temporary')
        lx.eval('user.value ke.selmode %s' % sel_mode)
    else:
        lx.eval('user.value ke.selmode %s' % sel_mode)
    lx.eval('select.typeFrom item')
