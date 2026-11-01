"""Bounded M5 look: measured lid UV crease and lower edge, no geometry/bitmap edits."""
import argparse,sys,json,hashlib
from pathlib import Path
from collections import Counter,defaultdict
import bpy,numpy as np
ROOT=Path(__file__).resolve().parent
V22=ROOT.parents[2]
SKIN='MIA_V14_SculptedSkin'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def snapshot():
    result={}
    for o in bpy.data.objects:
        if o.type!='MESH':continue
        m=o.data;h=hashlib.sha256()
        for v in m.vertices:h.update(np.asarray(v.co,np.float32).tobytes())
        for p in m.polygons:h.update(np.asarray(p.vertices,np.int32).tobytes());h.update(str(p.material_index).encode())
        for uv in m.uv_layers:
            h.update(uv.name.encode())
            for v in uv.data:h.update(np.asarray(v.uv,np.float32).tobytes())
        if m.shape_keys:
            for k in m.shape_keys.key_blocks:
                h.update(k.name.encode());h.update(str(k.value).encode())
                for v in k.data:h.update(np.asarray(v.co,np.float32).tobytes())
        h.update(np.asarray(o.matrix_world,np.float32).tobytes())
        result[o.name]=h.hexdigest()
    return result

def measured_lid_uv(skin):
    m=skin.data;P=np.array([v.co[:] for v in m.shape_keys.key_blocks[0].data])
    counts=Counter(tuple(sorted((f.vertices[i],f.vertices[(i+1)%len(f.vertices)]))) for f in m.polygons for i in range(len(f.vertices)))
    ad=defaultdict(set)
    for (a,b),count in counts.items():
        if count==1:ad[a].add(b);ad[b].add(a)
    uv=m.uv_layers['UVMap'];uvs=defaultdict(list)
    for f in m.polygons:
        if f.material_index==7:
            for li in f.loop_indices:uvs[m.loops[li].vertex_index].append(uv.data[li].uv[:])
    todo=set(ad);result=[]
    while todo:
        stack=[min(todo)];group=set()
        while stack:
            i=stack.pop()
            if i in group:continue
            group.add(i);stack.extend(ad[i])
        todo-=group;c=P[list(group)].mean(0)
        if not(len(group)>40 and .01<abs(c[0])<.06 and c[1]>.035 and 1.525<c[2]<1.555):continue
        inner=min(group,key=lambda i:abs(P[i,0]));outer=max(group,key=lambda i:abs(P[i,0]));paths=[]
        for first in ad[inner]:
            path=[inner,first]
            while path[-1]!=outer:
                nx=ad[path[-1]]-{path[-2]};assert len(nx)==1
                path.append(next(iter(nx)));assert len(path)<1000
            paths.append(path)
        paths.sort(key=lambda ids:P[ids,2].mean(),reverse=True)
        row={'side':int(np.sign(c[0])),'inner_uv':np.mean(uvs[inner],axis=0).tolist(),'outer_uv':np.mean(uvs[outer],axis=0).tolist()}
        for part,ids in zip(['upper','lower'],paths):
            arr=np.array([np.mean(uvs[i],axis=0) for i in ids]);arr=arr[np.argsort(arr[:,0])]
            xx=np.linspace(arr[0,0],arr[-1,0],19)
            row[part]=np.c_[xx,np.interp(xx,arr[:,0],arr[:,1])].tolist()
        result.append(row)
    assert len(result)==2,'Requires actual Mia dense eye boundaries, not legacy indices'
    return result

def apply_upperfold_m5(skin):
    measured=measured_lid_uv(skin)
    old=skin.data.materials[7];mat=old.copy();mat.name='MIA_FaceAnatomy9_Identity_m5'
    skin.data.materials[7]=mat;n=mat.node_tree.nodes;l=mat.node_tree.links
    assert n.get('IDENTITY9_SecondaryFoldPigment'),'Apply to saved M4 route only'
    assert not any(q.name.startswith('M5_') for q in n),'M5 already applied'
    sep=n.new('ShaderNodeSeparateXYZ');sep.name='M5_ActualUVComponents';l.new(n['FINISH8_ACTUAL_UV'].outputs['UV'],sep.inputs[0])
    def math(name,op,a,b=0):
        q=n.new('ShaderNodeMath');q.name='M5_'+name;q.operation=op
        for i,v in enumerate((a,b)):
            if isinstance(v,(float,int,np.floating)):q.inputs[i].default_value=float(v)
            else:l.new(v,q.inputs[i])
        return q.outputs[0]
    def fade(name,x,lo,hi,invert=False):
        q=n.new('ShaderNodeMapRange');q.name='M5_'+name;q.clamp=True;q.interpolation_type='SMOOTHERSTEP'
        l.new(x,q.inputs['Value']);q.inputs['From Min'].default_value=lo;q.inputs['From Max'].default_value=hi
        if invert:q.inputs['To Min'].default_value=1;q.inputs['To Max'].default_value=0
        return q.outputs[0]
    def gaussian(name,center,width):
        d=math(name+'Distance','SUBTRACT',sep.outputs['Y'],center)
        d=math(name+'Width','DIVIDE',d,width);sq=math(name+'Square','MULTIPLY',d,d)
        return math(name+'Gaussian','POWER',2.718281828,math(name+'Negative','MULTIPLY',sq,-1))
    def uvcurve(name,samples):
        q=n.new('ShaderNodeFloatCurve');q.name='M5_'+name;q.mapping.initialize();cv=q.mapping.curves[0]
        cv.points[0].location=(0,samples[0][1]);cv.points[-1].location=(1,samples[-1][1])
        for x,y in samples:cv.points.new(x,y).handle_type='AUTO'
        q.mapping.update();l.new(sep.outputs['X'],q.inputs['Value'])
        return q.outputs[0]
    sums={}
    for row in measured:
        tag=str(row['side']);inner=row['inner_uv'][0];outer=row['outer_uv'][0]
        t=math(tag+'T','DIVIDE',math(tag+'InnerDistance','SUBTRACT',sep.outputs['X'],inner),outer-inner)
        scope=math(tag+'UpperEnds','MULTIPLY',fade(tag+'UpperInner',t,.07,.23),fade(tag+'UpperOuter',t,.76,.95,True))
        # A short open upper arc, varying in separation from the actual lid.
        # Clearance probe: old .010..012 lies -0.70..+0.16 mm relative to
        # the actual black upper-lash top. This offset clears it by ~2 mm.
        off=math(tag+'CreaseOffset','ADD',.021,math(tag+'OuterOffset','MULTIPLY',t,-.003))
        upper=uvcurve(tag+'MeasuredUpperLidUV',row['upper'])
        crease_center=math(tag+'CreaseCenter','ADD',upper,off)
        crease=math(tag+'CreaseScope','MULTIPLY',gaussian(tag+'Crease',crease_center,.00125),scope)
        pigment_center=math(tag+'PigmentCenter','ADD',upper,.013)
        pigment=math(tag+'PigmentScope','MULTIPLY',gaussian(tag+'Pigment',pigment_center,.008),scope)
        lower=uvcurve(tag+'MeasuredLowerLidUV',row['lower'])
        lower_center=math(tag+'LowerEdgeCenter','SUBTRACT',lower,.011)
        lower_scope=math(tag+'LowerEnds','MULTIPLY',fade(tag+'LowerInner',t,.12,.28),fade(tag+'LowerOuter',t,.68,.86,True))
        highlight=math(tag+'LowerHighlightScope','MULTIPLY',gaussian(tag+'LowerHighlight',lower_center,.0028),lower_scope)
        for key,value in [('crease',crease),('pigment',pigment),('highlight',highlight)]:
            sums[key]=math(tag+key+'Sum','ADD',sums[key],value) if key in sums else value
    def mix(name,input_color,factor,strength,color,mode):
        q=n.new('ShaderNodeMixRGB');q.name='M5_'+name;q.blend_type=mode
        l.new(math(name+'Strength','MULTIPLY',factor,strength),q.inputs[0]);l.new(input_color,q.inputs[1]);q.inputs[2].default_value=color
        return q.outputs[0]
    base=n['IDENTITY9_SecondaryFoldPigment'].outputs[0]
    pigment=mix('UpperLidPigment',base,sums['pigment'],.14,(.58,.38,.35,1),'MULTIPLY')
    crease=mix('UpperCreasePigment',pigment,sums['crease'],.38,(.39,.21,.22,1),'MULTIPLY')
    final=mix('LowerBrightBoundary',crease,sums['highlight'],.14,(1,.86,.76,1),'MIX')
    l.new(final,n['PigmentTimesControlledLight'].inputs[1])
    mat['mia_m5_limits']='Measured existing UV boundaries with procedural open upper crease/brown pigment and faint lower bright edge. No new raster texture, UV, geometry or key edits. Blink render review required.'
    return mat,measured

def maps(mat):
    return {q.name:{'name':q.image.name,'size':list(q.image.size),'colorspace':q.image.colorspace_settings.name,'packed_sha256':hashlib.sha256(q.image.packed_file.data).hexdigest() if q.image.packed_file else None} for q in mat.node_tree.nodes if q.type=='TEX_IMAGE' and q.image}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--output-dir',required=True)
    a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);source=Path(a.source).resolve();out=Path(a.output_dir).resolve();out.mkdir(parents=True,exist_ok=True)
    native=out/'Mia_UpperFold_M5.blend';assert not native.exists();source_sha=sha(source)
    bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);before=snapshot()
    slots={o.name:[m.name if m else None for m in o.data.materials] for o in bpy.data.objects if o.type=='MESH'}
    skin=bpy.data.objects[SKIN];beforemaps=maps(skin.data.materials[7]);mat,measured=apply_upperfold_m5(skin)
    assert snapshot()==before;assert maps(mat)==beforemaps
    bpy.ops.wm.save_as_mainfile(filepath=str(native));bpy.ops.wm.open_mainfile(filepath=str(native),use_scripts=False)
    assert snapshot()==before;assert maps(bpy.data.objects[SKIN].data.materials[7])==beforemaps
    for name,ms in slots.items():
        actual=[m.name if m else None for m in bpy.data.objects[name].data.materials]
        for i,old in enumerate(ms):
            if name==SKIN and i==7:continue
            assert actual[i]==old,(name,i)
    assert sha(source)==source_sha
    report={'source':{'path':str(source),'sha256':source_sha},'candidate':{'path':str(native),'sha256':sha(native)},'measured_lid_uv':measured,'recipe':{'path':str(Path(__file__).resolve()),'sha256':sha(__file__)},'saved_reopen_audit':{'all_meshes_keys_uv_topology_transforms_exact':True,'only_skin_slot7_assignment_changed':True,'all_existing_packed_maps_exact':True,'source_native_unchanged':True},'maps':beforemaps,'limits':['One bounded procedural material candidate; no new painted map or resolution.','Offset/width/strength are artistic approximations; measured UV curves are exact source-derived geometry samples, not metrically measured anatomy from the illustration.','Half/fullblink and actual source comparison must be reviewed before adoption.','No ART PASS.']}
    (out/'manifest.json').write_text(json.dumps(report,indent=2));print('UPPERFOLD_M5_DONE',native)
