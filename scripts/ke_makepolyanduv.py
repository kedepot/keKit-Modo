# python
# MakePolyAndUV 1.5 - Kjell Emanunuelsson 2019
# Just a quick script I replace the regular "Make Polygon" with to avoid the bad uvs and sewing that sometimes happen.
# Its not included in the menu since it turned out less useful than I hoped... ;>
# This script will use make polygon and then just atlas-uv the new poly -> a bit fewer broken uvs to deal with.
# To-do: check UV-edge-islands (how?) and sort them, pick the biggest one and sew to there ?

import lx


# print("-----------MakePolyAndUV------------")

layer_index = lx.eval('query layerservice layers ? selected')
layer_ID = lx.eval1('query layerservice layer.ID ? {%s}' % layer_index)

# EDGE SELECTION
sel_edges = lx.evalN('query layerservice edges ? selected')

if len(sel_edges) <= 1 :
    print("invalid selection? : Skipping UVs...")
    sys.exit()
else:
    sel_edges_poly = sel_edges[0]

# UV-MAP SELECTION
sel_uv_map = lx.eval1('vertMap.list type:txuv ?')

# if sel_uv_map == '_____n_o_n_e_____':
# print "You dont seem to have a UV map selected - Using uv map used by selected geo."

p = lx.eval('query layerservice edge.polyList ? %s' % sel_edges_poly)
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

if not p_uv_map: sys.exit(":  >>> Selected geometry does not seem to have a uv-map? <<<  ")
else: sel_uv_map = p_uv_map

# print("UV map: ", sel_uv_map)


# clear poly selections
lx.eval('select.drop polygon')
lx.eval('select.typeFrom edge')
# lx.eval('select.convert vertex')

# Make Poly & atlas map it
lx.eval('poly.make auto')
lx.eval('select.typeFrom polygon')
new_poly = lx.evalN('query layerservice polys ? selected')

if new_poly:
    new_poly_verts = lx.eval('query layerservice poly.vertList ? %s' % new_poly)

    lx.eval('tool.set uv.create on')
    lx.eval('tool.reset')
    lx.eval('tool.setAttr uv.create proj atlas')
    lx.eval('tool.attr uv.create world false')
    lx.eval('tool.attr uv.create name %s' % sel_uv_map)
    lx.eval('tool.doApply')
    lx.eval('tool.set uv.create off 0')

    # Cleanup selections
    lx.eval('select.drop vertex')
    lx.eval('select.drop edge')
    lx.eval('select.drop polygon')
    lx.eval('select.typeFrom edge')
