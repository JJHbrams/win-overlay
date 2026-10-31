import bpy, hashlib, json, struct, sys
from pathlib import Path

OUT = Path(__file__).parent / "static-v11-independent.json"
V11 = Path(__file__).parents[0].parent / "Mia_Static_DetailedHair_v11.blend"
V09 = Path(r"C:\Users\antio\.codex\worktrees\mia-head-refine-v06\win-overlay\asset\mia\blender\mia-head-refine-v06\astra-v09\Mia_Astra_Head_v09.blend")
SOURCE = Path(r"D:\ai\Mia3DWork\model-v02\hair-surface-stage\Mia_HairSurface_v06.blend")

def sha(p):
 h=hashlib.sha256();
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(1048576),b""): h.update(b)
 return h.hexdigest()
def dh(points):
 h=hashlib.sha256()
 for p in points: h.update(struct.pack("<3f", *p))
 return h.hexdigest()
def obj(names):
 for n in names:
  if bpy.data.objects.get(n): return bpy.data.objects[n]
 return None
def mesh(o):
 d=o.data; topo=hashlib.sha256(repr([tuple(p.vertices) for p in d.polygons]).encode()).hexdigest()
 uv=hashlib.sha256(repr([(u.name,[(round(x.uv.x,8),round(x.uv.y,8)) for x in u.data]) for u in d.uv_layers]).encode()).hexdigest()
 return {"vertices":len(d.vertices),"polygons":len(d.polygons),"topology_hash":topo,"uv_hash":uv,"uv_layers":[u.name for u in d.uv_layers],"coords_hash":dh([tuple(v.co) for v in d.vertices])}
def capture(path):
 bpy.ops.wm.open_mainfile(filepath=str(path)); f=obj(["MIA_V06_FACE_SKIN","Mia_Face_AnimeTopology","Face"]); b=obj(["MIA_V06_BODY_SKIN","Mia_Body_Anatomy_Skin","Body"])
 keys=list(f.data.shape_keys.key_blocks) if f and f.data.shape_keys else []
 hair=[{"object":o.name,"mesh":o.data.name,"vertices":len(o.data.vertices),"polygons":len(o.data.polygons),"materials":[m.name for m in o.data.materials]} for o in bpy.data.objects if o.type=="MESH" and ("hair" in o.name.lower() or "miahair" in o.name.lower())]
 return {"filepath":bpy.data.filepath,"body":mesh(b) if b else None,"face":mesh(f) if f else None,"face_keys":[(k.name,len(k.data),dh([tuple(v.co) for v in k.data])) for k in keys],"hair_owners":hair,"images":{"count":len(bpy.data.images),"packed":sum(1 for i in bpy.data.images if i.packed_file),"external_missing":[i.filepath for i in bpy.data.images if i.filepath and not i.packed_file and not Path(bpy.path.abspath(i.filepath)).exists()]},"linked_libraries":[l.filepath for l in bpy.data.libraries]}

result={"inputs":{"v11":str(V11),"v09":str(V09),"source":str(SOURCE),"sha_before":{"v11":sha(V11),"v09":sha(V09),"source":sha(SOURCE)}},"v11":capture(V11),"v09":capture(V09)}
result["comparison"]={"body_equal":result["v11"]["body"]==result["v09"]["body"],"face_equal":result["v11"]["face"]==result["v09"]["face"],"face44_equal":len(result["v11"]["face_keys"])==len(result["v09"]["face_keys"])==44 and result["v11"]["face_keys"]==result["v09"]["face_keys"],"v11_hair_count":len(result["v11"]["hair_owners"]),"v11_hair_datablocks":len(set(x["mesh"] for x in result["v11"]["hair_owners"]))}
result["inputs"]["sha_after"]={"v11":sha(V11),"v09":sha(V09),"source":sha(SOURCE)}; result["inputs"]["unchanged"]=(result["inputs"]["sha_before"]==result["inputs"]["sha_after"]); result["scope_note"]="Static ownership/topology/UV presence only; no pose/deformation test and no ART PASS."
OUT.write_text(json.dumps(result,indent=2),encoding="utf-8"); print(json.dumps(result,indent=2))
