# python
# ke_vmap_weight 1.1 - Kjell Emanuelsson 2019-21
# 1.1 - Python3

import lx
import modo

u_arg = lx.arg()
weight = 0.0
print("---- Vmap Weight ------------------------------------------")

if u_arg:
    try:
        weight = float(u_arg)
    except Exception as e:
        print("No valid argument found - using default weight (0)\n", e)
        weight = 0.0

if weight:
    print("Using weight:", weight)

lx.eval('tool.set vertMap.setWeight on')
lx.eval('tool.setAttr vertMap.setWeight weight %s' % weight )
lx.eval('tool.doApply')
lx.eval('tool.set vertMap.setWeight off')