import bpy, hashlib, struct, json

PATHS = {
    "candidate": r"C:\Users\antio\.codex\worktrees\mia-body-head-v06\win-overlay\asset\mia\blender\mia-production-body-head-v06\Mia_BodyHead_v06.blend",
    "head_study": r"C:\Users\antio\.codex\worktrees\mia-body-head-v06\win-overlay\asset\mia\blender\mia-head-refine-v06\Mia_HeadRefine_v06.blend",
    "v12": r"C:\Users\antio\.codex\worktrees\mia-body-head-v06\win-overlay\asset\mia\blender\mia-production-body-head-v06\iterations\v12-body-fit-frozen\Mia_BodyHead_v06_v12.blend",
}

def coord_hash(points):
    h = hashlib.sha256()
    for p in points:
        h.update(struct.pack("<3f", p[0], p[1], p[2]))
    return h.hexdigest()

def face_obj():
    return bpy.data.objects.get("MIA_V06_FACE_SKIN") or bpy.data.objects.get("Mia_Face_AnimeTopology") or bpy.data.objects.get("Face")

def body_obj():
    return bpy.data.objects.get("MIA_V06_BODY_SKIN") or bpy.data.objects.get("Mia_Body_Anatomy_Skin")

out = {}
for tag, path in PATHS.items():
    bpy.ops.wm.open_mainfile(filepath=path)
    f = face_obj()
    keys = list(f.data.shape_keys.key_blocks) if f and f.data.shape_keys else []
    out[tag] = {"path": bpy.data.filepath, "face_keys": [(k.name, len(k.data), coord_hash([tuple(v.co) for v in k.data])) for k in keys]}
    b = body_obj()
    out[tag]["body_count"] = len(b.data.vertices) if b else None

c = out["candidate"]["face_keys"]
s = out["head_study"]["face_keys"]
out["face_study_compare"] = {
    "candidate_key_count": len(c), "study_key_count": len(s),
    "all_44_name_count_hashes_equal": len(c) == len(s) == 44 and all(a == b for a, b in zip(c, s)),
}

bpy.ops.wm.open_mainfile(filepath=PATHS["candidate"])
cb = body_obj(); ccoords = [tuple(v.co) for v in cb.data.vertices]
excluded = [i for i, v in enumerate(cb.data.vertices) if any(("head" in g.name.lower() or "neck" in g.name.lower()) and any(x.group == g.index and x.weight > 0 for x in v.groups) for g in cb.vertex_groups)]
bpy.ops.wm.open_mainfile(filepath=PATHS["v12"])
vb = body_obj(); vcoords = [tuple(v.co) for v in vb.data.vertices]
keep = [i for i in range(min(len(ccoords), len(vcoords))) if i not in set(excluded)]
d = [max(abs(ccoords[i][j] - vcoords[i][j]) for j in range(3)) for i in keep]
out["body_v12_compare"] = {"candidate_vertices": len(ccoords), "v12_vertices": len(vcoords), "excluded_head_neck": len(excluded), "compared": len(keep), "max_abs_delta": max(d) if d else None, "mean_abs_delta": sum(d) / len(d) if d else None}
print(json.dumps(out, indent=2))
