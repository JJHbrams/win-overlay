"""Read-only exact-native topology for a finite connected surface patch."""
from pathlib import Path
import hashlib,json
import bpy,numpy as np
P=Path(__file__).resolve().parent
d=json.loads((P/'current-body-audit.json').read_text())
native=Path(d['native'])
assert hashlib.sha256(native.read_bytes()).hexdigest()==d['sha256']
bpy.ops.wm.open_mainfile(filepath=str(native),use_scripts=False)
ob=bpy.data.objects['MIA_V27_SharedHeadBody'];me=ob.data
me.calc_loop_triangles()
np.savez_compressed(P/'posed-target/control-topology.npz',
    triangles=np.asarray([t.vertices[:] for t in me.loop_triangles],np.int32),
    triangle_materials=np.asarray([me.polygons[t.polygon_index].material_index for t in me.loop_triangles],np.int32),
    loop_vertices=np.asarray([l.vertex_index for l in me.loops],np.int32),
    polygon_sizes=np.asarray([p.loop_total for p in me.polygons],np.int32),
    polygon_materials=np.asarray([p.material_index for p in me.polygons],np.int32))
assert len(me.vertices)==4647 and hashlib.sha256(native.read_bytes()).hexdigest()==d['sha256']
print('CONTROL_TOPOLOGY_READ_ONLY_DONE',len(me.vertices),len(me.polygons),len(me.loop_triangles),flush=True)
