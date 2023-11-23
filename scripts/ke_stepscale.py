# python

# ke_stepscale v3.2  (simplified) Kjell Emanuelsson 2017-21
# 3.2 - Python3 fixes
# 3.1 - Fixed so that it -actually- only works with scaletool
#
# Doubles or halves size - When scaletool is active.
# Doubles by default. add "half" as argument to half size selection: "ke_stepscale.py half"
# (will not keep element scale values - always at 100% in tool)
#
# Suggest mapping contextual hotkey to "transform" tool
# (weirdly same mapping for scaling - will only work when scale tool is active still)
# Note: if mapped to mouse btns = modo jankiness - req perfectly still mouse...

uArgs = lx.args()
dbl = True
half = False
activeTool = "None"

if "half" in uArgs:
    half = True
    dbl = False

if lx.eval('tool.set TransformScale ?') == "on":
    activeTool = "Transform"

elif lx.eval('tool.set TransformScaleItem ?') == "on":
    activeTool = "TransformScaleItem"

elif lx.eval('tool.set TransformScale ?') == "off":
    sys.exit()

elif lx.eval('tool.set TransformScaleItem ?') == "off":
    sys.exit()

else:
    sys.exit()


if activeTool == "Transform":

    if dbl:
        setScale = 2.0
    else:
        setScale = 0.5

    lx.eval('tool.setAttr xfrm.transform SX %s' % setScale)
    lx.eval('tool.setAttr xfrm.transform SY %s' % setScale)
    lx.eval('tool.setAttr xfrm.transform SZ %s' % setScale)
    lx.eval('tool.doApply')
    lx.eval('tool.reset')

elif activeTool == "TransformScaleItem"	:

    sX = lx.eval('transform.channel scl.X ?')
    sY = lx.eval('transform.channel scl.Y ?')
    sZ = lx.eval('transform.channel scl.Z ?')

    if dbl:
        sX, sY, sZ = sX * 2, sY * 2, sZ * 2
    else:
        sX, sY, sZ = sX * 0.5, sY * 0.5, sZ * 0.5

    lx.eval('transform.channel scl.X %s' % sX)
    lx.eval('transform.channel scl.Y %s' % sY)
    lx.eval('transform.channel scl.Z %s' % sZ)
    lx.eval('tool.doApply')

else:
    sys.exit("Unexpected - Quitting StepScaleTool")
