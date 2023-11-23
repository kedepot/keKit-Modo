#python

# offsetwp2sel 1.2 - Kjell Emanuelsson 2018-21
# 1.2 - Python3
# 1.1 - You can now offset the workplane even if you have not fitted it.
#
# Offsets an active work plane to the average position of any element(s) selected.  
# (useful for wp alignments, rotation/unrotation scripts and whatnot)

verbose = False


def fn_avgpos(vertlist):
	vX, vY, vZ = [], [], []
	for v in vertlist:
		i = lx.eval('query layerservice vert.wdefpos ? %s' % v)
		vX.append(i[0]), vY.append(i[1]), vZ.append(i[2])
	total = len(vertlist)
	return sum(vX) / total, sum(vY) / total, sum(vZ) / total	


selcount = 0
selmode = lx.eval('query layerservice selmode ?')

if selmode == "vertex":
	sel = lx.eval('query layerservice verts ? selected')
	if sel != 0:
		pos = fn_avgpos(sel)
	else:
		sys.exit(": --- No verts selected. Aborting. ---")
	
	if verbose:
		selcount = len(sel)

elif selmode == "edge":
	
	selcount = lx.eval1('query layerservice edge.N ? selected')
	
	if selcount == 1:  # string/list return from index query (1 edge does not work otherwise)
		sel = [lx.eval('query layerservice edges ? selected')]
	else:
		sel = lx.eval('query layerservice edges ? selected')
	
	if selcount != 0:  # and then we can get the vertlist
		verts = []
		for i in sel:
			verts.extend(lx.evalN('query layerservice edge.vertList ? {%s}' % i))
		verts = list(set(verts))
		pos = fn_avgpos(verts)
		
	else:
		sys.exit(": --- No edges selected. Aborting. ---")

elif selmode == "polygon":

	selcount = lx.eval1('query layerservice poly.N ? selected')
	
	if selcount == 1:  # string/list int return from index query (1 poly int return gets wrong vertlist...)
		sel = [lx.eval('query layerservice polys ? selected')]
	else:
		sel = lx.eval('query layerservice polys ? selected')
	
	if selcount != 0:  # and then we can get the vertlist
		verts = []
		for i in sel:
			polyverts = lx.evalN('query layerservice poly.vertList ? {%s}' % i)
			verts.extend(polyverts)
		pos = fn_avgpos(verts)
	else:
		sys.exit(": --- No polys selected. Aborting. ---")
			
else:
	sys.exit(": --- Invalid selection mode: Please select Verts, Edges or Polys. Aborting. ---")


if verbose:
	print("Selmode:", selmode, "   Count:", selcount, "   Index:", sel, "   Pos:", pos)

# offset wp (using wdef vert pos on all selections to avoid item transform issues)
lx.eval('workplane.edit %s %s %s' % (pos[0], pos[1], pos[2]))
