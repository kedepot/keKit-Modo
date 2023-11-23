# python

# TripleSplitSpin (and spikey!) v1.4 - Kjell Emanuelsson 2018-21
# My take on Seneca Menards "triple or spin" script.
# Usage:
# VERT mode:  1 vert selected - *FAN-SPLITS* between verts on connected polys
#             2 (or more!) verts selected - *SPLITS* the geo between verts in the sequence you select them in.
# EDGE mode:     *SPINS* selected edge(s)
# POLYGON mode:  *TRIPLES* selected polys (if quads or ngons) -or- *SPINS* ONE selected quad if already tripled.
# SPIKEY special:  Runs *SPIKEY* on selected polys - If you select POLY(s) and ALSO convert the selection to VERTS,
#                  so the vertex selection consists of the same verts the polygon(s) consists of.
#                  The script leaves you with the new spikey verts selected with the push tool on (just click&drag).
#                  (If not needed, just set spikey_mode to False below.)
# ITEM mode etc : TRIPLES mesh (same as running the regular triple command)
# Symmetry support : Yup
#
# 1.4 - Python3 fixes
# 1.3 - Added an alternate split version that just uses the default behaviour
#			   that connects (splits) all the verts sharing a polygon.

import lx

u_args = lx.args()

spikey_mode = True
done = False
sym_verts = []
symmetry_axis = 0
og_verts = []

if "connectsplit" in u_args:
    connectsplit = True
else:
    connectsplit = False


def indexfiltersort(commalist):
    result = str(commalist)
    result = [int(''.join(filter(str.isdigit, index))) for index in result.split(",")]
    return result


def zigzagpair(inputlist):
    result = []
    while len(inputlist) >= 2:
        result_pair = inputlist[0], inputlist[1]
        inputlist.pop(0)
        result.append(result_pair)
    return result


def splitpairs(pairlist):
    for pair in pairlist:
        lx.eval('select.element %s %s set %s' % (sel_layer, 'vertex', pair[0]))
        lx.eval('select.element %s %s add %s' % (sel_layer, 'vertex', pair[1]))
        lx.eval('!!poly.split')


def splitpolyfan(firstvert):
    poly_verts = []
    polys = lx.eval('query layerservice vert.polyList ? {%s}' % firstvert)

    for poly in polys:
        if not lx.eval('query layerservice poly.hidden ? {%s}' % poly):
            poly_verts.extend(lx.eval('query layerservice poly.vertList ? {%s}' % poly))

    con_verts = list(lx.eval('query layerservice vert.vertList ? {%s}' % firstvert))
    con_verts.append(int(firstvert))
    con_verts = [v for v in poly_verts if v not in con_verts]

    for v in con_verts:
        lx.eval('select.element %s %s set %s' % (sel_layer, 'vertex', firstvert))
        lx.eval('select.element %s %s add %s' % (sel_layer, 'vertex', v))
        lx.eval('!!poly.split')


def spikey(input_sel_polys, input_sel_verts):
    poly_verts = []
    for poly in input_sel_polys:
        poly_verts.extend(lx.evalN('query layerservice poly.vertList ? {%s}' % poly))

    poly_verts = list(set(poly_verts))

    if sorted(poly_verts) == sorted(input_sel_verts):
        lx.eval('select.typeFrom polygon')
        lx.eval('tool.set poly.spikey on')
        lx.eval('tool.setAttr poly.spikey factor 0.0')
        lx.eval('tool.doApply')
        lx.eval('select.typeFrom vertex')
        return True
    else:
        return False


# -------------------------------------------------------------------------
# Initial scene check
# -------------------------------------------------------------------------
sel_layer = lx.eval('query layerservice layers ? selected')
sel_mode = lx.eval('query layerservice selmode ?')

if lx.eval('symmetry.state ?'):
    symmetry_mode = True
    symmetry_axis = lx.eval('symmetry.axis ?')
else:
    symmetry_mode = False


# -------------------------------------------------------------------------
# Vertex Mode
# -------------------------------------------------------------------------
if sel_mode == "vertex":

    sel_verts = lx.evalN('query layerservice verts ? selected')
    sel_count = len(sel_verts)

    if sel_count == 1:
        splitpolyfan(sel_verts[0])

    elif sel_count >= 2 and connectsplit:
        lx.eval('!!poly.split')

    elif sel_count >= 2 and not connectsplit:
        fantriple = False
        sel_verts = [int(i) for i in sel_verts]

        if spikey_mode:
            og_verts = lx.evalN('query layerservice verts ? all')
            sel_polys = lx.evalN('query layerservice polys ? selected')
            if sel_polys:
                done = spikey(sel_polys, sel_verts)

        if symmetry_mode and not done:
            first_symvert = lx.eval('query layerservice vert.symmetric ? {%s}' % sel_verts[0])
            lx.eval('select.symmetryState 0')

            if sel_count == 2 and first_symvert == sel_verts[1]:
                fantriple = True

            # Check to cover situations where symmetry is "broken" and do un-symmetric op instead
            elif first_symvert:
                sel_verts_sym = sel_verts[::2]
                sym_verts = [i for i in sel_verts if i not in sel_verts_sym]
                sel_verts = sel_verts_sym
            else:
                symmetry_mode = False  # "broken"

        # main vertex mode split op
        if fantriple:
            splitpolyfan(sel_verts[0])
            splitpolyfan(sel_verts[1])

        elif not done:
            vertex_pairs = zigzagpair(sel_verts)
            splitpairs(vertex_pairs)

            if symmetry_mode:
                vertex_pairs = zigzagpair(sym_verts)
                splitpairs(vertex_pairs)

    else:
        lx.eval('!!poly.triple')

    lx.eval('select.drop vertex')


# -------------------------------------------------------------------------
# Edge Mode
# -------------------------------------------------------------------------
elif sel_mode == "edge":

    if lx.evalN('query layerservice edges ? selected'):
        lx.eval('!!edge.spinQuads')
    else:
        lx.eval('!!poly.triple')


# -------------------------------------------------------------------------
# Polygon Mode
# -------------------------------------------------------------------------
elif sel_mode == "polygon":

    triple_only = False
    sel_polys = lx.evalN('query layerservice polys ? selected')

    if spikey_mode:
        og_verts = lx.evalN('query layerservice verts ? all')
        sel_verts = lx.evalN('query layerservice verts ? selected')
        if sel_verts:
            done = spikey(sel_polys, sel_verts)

    if not done:

        for p in sel_polys:
            if lx.eval1('query layerservice poly.numVerts ? {%s}' % p) > 3:
                triple_only = True
                break

        if not triple_only:

            lx.eval('select.convert edge')
            lx.eval('!!select.contract')
            lx.eval('!!select.edge remove poly equal 1')

            if symmetry_mode:  # removing edges if on the symmetry axis
                sel_edges = lx.evalN('query layerservice edges ? selected')
                for e in sel_edges:
                    edge_verts = indexfiltersort(e)
                    vpos1 = lx.evalN('query layerservice vert.wdefpos ? {%s}' % edge_verts[0])
                    vpos2 = lx.evalN('query layerservice vert.wdefpos ? {%s}' % edge_verts[1])
                    if vpos1[symmetry_axis] == 0 and vpos2[symmetry_axis] == 0:
                        lx.eval('select.element %s %s remove %s %s' % (sel_layer, 'edge', edge_verts[0], edge_verts[1]))

            try:
                lx.eval('!!edge.spinQuads')
            except Exception as e:
                print(e)
                pass
                # coz error popup block for the case with a fully connected all tri mesh selection only works with try?

            lx.eval('!!select.drop edge')
            lx.eval('!!select.typeFrom polygon')

        else:
            lx.eval('!!poly.triple')


# -------------------------------------------------------------------------
#  ..and the rest - mode
# -------------------------------------------------------------------------
else:
    # If in item mode etc, just operate like the triple command would
    lx.eval('!!poly.triple')


# Cleanup - restore symmetry
if symmetry_mode and not done:
    lx.eval('select.symmetryState 1')


# For spikey: leave off with push-control of new spike-verts
if spikey_mode and done:
    new_verts = lx.evalN('query layerservice verts ? all')
    spikey_verts = [v for v in new_verts if v not in og_verts]

    for v in spikey_verts:
        lx.eval('select.element %s %s add %s' % (sel_layer, 'vertex', v))

    lx.eval('tool.set xfrm.push on')
    lx.eval('tool.setAttr xfrm.push dist 0.0')
    lx.eval('tool.doApply')
