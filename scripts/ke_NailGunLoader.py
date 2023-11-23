#python#

# NailGun Loader 0.6b - Kjell Emanuelsson 2018-21
# Sets item for NailGun to use - pick item and run loader - then use nailgun
# 0.6 - Python3
# Update 0.5 : Added slots
# Note: for Loader 1.0: Presets/kitloading? in pop up form, with icons etc. ETA: never?

verbose = False
clearslot = False
loadslot = False
u_args = lx.args()
slotnr = []

for i in range(len(u_args)):
    if "load" in u_args:
        loadslot = True
    elif "clear" in u_args:
        clearslot = True

for nr in u_args:
    try:
        slotnr = int(nr)
    except ValueError:
        continue


def load_nailgun(item, item_name):
    lx.eval('user.value ke_nailgun.item {%s}' % item)
    lx.eval('user.value ke_nailgun.itemName {%s}' % item_name)


def fill_slot(item, item_name, nr):
    slot, slot_name = "ke_nailgun.itemSlot"+str(nr), "ke_nailgun.itemSlotName"+str(nr)
    lx.eval('user.value {%s} {%s}' % (slot, item))
    lx.eval('user.value {%s} {%s}' % (slot_name, item_name))


def load_slot(nr):
    slot, slot_name = "ke_nailgun.itemSlot"+str(nr), "ke_nailgun.itemSlotName"+str(nr)
    item = lx.eval('user.value {%s} ?' % slot)
    item_name = lx.eval('user.value {%s} ?' % slot_name)
    return item, item_name


def clear_slot(nr):
    slot, slot_name = "ke_nailgun.itemSlot"+str(nr), "ke_nailgun.itemSlotName"+str(nr)
    lx.eval('user.value {%s} {%s}' % (slot, "None"))
    lx.eval('user.value {%s} {%s}' % (slot_name, "None"))


def check_slots(count):
    slotlist = []
    for n in range(1, count+1):
        slot = "ke_nailgun.itemSlot"+str(n)
        slotlist.append(lx.eval('user.value {%s} ?' % slot))
    return slotlist


if verbose:
    print("Clear, load, slotnr:", clearslot, loadslot, slotnr)


# Loader - Assign item to instance

if clearslot:
    clear_slot(slotnr)
    sys.exit()

elif loadslot:  # can load blanks. fine?
    item = load_slot(slotnr)
    load_nailgun(item[0], item[1])
    lx.eval('select.item {%s} set' % item[0])
    sys.exit()


item = lx.eval('query sceneservice selection ? mesh')

if not item:
    item = lx.eval('query sceneservice selection ? meshInst ')

if item:

    item_name = lx.eval('query sceneservice mesh.name ? {%s}' % item)

    slot_list = check_slots(6)  # for 6 slots
    index_nr = 1
    full_check = 1

    for index in slot_list:
        if index == "None":
            fill_slot(item, item_name, index_nr)
            load_nailgun(item, item_name)
            sys.exit()
        else:
            index_nr += 1
        full_check += 1

    if full_check >= 6:
        print("Nailgun: --- Magazine Full. CTRL-LMB click 'Use' to empty slot.---")
        sys.exit()

    if verbose:
        print("Item Loaded for NailGun: ", item_name, "(%s)" % item, "Mag:", full_check)

else:
    sys.exit(": --- Selection Error: Mesh Item not selected. --- ")
