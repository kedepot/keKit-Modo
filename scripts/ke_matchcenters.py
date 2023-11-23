# python

# MatchCenters 1.0 Kjell Emanuelsson 2018
# Simple script that matches center rotation & position of your selected item(s) ***to the LAST selected item***

import lx
import modo

scene = modo.scene.current()
sel_items = scene.selected

if len(sel_items) < 2:
    sys.exit(": \n Selection Error: Not enough items selected - At least 2 needed. -- Aborting Script -- ")

match_item = sel_items.pop(-1)

# match rot & pos
for item in sel_items:
    lx.eval('select.drop item')
    scene.select(item)
    scene.select(match_item, add=True)
    lx.eval('item.match cen pos')
    lx.eval('item.match cen rot')

# select matched items
for item in sel_items:
    scene.select(item, add=True)

scene.deselect(match_item)
lx.eval('tool.set TransformMoveItem on')
