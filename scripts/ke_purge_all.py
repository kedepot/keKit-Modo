# python

# Purge ALL 1.0 Kjell Emanuelsson 2019.
# Macro script that just runs all the other purge scripts in the kit.

print(" >>> ---------------  Purge ALL -------------- <<<")
lx.eval("!!@ke_purge_empty_layers.py")
lx.eval("!!@ke_purge_images.py")
lx.eval("!!@ke_purge_materials.py")
lx.eval("!!@ke_purge_tlocs.py")
