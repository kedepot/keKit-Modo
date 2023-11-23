# python
# Atlas & Texel Map v1.1 - Kjell Emanuelsson 2019-21
# 1.1 - Python3
# UV Atlas maps & checks the FIRST selected polys assigned image size for texel density scaling basis.
# would have just been a macro, but the "poly" option was borken on the texel density toolkit version i was using...
# Will use whatever density target you have specified in the texel density toolkit, or,
# user argument with a custom value. E.g: "@ke_atlastexel.py 1024" will override the density goal.
# Script is limited to color textures. Override with user arguemnt "anyclip", to allow...any type,
# note: Probably wont work with parenthesis in your materialnames, not counting the default (Material) thing.
#       I also put in some uv-treatments (relax, attempting rectangle, orient and fit)
#       There is also an argument for barycentric instead of atlas uv mapping: "barycentric"

import re
import modo

anyclip = False
density = []
clip_info = []
clip_name = []
barycentric = False
fix_overlap = False

u_arg = lx.args()
if u_arg:
    for i in u_arg:
        if "barycentric" in u_arg:
            barycentric = True
        if "anyclip" in u_arg:
            anyclip = True
        try:
            density = int(i)
        except Exception as e:
            print(e)
            density = []


print("------------------------ Atlas & Texel Map----------------------------")

# ---------------------------------------------------------------------------
# Scene setup & making sure item is selected --------------------------------
# ---------------------------------------------------------------------------
layer_index = lx.eval('query layerservice layers ? selected')
layer_ID = lx.eval1('query layerservice layer.ID ? {%s}' % layer_index)
lx.eval('select.subItem {%s} set' % layer_ID)
scene = modo.scene.current()

# ---------------------------------------------------------------------------
# Selections ----------------------------------------------------------------
# ---------------------------------------------------------------------------
p = lx.eval('query layerservice polys ? selected')
if not p:
    sys.exit(":   >>>   No polys selected  <<<   ")
else: p = p[0]

p_mat = lx.eval('query layerservice poly.material ? %s' % p)
# p_verts = lx.eval('query layerservice poly.vertList ? %s' % p)
print("Polygon material:", p_mat)

# ---------------------------------------------------------------------------
# Check for selected polys' UV map ------------------------------------------
# ---------------------------------------------------------------------------
sel_uv_map = lx.eval1('vertMap.list type:txuv ?')

uv_maps = lx.evalN('query layerservice vmaps ? texture')

p_uv_map = []
for i in uv_maps:
    uvmap_name = lx.eval('query layerservice vmap.name ? %s' % i)
    if lx.eval('query layerservice uv.N ? %s' % "all"):
        # finding if the uv map is used by the selection via vmap values...
        p_uvs = lx.eval('query layerservice poly.vmapValue ? %s' % p)
        if any(p_uvs):
            p_uv_map = uvmap_name
            break

if not p_uv_map: sys.exit(":  >>> Selected poly does not seem to have a uv-map? <<<  ")

if sel_uv_map == '_____n_o_n_e_____':
    lx.eval('select.vertexMap {%s} txuv replace' % p_uv_map)
    print("No uv-map selected: Selecting uvmap used by polygon.")
else: p_uv_map = sel_uv_map

print("UV-map used: ", p_uv_map)

if p_mat != "Default":
    sel_mask = []
    for mask in scene.items('mask'):
        mask_name = re.sub(r" ?\([^)]+\)", "", mask.name)
        if mask_name == p_mat:
            sel_mask = mask

    for child in sel_mask.childrenByType("imageMap"):
        if child.channel("effect").get() == "diffColor" or anyclip:
            clip_info = lx.eval('query layerservice clip.info ? %s' % child.index)
            clip_info = [int(i) for i in re.findall(r'\d+', clip_info)]
            clip_name = child.name
else:
    print("Default material detected - No texel density from clip will be attempted.")

# ---------------------------------------------------------------------------
# make new uvs --------------------------------------------------------------
# ---------------------------------------------------------------------------
lx.eval('tool.set uv.create on')
# lx.eval('tool.attr uv.create newmap false')
lx.eval('tool.attr uv.create newmap true')
lx.eval('tool.attr uv.create name {%s} ' % p_uv_map)

if barycentric:
    lx.eval('tool.setAttr uv.create proj barycentric')
else:
    lx.eval('tool.setAttr uv.create proj atlas')
    # lx.eval('tool.attr uv.create orient true')

lx.eval('tool.doApply')
lx.eval('tool.set uv.create off')

# ---------------------------------------------------------------------------
# clean up the uvs a bit ----------------------------------------------------
# ---------------------------------------------------------------------------
lx.eval('uv.orient auto')
lx.eval('!!uv.rectangle false 0.2 false false')

if not barycentric:
    lx.eval('tool.set uv.relax on')
    lx.eval('tool.attr uv.relax mode lscm')
    # lx.eval('tool.attr uv.relax mode adaptive')  # too slow
    lx.eval('tool.attr uv.relax iter 10')
    lx.eval('tool.doApply')
    lx.eval('tool.set uv.relax off')
    # lx.eval('uv.orient auto')

# lx.eval('uv.fit island true')
# lx.eval('uv.pack true true true auto 0.2 false false normalized 1001')
# ---------------------------------------------------------------------------
# Adjust UVs for texel density ----------------------------------------------
# ---------------------------------------------------------------------------
if clip_info:
    lx.eval('user.value texeldensity.sizeImage %s' % clip_info[0])
    print("Image:", clip_name, "   Image size (U):", clip_info[0])
else:
    print("No texture clip found! Using current Texel Density setting.")

if density:
    lx.eval('user.value texeldensity.sizeUV %s' % density)

lx.eval('texeldensity.set island all')

# if fix_overlap:      # Does not work often enough like this to bother with...
# lx.eval('select.uvOverlap %s false flipped:false zeroArea:false' % p_uv_map)
