import bpy, hashlib, struct, json
C=r"C:\Users\antio\.codex\worktrees\mia-body-head-v06\win-overlay\asset\mia\blender\mia-production-body-head-v06\Mia_BodyHead_v06.blend"
H=r"C:\Users\antio\.codex\worktrees\mia-body-head-v06\win-overlay\asset\mia\blender\mia-head-refine-v06\astra-v09\Mia_Astra_Head_v09.blend"
V=r"C:\Users\antio\.codex\worktrees\mia-body-head-v06\win-overlay\asset\mia\blender\mia-production-body-head-v06\iterations\v12-body-fit-frozen\Mia_BodyHead_v06_v12.blend"
def hh(a):
 h=hashlib.sha256()
 for p in a:h.update(struct.pack('<3f',*p))
 return h.hexdigest()
def op(p): bpy.ops.wm.open_mainfile(filepath=p)
def f(): return bpy.data.objects.get('MIA_V06_FACE_SKIN') or bpy.data.objects.get('Mia_Face_AnimeTopology') or bpy.data.objects.get('Face')
def b(): return bpy.data.objects.get('MIA_V06_BODY_SKIN') or bpy.data.objects.get('Mia_Body_Anatomy_Skin')
def keys(p):
 op(p); return [(k.name,len(k.data),hh([tuple(v.co) for v in k.data])) for k in f().data.shape_keys.key_blocks]
c=keys(C); h=keys(H); op(C); bo=b(); cc=[tuple(v.co) for v in bo.data.vertices]; ex=[i for i,v in enumerate(bo.data.vertices) if any(('head' in g.name.lower() or 'neck' in g.name.lower()) and any(x.group==g.index and x.weight>0 for x in v.groups) for g in bo.vertex_groups)]; op(V); bv=b(); vv=[tuple(v.co) for v in bv.data.vertices]; keep=[i for i in range(min(len(cc),len(vv))) if i not in set(ex)]; ds=[max(abs(cc[i][j]-vv[i][j]) for j in range(3)) for i in keep]
print(json.dumps({'candidate':C,'astra_head':H,'v12':V,'face44':len(c)==len(h)==44 and all(a==z for a,z in zip(c,h)),'face_key_hashes':[(a[0],a[2],z[2],a[2]==z[2]) for a,z in zip(c,h)],'body_v12':{'excluded_head_neck':len(ex),'compared':len(keep),'max_abs_delta':max(ds),'mean_abs_delta':sum(ds)/len(ds)}}))
