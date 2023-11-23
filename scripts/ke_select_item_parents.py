# python#

# Select Item Parents v1.0 - Kjell Emanuelsson 2019.

import modo

scene = modo.scene.current()

parent_list = []

for item in scene.selected:
    parent = item.itemGraph(graphType='parent').forward()
    if parent:
        parent_list.append(parent[0])

if parent_list:
    scene.select(parent_list)
