# python

# uv_planar_selected 1.0 - Kjell Emanuelsson 2018.
# Fits and fires front project to selection using workPlane and relaxes uvs
# notes:
# - Stores original relax values and restores them.
# - Wp rotation is to avoid flipped uvs (Y up)

import lx

# Fit WP
lx.eval('workPlane.fitSelect')
lx.eval('workPlane.rotate 0 180.0')

# Initiate UV Planar projection
lx.eval('tool.set uv.create on')
lx.eval('tool.attr uv.create proj planar')
lx.eval('tool.attr uv.create axis 1')
lx.eval('tool.doApply')


# -----------------------------------------------------------------
# start conformal smooth (for distribution)
# -----------------------------------------------------------------

lx.eval('tool.set uv.relax on')
lx.eval('tool.attr uv.relax mode lscm')

# grab current settings
og_adaptive_iter = lx.evalN('tool.attr uv.relax iter ?')
og_adaptive_boundary = lx.eval('tool.attr uv.relax boundary ?')

# run conformal smooth
lx.eval('tool.attr uv.relax iter 16')
lx.eval('tool.attr uv.relax boundary smooth')
lx.eval('tool.doApply')

# restore adaptive settings
lx.eval('tool.attr uv.relax iter {%s}' % og_adaptive_iter)
lx.eval('tool.attr uv.relax boundary {%s}' % og_adaptive_boundary)

lx.eval('tool.set uv.relax off')

# -----------------------------------------------------------------
# start adaptive smooth (for better boundary)
# -----------------------------------------------------------------

lx.eval('tool.set uv.relax on')
lx.eval('tool.attr uv.relax mode adaptive')

# grab current settings
og_adaptive_iter = lx.evalN('tool.attr uv.relax iter ?')
og_adaptive_area = lx.evalN('tool.attr uv.relax area ?')
og_adaptive_boundary = lx.eval('tool.attr uv.relax boundary ?')

# run adaptive smooth
lx.eval('tool.attr uv.relax iter 48')
lx.eval('tool.attr uv.relax area 0.1')
lx.eval('tool.attr uv.relax boundary smooth')
lx.eval('tool.doApply')

# restore adaptive settings
lx.eval('tool.attr uv.relax iter {%s}' % og_adaptive_iter)
lx.eval('tool.attr uv.relax area {%s}' % og_adaptive_area)
lx.eval('tool.attr uv.relax boundary {%s}' % og_adaptive_boundary)

lx.eval('tool.set uv.relax off')

# Finish / reset WP
lx.eval('uv.orient auto')
lx.eval('uv.fit entire true')
lx.eval('workPlane.reset')
