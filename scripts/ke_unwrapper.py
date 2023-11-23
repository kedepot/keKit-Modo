# python
# Unwrapper 2.1 - Kjell Emanunuelsson 2019-21
# 2.1 - Python 3 fixes
# (Using a minor mod on the uv-reading py-api example from the foundry!)
# Slightly less simple macro to Unwrap selected geo (edges or polys) and relax a little and rectangle if possible
# Arguments: adaptive (relax), both (lscm + adaptive relax), rect (rectangle), nopack (skips pack),
#            selection (selected poly only), to_side (places uv outside 0-1 UV space,
#            stepping leftwards if the udim is occupied). u_pos (changes to_side to go right),
#            v_neg (to_side goes down), v_pos (to_side goes up).

import lx
import lxifc
import math

adaptive = False
both = False
rect = False
nopack = False
to_side = False  # Places packed uv to UDIM U-1
side = 9  # clock direction for to_side placement ;>
selection = False  # Works best with adaptive too

u_args = lx.args()
for i in range(len(u_args)):
    if "adaptive" in u_args:
        adaptive = True
    if "both" in u_args:
        both = True
    if "rect" in u_args:
        rect = True
    if "nopack" in u_args:
        nopack = True
    if "selection" in u_args:
        selection = True
    if "to_side" in u_args:
        to_side = True
    if "u_pos" in u_args:
        side = 3
    elif "v_neg" in u_args:
        side = 6
    elif "v_pos" in u_args:
        side = 12


class uvVisitor(lxifc.Visitor):
    def __init__(self, polyAccessor, mapID):
        self.polyAccessor = polyAccessor
        self.mapID = mapID
        self.storage = lx.object.storage('f', 2)
        self.values = []

    def vis_Evaluate(self):
        nVerts = self.polyAccessor.VertexCount()
        for eachVert in range(nVerts):
            vertID = self.polyAccessor.VertexByIndex(eachVert)
            if self.polyAccessor.MapEvaluate(self.mapID, vertID, self.storage):
                currentValue = self.storage.get()
                if currentValue not in self.values:
                    self.values.append(currentValue)


def get_uv_positions(uv_map):
    layerService = lx.service.Layer()
    layerScanObject = layerService.ScanAllocate(lx.symbol.f_LAYERSCAN_PRIMARY)
    localizedMesh = layerScanObject.MeshBase(0)
    polyAccessor = localizedMesh.PolygonAccessor()
    mapAccessor = localizedMesh.MeshMapAccessor()
    mapAccessor.SelectByName(lx.symbol.i_VMAP_TEXTUREUV, uv_map)
    mapID = mapAccessor.ID()
    visitorInstance = uvVisitor(polyAccessor, mapID)
    polyAccessor.Enumerate(lx.symbol.iMARK_ANY, visitorInstance, 0)
    layerScanObject.Apply()

    # Geting a list of occupied udims
    udim = []
    for uv in visitorInstance.values:
        if side == 9 or side == 3:
            udim.append(int(math.floor(uv[0])))
        elif side == 6 or side == 12:
            udim.append(int(math.floor(uv[1])))

    # returning the next unoccupied udim
    udim = sorted(udim)
    if side == 3:
        return udim[-1] + 1
    elif side == 9:
        return udim[0] - 1
    elif side == 12:
        return udim[-1] + 1
    elif side == 6:
        return udim[0] - 1


print("-----------Unwrapper------------")

# -----------------------------------------------------------------
# Selection
# -----------------------------------------------------------------
if not selection:
    lx.eval('select.convert vertex')
    lx.eval('select.connect')
    lx.eval('select.convert polygon')
    lx.eval('hide.unsel')
    lx.eval('select.typeFrom edge')

else:
    if lx.eval('query layerservice selmode ?') == "polygon":
        lx.eval('hide.unsel')
    else:
        sys.exit(": Polygon Selection only - script aborted. ")

# Use the correct UV map (if none exists the default "Texture" UV will be created/used)
sel_uv_map = lx.eval1('vertMap.list type:txuv ?')
if sel_uv_map == '_____n_o_n_e_____':
    sel_uv_map = "Texture"
    print("You dont seem to have a UV map selected - using default 'Texture' UV map. ")
else:
    print("Using UV map", sel_uv_map)

# -----------------------------------------------------------------
# Unwrap
# -----------------------------------------------------------------
lx.eval('tool.set uv.unwrap on')
lx.eval('tool.attr uv.unwrap iter 128')
lx.eval('tool.attr uv.unwrap gaps 0.2')
lx.eval('tool.attr uv.unwrap project planar')
lx.eval('tool.attr uv.unwrap pinning u')
lx.eval('tool.attr uv.unwrap axis y')
lx.eval('tool.attr uv.unwrap angle 0.0')
lx.eval('tool.attr uv.unwrap seal false')
lx.eval('tool.doApply')
lx.eval('tool.set uv.unwrap off')
lx.eval('select.typeFrom polygon')

# -----------------------------------------------------------------
# Relax
# -----------------------------------------------------------------
lx.eval('tool.set uv.relax on')

if not adaptive or both:
    lx.eval('tool.attr uv.relax mode lscm')
    lx.eval('tool.attr uv.relax iter 48')
    lx.eval('tool.doApply')

if adaptive or both:
    lx.eval('tool.set uv.relax on')
    lx.eval('tool.setAttr uv.relax mode adaptive')
    lx.eval('tool.attr uv.relax iter 36')  # too slow on higher iter
    lx.eval('tool.doApply')

lx.eval('tool.set uv.relax off')

# -----------------------------------------------------------------
# Cleanup & Finish
# -----------------------------------------------------------------
# Rectangle
if rect: lx.eval('!!uv.rectangle true 0.1 false false')

# Orient UV
lx.eval('uv.orient auto')
lx.eval('tool.doApply')

# Pack UVS
if not nopack:

    if to_side:
        uv_side = get_uv_positions(sel_uv_map)
        if not uv_side:
            uv_side = -1
        print("Using UDIM Space:", uv_side)
        if side == 3 or side == 9:
            lx.eval('uv.pack true true true auto 0.1 false false manual 1001 {%s} 0.0 1.0 1.0 1 1' % uv_side)
        else:
            lx.eval('uv.pack true true true auto 0.1 false false manual 1001 0.0 {%s} 1.0 1.0 1 1' % uv_side)

    else:
        lx.eval('uv.pack true true true auto 0.1 false false normalized 1001 0.0 0.0 1.0 1.0 1 1')

# Select Result
lx.eval('unhide')
lx.eval('select.drop vertex')
lx.eval('select.drop edge')
lx.eval('select.typeFrom polygon')
