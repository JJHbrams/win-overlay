"""Mia artist-directed surface hair study; never modifies its anatomy input.

The concealed volume, crown gathering, asymmetric fringe, loose nape waves and
single braid have distinct flow guides. This is an editable art candidate, not
an automatic likeness or rig acceptance claim.
"""
import argparse
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

EXPECTED_SHA = "d90744a9ec2370ae8d9564e482fbffd6b2485334f9571278d4482ce26ac943ca"
ROOT = Path("D:/ai/Mia3DWork/model-v02/hair-surface-stage")
BODY_BVH = None
BODY_FRAME = None
CLEARANCE_STATS = {}
FRONT_REGIONS = {"TEMPLE_LOOSE_WAVE", "SIDE_WISP", "LEFT_BRAID"}
REAR_REGIONS = {"SIDE_NAPE", "SIDE_REAR_WISP", "NAPE_LONG_WAVE", "NAPE_SHORT_LAYER", "CONCEALED_VOLUME"}
PROFILES = [
    (1.766,.001,.001,.021),(1.744,.056,.066,.021),
    (1.712,.088,.102,.023),(1.673,.107,.117,.024),
    (1.623,.115,.114,.029),(1.584,.119,.085,.053),
    (1.537,.126,.075,.068),(1.476,.132,.074,.079),
    (1.430,.122,.061,.089),(1.411,.095,.045,.096),
    (1.403,.038,.020,.101),(1.404,.001,.001,.101),
]


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default=str(ROOT / "Mia_HairSurface_v01.blend"))
    parser.add_argument("--render-dir", default=str(ROOT / "previews-v01"))
    parser.add_argument("--report", default=str(ROOT / "hair-surface-report-v01.json"))
    parser.add_argument("--expected-input-sha256", default=EXPECTED_SHA,
                        help="Explicit frozen input hash; permits a reviewed no-hair face-art checkpoint")
    parser.add_argument("--quick", action="store_true", help="Four art directions only")
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def fingerprint(obj):
    h = hashlib.sha256()
    for row in obj.matrix_world:
        h.update(struct.pack("4f", *row))
    for vertex in obj.data.vertices:
        h.update(struct.pack("3f", *vertex.co))
    for poly in obj.data.polygons:
        h.update(struct.pack("%dI" % len(poly.vertices), *poly.vertices))
    for uv in obj.data.uv_layers:
        h.update(uv.name.encode())
        for item in uv.data:
            h.update(struct.pack("2f", *item.uv))
    for key in obj.data.shape_keys.key_blocks if obj.data.shape_keys else []:
        h.update(key.name.encode())
        for point in key.data:
            h.update(struct.pack("3f", *point.co))
    return h.hexdigest()


def build_body_bvh(body):
    """Only the active canonical body, in its evaluated world frame."""
    global BODY_BVH, BODY_FRAME
    deps=bpy.context.evaluated_depsgraph_get()
    evaluated=body.evaluated_get(deps)
    data=evaluated.to_mesh(preserve_all_data_layers=True,depsgraph=deps)
    BODY_FRAME=[list(row)for row in evaluated.matrix_world]
    BODY_BVH=BVHTree.FromPolygons(
        [evaluated.matrix_world@v.co for v in data.vertices],
        [list(p.vertices)for p in data.polygons])
    evaluated.to_mesh_clear()


def body_hit(x,z,front):
    origin=Vector((x,-2 if front else 2,z))
    return BODY_BVH.ray_cast(origin,Vector((0,1 if front else -1,0)),4)[0]


def body_clearance(point,region,margin=.008):
    p=Vector(point)
    if p.z>=1.49 or region not in FRONT_REGIONS|REAR_REGIONS:return p
    front=region in FRONT_REGIONS
    hit=body_hit(p.x,p.z,front)
    if hit is None:return p
    target=hit.y-margin if front else hit.y+margin
    prior=p.y
    p.y=min(p.y,target) if front else max(p.y,target)
    if abs(p.y-prior)>1e-8:
        row=CLEARANCE_STATS.setdefault(region,{"adjusted_samples":0,"max_y_shift":0})
        row["adjusted_samples"]+=1
        row["max_y_shift"]=max(row["max_y_shift"],abs(p.y-prior))
    return p


def clearance_proof(owned):
    summary={}
    for obj in owned.objects:
        region=obj.get("region")
        if obj.type!="MESH" or region not in FRONT_REGIONS|REAR_REGIONS:continue
        row=summary.setdefault(region,{"tested":0,"minimum_clearance":None,"below_3mm":0})
        data=obj.data
        samples=[v.co for v in data.vertices]
        samples.extend(sum((data.vertices[i].co for i in poly.vertices),Vector())/len(poly.vertices)
                       for poly in data.polygons)
        front=region in FRONT_REGIONS
        for p in samples:
            if p.z>=1.49:continue
            hit=body_hit(p.x,p.z,front)
            if hit is None:continue
            gap=hit.y-p.y if front else p.y-hit.y
            row["tested"]+=1
            row["minimum_clearance"]=gap if row["minimum_clearance"] is None else min(gap,row["minimum_clearance"])
            row["below_3mm"]+=gap<.003
    return summary


def collection(name):
    result = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(result)
    return result


def link(obj, target):
    for source in list(obj.users_collection):
        source.objects.unlink(obj)
    target.objects.link(obj)
    return obj


def material(name, color, emission=False):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    nodes, links = m.node_tree.nodes, m.node_tree.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    if emission:
        shader = nodes.new("ShaderNodeEmission")
        shader.inputs["Color"].default_value = (*color, 1)
    else:
        shader = nodes.new("ShaderNodeBsdfPrincipled")
        shader.inputs["Base Color"].default_value = (*color, 1)
        shader.inputs["Roughness"].default_value = .83
        shader.inputs["Specular IOR Level"].default_value = .12
    links.new(shader.outputs[0], out.inputs["Surface"])
    return m


def catmull(points, t):
    u = min(.999999, max(0.0, t)) * (len(points) - 1)
    index = int(u)
    x = u - index
    a, b, c, d = [Vector(points[min(len(points) - 1, max(0, j))])
                   for j in (index - 1, index, index + 1, index + 2)]
    return .5 * ((2 * b) + (-a + c) * x + (2 * a - 5 * b + 4 * c - d) * x*x
                 + (-a + 3 * b - 3 * c + d) * x*x*x)


def piecewise(values, t):
    u = min(.999999, max(0, t)) * (len(values) - 1)
    index = int(u)
    x=u-index
    a,b,c,d=[values[min(len(values)-1,max(0,j))]for j in (index-1,index,index+1,index+2)]
    return .5*((2*b)+(-a+c)*x+(2*a-5*b+4*c-d)*x*x+(-a+3*b-3*c+d)*x*x*x)


def on_crown_surface(center):
    """Keep primary crown guide centers outside the concealed volume.

    A guide drawn through the skull exposes the featureless foundation instead
    of its intended flow; project each sampled row, not just control points.
    """
    z=center.z
    if z>1.756:
        return center
    for a,b in zip(PROFILES[:9],PROFILES[1:10]):
        if b[0]<=z<=a[0]:
            t=(a[0]-z)/(a[0]-b[0])
            rx=a[1]*(1-t)+b[1]*t;ry=a[2]*(1-t)+b[2]*t
            cy=a[3]*(1-t)+b[3]*t
            radius=math.sqrt((center.x/rx)**2+((center.y-cy)/ry)**2)
            if .01<radius<1.045:
                q=center.copy();q.x*=1.045/radius;q.y=cy+(q.y-cy)*1.045/radius
                return q
            break
    return center


def actual_crown_surface(point, offset=0):
    """Project a patch vertex to the same smooth profile as its support mesh.

    Per-row linear profile estimates caused stepped intersections. The guide
    stays artist-authored; only the supporting crown attachment is registered.
    """
    if point.z>1.755 or point.z<1.62:
        return point
    lo,hi=0,.52
    for _ in range(24):
        t=(lo+hi)*.5
        if catmull(PROFILES,t)[0]>point.z:lo=t
        else:hi=t
    z,rx,ry,cy=catmull(PROFILES,(lo+hi)*.5)
    theta=math.atan2((point.y-cy)/max(ry,.001),point.x/max(rx,.001))
    normal=Vector((math.cos(theta)/max(rx,.001),math.sin(theta)/max(ry,.001),0)).normalized()
    return Vector((rx*math.cos(theta),cy+ry*math.sin(theta),point.z))+normal*offset


def mesh(name, vertices, polygons, mat, owner, region):
    data = bpy.data.meshes.new(name + "_MESH")
    data.from_pydata([body_clearance(p,region)for p in vertices], [], polygons)
    data.materials.append(mat)
    data.update()
    if region in ("CONCEALED_VOLUME","HALF_UP_KNOT","LEFT_BRAID"):
        bm=bmesh.new();bm.from_mesh(data)
        bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7)
        bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-8)
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        bm.to_mesh(data);bm.free();data.update()
    obj = bpy.data.objects.new(name, data)
    owner.objects.link(obj)
    obj["owner"] = "Mia_HairSurface_Study"
    obj["region"] = region
    for poly in data.polygons:
        poly.use_smooth = True
    return obj


def line(name, points, radius, mat, owner, region):
    data = bpy.data.curves.new(name + "_CURVE", "CURVE")
    data.dimensions = "3D"
    data.resolution_u = 4
    data.bevel_depth = radius
    data.bevel_resolution = 2
    sp = data.splines.new("POLY")
    sp.points.add(len(points)-1)
    for item, co in zip(sp.points, [body_clearance(p,region,.008+radius)for p in points]):
        item.co = (*co, 1)
    data.materials.append(mat)
    obj = bpy.data.objects.new(name, data)
    owner.objects.link(obj)
    obj["owner"] = "Mia_HairSurface_Study"
    obj["region"] = region
    return obj


def panel(name, guides, widths, facing, mat, owner, region, ink=None,
          camber=.0045, rows=54, cols=11, strand_lines=2):
    """A broad convex ribbon with a physical backside and buried root.

    Across direction is obtained from the authored outward-facing direction and
    transported tangent. Widths are artist controls rather than constant tubes.
    """
    coordinates, polygons, samples = [], [], []
    prior = None
    direction = Vector(facing).normalized() if not callable(facing) else None
    for i in range(rows):
        t = i / (rows-1)
        center = catmull(guides, t)
        if region in ("CROWN_GATHER","SIDE_NAPE") or (region=="CROWN_FRINGE" and center.z>1.63):
            center=on_crown_surface(center)
        if callable(facing):
            direction=Vector(facing(center)).normalized()
        tangent = (catmull(guides, min(1, t+.002)) - catmull(guides, max(0, t-.002))).normalized()
        across = tangent.cross(direction)
        if across.length < .01:
            across = tangent.cross(Vector((0, 0, 1)))
        across.normalize()
        if prior is not None and prior.dot(across) < 0:
            across = -across
        prior = across
        normal = across.cross(tangent).normalized()
        if normal.dot(direction) < 0:
            normal = -normal
        half_width = max(.00025, piecewise(widths, t))
        samples.append((center, across, normal, half_width))
        for j in range(cols):
            q = j / (cols-1)*2-1
            height = camber*(1-q*q)*math.sin(math.pi*min(.95, t+.05))**.35
            vertex=center + across*q*half_width + normal*height
            if region in ("CROWN_GATHER","SIDE_NAPE") and t<.86:
                # The root enters the support smoothly; patch edges follow its
                # curvature instead of slicing it in staircase-shaped cuts.
                buried=max(0,min(1,t/.16))
                attach_offset=-.0015*(1-buried)+(.0010+height)*buried
                projected=actual_crown_surface(vertex,attach_offset)
                release=max(0,min(1,(t-.60)/.26))
                release=release*release*(3-2*release)
                vertex=projected.lerp(vertex,release)
            coordinates.append(vertex)
    for i in range(rows-1):
        for j in range(cols-1):
            a = i*cols+j
            polygons.append((a, a+1, a+cols+1, a+cols))
    obj = mesh(name, coordinates, polygons, mat, owner, region)
    solid = obj.modifiers.new("Shallow physical hair surface", "SOLIDIFY")
    solid.thickness = .0010
    solid.offset = -1
    obj["construction"] = "authored region flow; shallow convex patch with thickness"
    if ink:
        # Ink is selective and much thinner than the geometric width.
        for edge in (-1, 1):
            col=0 if edge<0 else cols-1
            pts=[coordinates[i*cols+col]+samples[i][2]*.00018 for i in range(7,rows)]
            line(name + ("_EdgeL" if edge < 0 else "_EdgeR"), pts, .00030, ink, owner, region)
        for k in range(strand_lines):
            q = -.50 + (k+.35) / max(1, strand_lines)*.9
            u=(q+1)*.5*(cols-1);index=int(u);blend=u-index
            pts=[coordinates[i*cols+index].lerp(coordinates[i*cols+index+1],blend)+samples[i][2]*.00018
                 for i in range(10,rows-4)]
            line(name + "_Etch%02d" % k, pts, .00018, ink, owner, region)
    return obj


def concealed_volume(owner, mat):
    # Front recedes behind the face below the forehead; lower contour is buried
    # above the visible wave tips. The closed dome prevents open-scalp windows.
    profiles = PROFILES
    vertices, polygons = [], []
    rings, segments = 80, 80
    for i in range(rings):
        t = i/(rings-1)
        p = catmull(profiles, t)
        z, rx, ry, cy = p[:]
        for j in range(segments):
            a = j/segments*math.tau
            loose = max(0, min(1, (1.62-z)/.20))
            irregular = 1 + loose*(.035*math.sin(3*a+.7)+.018*math.sin(7*a))
            # The support volume must not draw a straight dark cap across the
            # forehead between individual bangs. Recess that concealed sector
            # behind the intact anatomy; face and scalp source meshes stay full.
            front=max(0,-math.sin(a))
            lower=max(0,min(1,(1.705-z)/.070))
            recess=.052*lower*front**3
            vertices.append((rx*math.cos(a)*irregular, cy+ry*math.sin(a)*irregular+recess,
                             z+loose*.008*math.sin(5*a+.2)))
    for i in range(rings-1):
        for j in range(segments):
            a = i*segments+j
            b = i*segments+(j+1)%segments
            polygons.append((a,b,b+segments,a+segments))
    polygons.extend([tuple(reversed(range(segments))), tuple((rings-1)*segments+j for j in range(segments))])
    return mesh("MiaHair_Concealed_Closed_DomeNape", vertices, polygons, mat, owner, "CONCEALED_VOLUME")


def crown(owner, mats):
    dark, ash, ink = mats
    # Front crown spreads across the skull, with several flow lengths and no
    # straight horizontal bang line. One selected forelock crosses the face.
    fronts = [
        ("R_Outer", [(-.004,.022,1.757),(-.064,-.026,1.726),(-.111,-.057,1.657),(-.123,-.073,1.582),(-.143,-.059,1.555)], [.008,.032,.029,.020,.001]),
        ("R_Sweep", [(.008,.012,1.758),(-.042,-.056,1.711),(-.091,-.098,1.648),(-.080,-.117,1.590),(-.100,-.123,1.563)], [.009,.037,.034,.019,.001]),
        ("R_Short", [(.016,.004,1.757),(-.019,-.074,1.703),(-.049,-.111,1.651),(-.054,-.117,1.602)], [.008,.034,.031,.001]),
        ("Center_Slip", [(.016,.002,1.759),(.003,-.078,1.705),(-.006,-.115,1.638),(.013,-.130,1.571),(.040,-.125,1.538)], [.006,.027,.023,.013,.0004]),
        ("L_Sweep", [(.024,.006,1.756),(.049,-.059,1.705),(.071,-.104,1.648),(.081,-.119,1.592),(.104,-.115,1.571)], [.006,.030,.030,.019,.0005]),
        ("L_Outer", [(.030,.012,1.752),(.093,-.029,1.703),(.116,-.059,1.645),(.121,-.064,1.582),(.151,-.045,1.561)], [.005,.029,.032,.020,.0005]),
    ]
    for i, (name, guides, widths) in enumerate(fronts):
        # Divide the visible part of broad flow families into unequal shallow
        # tapered locks. Shared origins remain buried in the crown, while tips
        # have different lengths instead of a repeated scalloped bang edge.
        children=(0,) if name=="Center_Slip" else (-1,1)
        for child in children:
            flow=[]
            for j,p in enumerate(guides):
                u=j/(len(guides)-1)
                offset=child*.010*math.sin(u*math.pi*.70)
                flow.append((p[0]+offset,p[1]-.001*abs(child),p[2]+child*.014*u*u))
            scale=.36 if child==0 else (.41 if child<0 else .37)
            panel("MiaHair_CrownFringe_"+name+"_%d"%child,flow,[w*scale for w in widths],
                  (0,-1,.20),ash if i in (2,4) and child<=0 else dark,owner,
                  "CROWN_FRINGE",ink,camber=.0013,strand_lines=1)
    # Seven low under-fringe sweeps fill the large windows left by the long
    # outer locks. Their uneven tips skim brows, while eye apertures stay open.
    under=[
        ("R0",[(.004,-.020,1.738),(-.034,-.078,1.686),(-.072,-.107,1.625),(-.083,-.109,1.584)], [.003,.013,.012,.0003]),
        ("R1",[(.015,-.025,1.738),(-.012,-.088,1.680),(-.046,-.111,1.621),(-.063,-.113,1.572)], [.003,.014,.013,.0003]),
        ("R2",[(.018,-.027,1.735),(.001,-.089,1.680),(-.020,-.113,1.632),(-.039,-.115,1.584)], [.003,.014,.013,.0003]),
        ("Mid",[(.022,-.030,1.738),(.011,-.096,1.672),(-.002,-.116,1.621),(-.018,-.118,1.600)], [.003,.013,.013,.0003]),
        ("L0",[(.024,-.021,1.739),(.034,-.088,1.681),(.026,-.113,1.628),(.012,-.116,1.587)], [.003,.013,.012,.0003]),
        ("L1",[(.028,-.017,1.736),(.056,-.078,1.683),(.062,-.108,1.625),(.047,-.114,1.578)], [.003,.014,.012,.0003]),
        ("L2",[(.033,-.010,1.736),(.079,-.066,1.680),(.091,-.101,1.626),(.078,-.110,1.586)], [.003,.013,.011,.0003]),
    ]
    for i,(name,guides,widths) in enumerate(under):
        panel("MiaHair_UnderFringe_"+name,guides,widths,(0,-1,.1),
              ash if i in (1,4) else dark,owner,"UNDER_FRINGE",ink,
              camber=.0010,strand_lines=1)
    for side,label in ((-1,"R"),(1,"L")):
        panel("MiaHair_UnderFringe_Temple"+label,
              [(side*.079,-.020,1.665),(side*.098,-.045,1.612),
               (side*.094,-.059,1.558),(side*.109,-.053,1.523),
               (side*.092,-.056,1.493)],
              [.004,.014,.014,.011,.0003],(side*.6,-1,.05),dark,owner,
              "UNDER_FRINGE",ink,camber=.0011,strand_lines=1)
    # Actual upper crown-to-knot gathering follows the dome around both sides.
    for side,label in ((-1,"R"),(1,"L")):
        for i in range(4):
            x = .042 + i*.021
            guides = [(side*.007,.024,1.759-i*.002), (side*x,.061,1.735-i*.009),
                      (side*(x+.022),.112,1.686-i*.007), (side*.038,.160,1.623+i*.003)]
            panel("MiaHair_Gather_%s%d" % (label,i), guides,
                  [.004,.024,.022,.005], (side*.6,.8,.2), ash if i==2 else dark,
                  owner,"CROWN_GATHER",ink,camber=.0013,strand_lines=1)
    for i,x in enumerate((-.030,0,.030)):
        panel("MiaHair_Gather_BackPart%d"%i,
              [(x*.12,.026,1.762),(x*.6,.092,1.731),(x,.145,1.686),(x*.4,.164,1.634)],
              [.004,.026,.028,.005],(0,1,.3),ash if i==0 else dark,owner,"CROWN_GATHER",ink,camber=.0013,strand_lines=1)
    for side,label in ((-1,"R"),(1,"L")):
        panel("MiaHair_Gather_Temple"+label,
              [(side*.044,-.002,1.737),(side*.101,.008,1.691),
               (side*.119,.050,1.654),(side*.095,.121,1.628),(side*.035,.158,1.625)],
              [.004,.024,.027,.023,.004],(side,.0,.1),dark,owner,"CROWN_GATHER",ink,camber=.0013,strand_lines=1)
    # Smaller asymmetric splits sit on selected larger bangs; they do not form
    # a second equally ranked fringe or a straight bowl edge.
    small=[
        [(-.005,-.057,1.725),(-.039,-.109,1.662),(-.070,-.129,1.609),(-.079,-.132,1.592)],
        [(.028,-.045,1.727),(.048,-.107,1.662),(.042,-.132,1.612),(.061,-.136,1.582)],
        [(-.042,-.032,1.724),(-.090,-.089,1.668),(-.112,-.119,1.607),(-.124,-.113,1.590)],
    ]
    for i,guides in enumerate(small):
        panel("MiaHair_Fringe_Split%d"%i,guides,[.004,.011,.009,.0002],(0,-1,.1),
              dark,owner,"FRINGE_SPLIT",ink,camber=.0015,cols=7,strand_lines=1)
    # Flyaways are short silhouette strokes whose roots enter primary patches.
    flyaways = [
        [(-.026,.017,1.752),(-.047,-.007,1.768),(-.066,-.014,1.766),(-.078,-.016,1.756)],
        [(.016,.020,1.756),(.025,.027,1.779),(.021,.030,1.784),(.009,.034,1.780)],
        [(.086,-.025,1.708),(.124,-.048,1.722),(.148,-.053,1.708)],
        [(-.103,-.022,1.682),(-.145,-.042,1.696),(-.166,-.042,1.674)],
    ]
    for i,guides in enumerate(flyaways):
        panel("MiaHair_Crown_Flyaway_%02d"%i,guides,[.0015,.006,.002,.0002],
              (0,-1,.2),dark,owner,"CROWN_FLYAWAY",ink,camber=.0008,cols=7,strand_lines=0)


def loose_waves(owner,mats):
    dark,ash,ink=mats
    # Two unequal face-framing tiers per side. The waves turn outward and back
    # instead of hanging in parallel straight strips.
    for side,label in ((-1,"R"),(1,"L")):
        for i in range(3):
            lift=i*.014
            guides=[(side*(.077+i*.012),.003,1.677-i*.018),
                    (side*(.117+i*.012),-.055,1.579-i*.020),
                    (side*(.126+i*.017),-.090,1.513-i*.020),
                    (side*(.144+i*.006),-.112,1.485-i*.008),
                    (side*(.146+i*.006),-.120,1.462-i*.004),
                    (side*(.145+i*.006),-.125,1.437-i*.001)]
            for child in (-1,1):
                flow=[]
                for j,p in enumerate(guides):
                    u=j/(len(guides)-1)
                    flow.append((p[0]+side*child*.006*u,p[1]+child*.009*u,
                                 p[2]+child*.013*u*u))
                panel("MiaHair_%s_TempleWave%d_%d"%(label,i,child),flow,
                      [w*(.37 if child<0 else .33) for w in (.012,.030,.025,.028,.019,.0004)],
                      (side*.7,-.8,0),ash if i==1 and child<0 else dark,owner,
                      "TEMPLE_LOOSE_WAVE",ink,camber=.0011,strand_lines=1)
        # Side-to-nape layers cover the support volume while leaving short
        # tufts to break silhouette. No repeated rose-shaped surface ornaments.
        for i in range(2):
            guides=[(side*.096,.057+i*.034,1.671-i*.018),
                    (side*.126,.077+i*.032,1.596-i*.024),
                    (side*.152,.078+i*.030,1.514-i*.023),
                    (side*.142,.093+i*.030,1.436-i*.027),
                    (side*.165,.074+i*.033,1.379-i*.025),
                    (side*.153,.088+i*.031,1.347-i*.018)]
            for child in (-1,1):
                flow=[]
                for j,p in enumerate(guides):
                    u=j/(len(guides)-1)
                    flow.append((p[0]+side*child*.003*u,p[1]+child*.012*u,
                                 p[2]+child*.017*u*u))
                panel("MiaHair_%s_SideNape%d_%d"%(label,i,child),flow,
                      [w*(.35 if child<0 else .32) for w in (.009,.031,.033,.033,.019,.0003)],
                      (side,.2,.0),dark if i==0 else ash,owner,"SIDE_NAPE",ink,
                      camber=.0012,strand_lines=1)
        for i,(z,y,length) in enumerate(((1.652,-.010,.175),(1.566,.018,.180),(1.476,.066,.145))):
            length=min(length,z-1.435)
            guides=[(side*.125,y,z),(side*.141,y-.010,z-length*.38),
                    (side*.155,y-.010,z-length*.72),(side*.162,y,z-length)]
            if i == 0:
                guides = [(p[0], depth, p[2]) for p, depth in
                          zip(guides, (-.010, -.050, -.085, -.100))]
            # These two wisps originate behind the ear. Front projection folded
            # them around the shoulder; keep their intended rear-side flow.
            wisp_region = "SIDE_WISP" if i == 0 else "SIDE_REAR_WISP"
            panel("MiaHair_%s_LooseWisp%d"%(label,i),guides,[.001,.0035,.0028,.0002],
                  (side,-.4,.1),dark,owner,wisp_region,ink,camber=.0005,cols=7,strand_lines=0)
    # Rear loose hair starts below/around the half-up gathering. The uneven
    # lengths, staggered S-bends and overlapping widths avoid a cape-like rim.
    specifications=[
        (-.120,.105,1.653,-.154,1.327),(-.084,.143,1.679,-.118,1.291),
        (-.043,.159,1.638,-.065,1.319),(.000,.169,1.654,.010,1.283),
        (.042,.163,1.643,.072,1.307),(.086,.143,1.674,.119,1.292),
        (.120,.102,1.641,.151,1.340),
    ]
    for i,(x,y,z,endx,endz) in enumerate(specifications):
        bend=1 if i%2 else -1
        guides=[(x*.72,y*.70,z+.018),(x+bend*.018,y+.014,z-.078),
                (x-bend*.010,y+.018,z-.154),(endx+bend*.016,y-.018,endz+.055),
                (endx,y-.035,endz)]
        for child in ((-1,0,1) if i in (0,2,3,5) else (-1,1)):
            flow=[]
            for j,p in enumerate(guides):
                u=j/(len(guides)-1)
                flow.append((p[0]+child*.014*u,p[1]+abs(child)*.002,
                             p[2]+child*.022*u*u))
            scale=.31 if child<=0 else .27
            panel("MiaHair_Rear_LongWave%02d_%d"%(i,child),flow,
                  [w*scale for w in (.001,.034,.035,.026,.0004)],
                  (x*3,1,.1),ash if i in (2,5) and child<=0 else dark,
                  owner,"NAPE_LONG_WAVE",ink,camber=.0012,strand_lines=1)
    # Short overlapping rear tiers retain large shared masses; they are not
    # equal-ranking copies of every long wave.
    for i,(x,z) in enumerate(((-.096,1.465),(-.035,1.443),(.038,1.476),(.102,1.450))):
        guides=[(x*.30,.110,1.697),(x,.176,1.593),(x*1.2,.184,z+.075),
                (x*1.05,.171,z),(x*.82,.181,z-.028)]
        for child in (-1,0,1):
            flow=[]
            for j,p in enumerate(guides):
                u=j/(len(guides)-1)
                flow.append((p[0]+child*.015*u,p[1]+abs(child)*.002,
                             p[2]+child*.019*u*u))
            panel("MiaHair_Rear_ShortLayer%02d_%d"%(i,child),flow,
                  [w*(.33 if child<=0 else .30) for w in (.001,.035,.035,.024,.0004)],
                  (x*2,1,.1),dark if i%2 or child else ash,owner,"NAPE_SHORT_LAYER",ink,
                  camber=.0012,strand_lines=1)


def knot_and_braid(owner,mats):
    dark,ash,ink=mats
    # One gathered half-up knot, with a closed irregular core and broad wraps.
    vertices,faces=[],[]
    rings,segments=25,44
    for i in range(rings):
        p=math.pi*i/(rings-1)
        for j in range(segments):
            a=math.tau*j/segments
            radial=1+.065*math.sin(3*a+2*p)
            vertices.append((.044*math.sin(p)*math.cos(a)*radial,
                             .157+.034*math.sin(p)*math.sin(a)*radial,
                             1.625+.037*math.cos(p)))
    for i in range(rings-1):
        for j in range(segments):
            a=i*segments+j;b=i*segments+(j+1)%segments
            faces.append((a,b,b+segments,a+segments))
    mesh("MiaHair_HalfUp_OneClosedKnot",vertices,faces,dark,owner,"HALF_UP_KNOT")
    for i in range(6):
        a=i*math.tau/6
        guides=[]
        for j in range(6):
            t=j/5
            ang=a+t*math.pi*1.3
            guides.append((.044*math.cos(ang),.159+.036*math.sin(ang),1.625+.029*math.sin(t*math.pi-.7)))
        panel("MiaHair_Knot_Wrap%02d"%i,guides,[.003,.008,.009,.009,.006,.001],
              lambda p:(p.x,p.y-.157,(p.z-1.625)*.7),ash if i==2 else dark,owner,"KNOT_WRAP",ink,
              camber=.0017,cols=7,strand_lines=1)
    centers=[(.100,-.003,1.606),(.111,-.028,1.561),(.121,-.066,1.493),
             (.132,-.102,1.406),(.145,-.111,1.319)]
    for lane in range(3):
        points=[]
        n=150
        for i in range(n):
            t=i/(n-1);c=catmull(centers,t)
            tangent=(catmull(centers,min(1,t+.002))-catmull(centers,max(0,t-.002))).normalized()
            u=tangent.cross(Vector((0,-1,0))).normalized()
            v=tangent.cross(u).normalized()
            phase=t*math.tau*6.5+lane*math.tau/3
            radius=.010*(1-.48*t)
            if c.z<1.49:
                full_radius=radius+.0073*(1-.55*t)
                hits=[body_hit(c.x+offset,c.z,True)for offset in (-full_radius,0,full_radius)]
                hits=[p for p in hits if p is not None]
                if hits:c.y=min(c.y,min(p.y for p in hits)-full_radius-.008)
            points.append(c+u*(radius*math.cos(phase))+v*(radius*.70*math.sin(phase)))
        verts,polys=[],[]
        section=10
        for i,center in enumerate(points):
            t=i/(n-1)
            tangent=(points[min(n-1,i+1)]-points[max(0,i-1)]).normalized()
            u=tangent.cross(Vector((0,-1,0))).normalized();v=tangent.cross(u).normalized()
            r=.0073*(1-.55*t)
            for j in range(section):
                a=j/section*math.tau
                verts.append(center+u*r*math.cos(a)+v*r*.75*math.sin(a))
        for i in range(n-1):
            for j in range(section):
                a=i*section+j;b=i*section+(j+1)%section
                polys.append((a,b,b+section,a+section))
        polys.extend([tuple(reversed(range(section))),
                      tuple((n-1)*section+j for j in range(section))])
        obj=mesh("MiaHair_LEFT_OneBraid_Lane%d"%lane,verts,polys,ash if lane==1 else dark,owner,"LEFT_BRAID")
        obj["braid_assembly"]="ONE_ANATOMICAL_LEFT_BRAID"
        # A narrow front-facing internal stroke makes each over/under lobe read.
        line("MiaHair_Braid_Etch%d"%lane,[p+Vector((0,-.004,0)) for p in points],.00035,ink,owner,"LEFT_BRAID")
    tail=[body_clearance(p,"LEFT_BRAID",.0165)for p in
          ((.145,-.111,1.330),(.145,-.110,1.310),(.153,-.109,1.292))]
    panel("MiaHair_Braid_Tail",tail,[.011,.009,.0003],(0,-1,0),dark,owner,"LEFT_BRAID",ink,cols=9,strand_lines=2)


def aim(camera,position,target):
    camera.location=position
    camera.rotation_euler=(Vector(target)-camera.location).to_track_quat("-Z","Y").to_euler()


def render(args,owned):
    sc=bpy.context.scene
    sc.render.engine="BLENDER_EEVEE"
    sc.render.resolution_x=sc.render.resolution_y=768
    sc.render.resolution_percentage=100
    sc.render.image_settings.file_format="PNG"
    sc.render.film_transparent=False
    sc.render.image_settings.color_mode="RGBA"
    camera=bpy.data.objects["MIA_REVIEW_CAMERA"]
    sc.camera=camera
    camera.data.type="ORTHO"
    camera.data.ortho_scale=.61
    out=Path(args.render_dir);out.mkdir(parents=True,exist_ok=True)
    directions={"front":(0,-.85,1.58),"left":(.85,0,1.58),"back":(0,.85,1.58),
                "right_3q":(-.65,-.65,1.60),"left_3q":(.65,-.65,1.60),
                "rear_3q":(-.65,.65,1.60),"right":(-.85,0,1.58),"high_front":(0,-.85,1.82)}
    result=[]
    for name,position in list(directions.items())[:4] if args.quick else directions.items():
        aim(camera,position,(0,.025,1.53))
        sc.render.filepath=str(out/("art_"+name+".png"))
        bpy.ops.render.render(write_still=True);result.append(sc.render.filepath)
    if not args.quick:
        clay=material("MiaHair_StructureClay",(.24,.24,.24))
        originals={}
        for obj in owned.objects:
            if obj.type=="CURVE":obj.hide_render=True
            elif obj.type=="MESH":
                originals[obj.name]=list(obj.data.materials)
                obj.data.materials.clear();obj.data.materials.append(clay)
        for name in ("front","left","back","right_3q"):
            aim(camera,directions[name],(0,.025,1.53))
            sc.render.filepath=str(out/("structure_"+name+".png"))
            bpy.ops.render.render(write_still=True);result.append(sc.render.filepath)
        for obj in owned.objects:
            if obj.type=="CURVE":obj.hide_render=False
            elif obj.name in originals:
                obj.data.materials.clear()
                for mat in originals[obj.name]:obj.data.materials.append(mat)
    return result


def main():
    args=arguments()
    assert Path(args.input).resolve()!=Path(args.output).resolve(),"source overwrite forbidden"
    input_sha=sha(args.input)
    assert input_sha==args.expected_input_sha256.lower(),"Frozen input SHA mismatch"
    bpy.ops.wm.open_mainfile(filepath=args.input)
    bpy.context.view_layer.update()
    canonical=[bpy.data.objects[n] for n in ("Mia_Face_AnimeTopology","Mia_Body_Anatomy_Skin")]
    assert not [c.name for c in bpy.data.collections if c.name.startswith("MIA_HAIR_")],"Refuse stacked hair-stage input"
    primary=[o for o in bpy.data.objects if o.type=="MESH" and
             (o.name.startswith("Mia_Face_AnimeTopology") or o.name.startswith("Mia_Body_Anatomy_Skin"))]
    assert {o.name for o in primary}=={o.name for o in canonical} and len(primary)==2,"Duplicate canonical anatomy"
    before={o.name:fingerprint(o) for o in canonical}
    source_expression={k.name:k.value for k in canonical[0].data.shape_keys.key_blocks}
    build_body_bvh(canonical[1])
    owned=collection("MIA_HAIR_SURFACE_V01_OWNED")
    mats=(material("MiaHairSurface_Charcoal",(.051,.046,.053)),
          material("MiaHairSurface_Ash",(.073,.066,.073)),
          material("MiaHairSurface_Ink",(.005,.004,.006),True))
    concealed_volume(owned,mats[0]);crown(owned,mats);loose_waves(owned,mats);knot_and_braid(owned,mats)
    bpy.context.view_layer.update()
    points=[o.matrix_world@v.co for o in owned.objects if o.type=="MESH" for v in o.data.vertices]
    envelope=[[min(p[i] for p in points),max(p[i] for p in points)]for i in range(3)]
    assert envelope[0][0]>-.22 and envelope[0][1]<.22 and envelope[2][0]>1.20 and envelope[2][1]<1.82,envelope
    after={o.name:fingerprint(o) for o in canonical}
    assert before==after,"Anatomy changed"
    assert source_expression=={k.name:k.value for k in canonical[0].data.shape_keys.key_blocks},"Expression changed"
    clearance=clearance_proof(owned)
    Path(args.output).parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=args.output)
    frames=render(args,owned)
    assert sha(args.input)==input_sha
    report={"status":"ART_CANDIDATE_PENDING_REVIEW","source":args.input,"source_sha256":input_sha,
            "source_unchanged":True,"canonical_fingerprints_before":before,"canonical_fingerprints_after":after,
            "output":args.output,"output_sha256":sha(args.output),"envelope_xyz":envelope,
            "builder_sha256":sha(__file__),
            "owned_collection":owned.name,"mesh_objects":sum(o.type=="MESH"for o in owned.objects),
            "canonical_expression_preserved":True,"input_expression":source_expression,
            "clearance_target":"evaluated active Mia_Body_Anatomy_Skin; no archived donor/Face ray target",
            "clearance_body_world":BODY_FRAME,"clearance_adjustments":CLEARANCE_STATS,
            "clearance_vertex_and_face_center_proof":clearance,
            "clearance_scope":"below z1.49; semantic front locks/braid and rear nape/support, scalp roots exempt",
            "articulation":"unrigged static hair study; no secondary animation claim",
            "braid_assemblies":1,"braid_lanes":3,"construction":"closed concealed volume + regional authored shallow convex panels",
            "renders":frames}
    Path(args.report).parent.mkdir(parents=True,exist_ok=True)
    Path(args.report).write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print("HAIR_SURFACE_REPORT="+args.report)


if __name__=="__main__":main()
