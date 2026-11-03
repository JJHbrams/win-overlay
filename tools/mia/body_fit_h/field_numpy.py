"""Fast CPU H field with an independent frozen-expression reference.

No scene, mesh, optimizer, file output or native mutation. Parameters are
cap/trap scale, RX/RY profile shift in metres, and shared bilateral fan scale.
The field is approximate and its values are not signed geometric distances.
"""
from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import math
import sys
import numpy as np

sys.dont_write_bytecode = True
DEFAULT_CANONICAL = Path('D:/MiaWorkCache/mia-reference-work/win-overlay')
PARAMETER_NAMES = ('cap_scale', 'trap_scale', 'rx_shift_m', 'ry_shift_m', 'fan_scale')
LOWER_BOUNDS = np.array([.15, .15, 0., 0., .8])
UPPER_BOUNDS = np.array([1., 1., .08, .06, 1.])
HINGE_EPS = .001
GATE_ZERO_Z = 1.34
GATE_FULL_Z = 1.365
EXPECTED_E_SHA = '6bd907200a1ed082daf81fd2abde77e229890ecce405b415e3ca5b8e1e76f20d'
EXPECTED_BASE_SHA = '94ff4d29ec7629de017281aef6fc63e3d681fd2da0dd7d9c6f6583b265f34bd0'


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def smoothstep5(t):
    t = np.clip(t, 0., 1.)
    return t*t*t*(10.-15.*t+6.*t*t)


def hinge(d, eps=HINGE_EPS):
    """C2 positive part with derivative smoothstep5 in [0,1]."""
    q = np.clip(d/eps, 0., 1.)
    return eps*(2.5*q**4-3.*q**5+q**6)+np.maximum(d-eps, 0.)


def smooth_min(a, b, width):
    h = np.maximum(width-np.abs(a-b), 0.)/width
    return np.minimum(a, b)-h*h*(width*.25)


class Model:
    parameter_names = PARAMETER_NAMES
    lower_bounds = LOWER_BOUNDS
    upper_bounds = UPPER_BOUNDS

    def __init__(self, canonical=DEFAULT_CANONICAL):
        self.canonical = Path(canonical)
        body = self.canonical/'asset/mia/blender/mia-fit-v003/body'
        self.source_dir = body/'shoulder11'
        self.wrapper = _load('H_numpy_frozen11', self.source_dir/'field.py')
        self.frozen = self.wrapper.base
        self.base = self.frozen.base
        self.p = json.loads((self.source_dir/'parameters.json').read_text(encoding='utf-8'))
        self.provenance = []
        for role, path in [
            ('frozen11_wrapper', self.source_dir/'field.py'),
            ('parameters', self.source_dir/'parameters.json'),
            ('actual_transitive_E', Path(self.frozen.__file__)),
            ('actual_transitive_base', Path(self.base.__file__)),
            ('canonical_E', body/'design-sculpt07/E/field.py'),
            ('canonical_base', body/'design-sculpt07/field.py'),
        ]:
            self.provenance.append(dict(role=role, path=str(path), sha256=_sha(path)))
        assert self.provenance[2]['sha256'] == self.provenance[4]['sha256'] == EXPECTED_E_SHA
        assert self.provenance[3]['sha256'] == self.provenance[5]['sha256'] == EXPECTED_BASE_SHA

        g_path = body/'surface-review12/proportion-G-probe/RAM-calibration.json'
        g = json.loads(g_path.read_text(encoding='utf-8'))['component_nesting']
        self.provenance.append(dict(role='fixed_cap_trap_anchor_source', path=str(g_path), sha256=_sha(g_path)))
        self.anchors = {
            'shoulder': np.array(g['cap']['anchor_world'], float),
            'trapezius': np.array(g['trap']['anchor_world'], float),
        }
        fan = self.p['anterior_fan']
        angle = math.radians(fan['angle_y_degrees'])
        co, si = math.cos(angle), math.sin(angle)
        rotation = np.array([[co, 0., si], [0., 1., 0.], [-si, 0., co]])
        local = .95*np.array([-1./np.sqrt(2.), 0., -1./np.sqrt(2.)])
        self.anchors['anterior_fan'] = np.array(fan['center'])+rotation@np.diag(fan['radii'])@local
        assert self.anchors['anterior_fan'][0] < fan['center'][0]
        assert self.anchors['anterior_fan'][2] < fan['center'][2]
        self.anchor_local = {}
        for key, anchor in self.anchors.items():
            q = self.p[key]
            angle = math.radians(q['angle_y_degrees'])
            co, si = math.cos(angle), math.sin(angle)
            inverse_rotation = np.array([[co, 0., -si], [0., 1., 0.], [si, 0., co]])
            u = inverse_rotation@(anchor-np.array(q['center']))/np.array(q['radii'])
            assert np.linalg.norm(u) < 1.
            self.anchor_local[key] = u

        self._tables = {}
        for key in ['x_radius', 'y_radius', 'center_y']:
            table = np.asarray(self.p['thorax'][key], float)
            self._tables[key] = table, self.base.slopes(table[:, 0], table[:, 1])
        old_p = copy.deepcopy(self.p)
        old_p['trapezius'] = self.p['shoulder11']['old_trapezius']
        self._fold_expr, _ = self.frozen.make(old_p)
        self._fhom_expr, self._current_reg = self.frozen.make(self.p)
        self._f11_expr, _ = self.wrapper.make(self.p)

    @staticmethod
    def _points(points):
        points = np.asarray(points, dtype=float)
        if points.ndim != 2 or points.shape[1] != 3 or not np.isfinite(points).all():
            raise ValueError('Expected finite points[N,3]')
        return points

    @staticmethod
    def _params(params):
        params = np.asarray(params, dtype=float)
        if params.shape != (5,) or not np.isfinite(params).all():
            raise ValueError('Expected five finite H parameters')
        if np.any(params < LOWER_BOUNDS) or np.any(params > UPPER_BOUNDS):
            raise ValueError('H parameter outside declared bounds')
        return params

    def _profile(self, z, key):
        table, slopes = self._tables[key]
        x, y = table[:, 0], table[:, 1]
        out = np.full_like(z, float(y[0]))
        # Same Hermite accumulation and clamping order as frozen base.profile.
        for i in range(len(x)-1):
            h = float(x[i+1]-x[i])
            t = np.minimum(np.maximum((z-float(x[i]))/h, 0.), 1.)
            t2, t3 = t*t, t*t*t
            out = out+(2*t3-3*t2)*(float(y[i])-float(y[i+1]))+(t3-2*t2+t)*float(h*slopes[i])+(t3-t2)*float(h*slopes[i+1])
        return out

    @staticmethod
    def _ellipsoid(points, component, sign):
        center = np.array(component['center'], float)
        center[0] *= sign
        radii = component['radii']
        angle = sign*math.radians(component.get('angle_y_degrees', 0.))
        co, si = math.cos(angle), math.sin(angle)
        dx, dy, dz = (points-center).T
        qx = (co*dx-si*dz)/radii[0]
        qz = (si*dx+co*dz)/radii[2]
        return (np.sqrt(np.maximum(qx*qx+(dy/radii[1])*(dy/radii[1])+qz*qz, 0.))-1.)*min(radii)

    def contracted_component(self, key, scale):
        if key not in self.anchors:
            raise ValueError('Only cap, trap and fan contract')
        q = copy.deepcopy(self.p[key])
        if scale != 1.:
            anchor = self.anchors[key]
            q['center'] = (anchor+scale*(np.array(q['center'])-anchor)).tolist()
            q['radii'] = (scale*np.array(q['radii'])).tolist()
        return q

    def _breasts(self, points):
        x, y, z = points.T
        b = self.p['breast'];c = b['support_map']
        weight = (1.-smoothstep5((np.abs(x)-c['x_full'])/(c['x_zero']-c['x_full'])))*(1.-smoothstep5((y-c['y_full'])/(c['y_zero']-c['y_full'])))*smoothstep5((z-c['z0'])/(c['z_full']-c['z0']))
        zp = z-weight*(z-c['z0'])*(1.-1./c['height_scale'])
        dz = zp-b['center_z'];rx, ry, rz = b['radii']
        width = b['upper_posterior_warp']['width_m']
        v = np.minimum(np.maximum(dz/width, 0.), 1.)
        h = width*(v*v*v-.5*v*v*v*v)+np.maximum(dz-width, 0.)
        warp = b['upper_posterior_warp']['k']*h
        mass = []
        for sign in [-1, 1]:
            xp = x+sign*c['medial_gather_m']*weight
            qx = (xp-sign*b['center_x'])/rx
            qy = (y-warp-b['center_y']-b['yz_shear']*dz)/ry
            qz = dz/rz
            value = (np.sqrt(np.maximum(qx*qx+qy*qy+qz*qz, 0.))-1.)*min(b['radii'])
            mass.append(np.maximum(value, y-b['posterior_cap_y']))
        return smooth_min(mass[0], mass[1], b['interbreast_blend'])

    def _union(self, points, params=None, original_trap=False):
        x, y, z = points.T;t = self.p['thorax']
        rx = self._profile(z, 'x_radius');ry = self._profile(z, 'y_radius')
        if params is not None:
            rx = rx-hinge(rx-self._profile(z+params[2], 'x_radius'))
            ry = ry-hinge(ry-self._profile(z+params[3], 'y_radius'))
        cy = self._profile(z, 'center_y')
        torso = np.maximum((np.sqrt(np.maximum((x/rx)*(x/rx)+((y-cy)/ry)*((y-cy)/ry), 0.))-1.)*.075, np.maximum(t['z_min']-z, z-t['z_max']))
        b = self.p['breast'];blend = b['upper_thorax_blend']
        local_blend = blend['lower_m']+(blend['upper_m']-blend['lower_m'])*smoothstep5((z-b['center_z'])/blend['ramp_height_m'])
        result = smooth_min(torso, self._breasts(points), local_blend)
        scales = {} if params is None else {'shoulder': params[0], 'trapezius': params[1], 'anterior_fan': params[4]}
        components = {}
        for key in ['shoulder', 'upper_arm', 'anterior_fan', 'posterior_wall', 'trapezius']:
            if key == 'trapezius' and original_trap:
                components[key] = self.p['shoulder11']['old_trapezius']
            elif key in scales:
                components[key] = self.contracted_component(key, scales[key])
            else:
                components[key] = self.p[key]
        for sign in [-1, 1]:
            for key in ['shoulder', 'upper_arm', 'anterior_fan', 'posterior_wall', 'trapezius']:
                result = smooth_min(result, self._ellipsoid(points, components[key], sign), self.p[key]['blend'])
        return result

    def baseline(self, points, version='11'):
        points = self._points(points)
        if version == 'old':
            return self._union(points, original_trap=True)
        hom = self._union(points)
        if version == 'hom11':
            return hom
        if version != '11':
            raise ValueError('Unknown baseline version')
        old = self._union(points, original_trap=True)
        gate = self.p['shoulder11']
        return old+smoothstep5((points[:, 2]-gate['gate_zero_z'])/(gate['gate_full_z']-gate['gate_zero_z']))*(hom-old)

    def evaluate(self, points, params):
        points = self._points(points);params = self._params(params)
        old = self._union(points, original_trap=True)
        changed = self._union(points, params)
        weight = smoothstep5((points[:, 2]-GATE_ZERO_Z)/(GATE_FULL_Z-GATE_ZERO_Z))
        return old+weight*(changed-old)

    def changed_union(self, points, params):
        """FH before the outer construction gate; useful for nesting checks."""
        return self._union(self._points(points), self._params(params))

    def expression(self, params, with_parts=False):
        params = self._params(params);b = self.frozen
        x, y, z = [b.E('POS', i) for i in range(3)];t = self.p['thorax']
        def radius(key, shift):
            old = b.profile(z, t[key]);d = old-b.profile(z+float(shift), t[key]);q = b.mi(b.ma(d/HINGE_EPS, 0.), 1.)
            h = HINGE_EPS*(2.5*q*q*q*q-3.*q*q*q*q*q+q*q*q*q*q*q)+b.ma(d-HINGE_EPS, 0.)
            return old-h
        rx = radius('x_radius', params[2]);ry = radius('y_radius', params[3]);cy = b.profile(z, t['center_y'])
        torso = b.ma((b.sqrt((x/rx)*(x/rx)+((y-cy)/ry)*((y-cy)/ry))-1.)*.075, b.ma(t['z_min']-z, z-t['z_max']))
        breast = self.p['breast'];blend = breast['upper_thorax_blend'];tt = b.mi(b.ma((z-breast['center_z'])/blend['ramp_height_m'], 0.), 1.);ramp = tt*tt*tt*(10.-15.*tt+6.*tt*tt);width = blend['lower_m']+(blend['upper_m']-blend['lower_m'])*ramp
        result = b.sm(torso, self._current_reg['breast_pair'], width)
        scales = {'shoulder': params[0], 'trapezius': params[1], 'anterior_fan': params[4]}
        for sign in [-1, 1]:
            for key in ['shoulder', 'upper_arm', 'anterior_fan', 'posterior_wall', 'trapezius']:
                if key in scales:
                    component = self.contracted_component(key, scales[key]);center = component['center'].copy();center[0] *= sign
                    d = b.ellipsoid(x, y, z, center, component['radii'], sign*math.radians(component['angle_y_degrees']))
                else:
                    d = self._current_reg[key+('_L' if sign < 0 else '_R')]
                result = b.sm(result, d, self.p[key]['blend'])
        weight = b.smooth01((z-GATE_ZERO_Z)/(GATE_FULL_Z-GATE_ZERO_Z))
        field = self._fold_expr+weight*(result-self._fold_expr)
        if with_parts:
            return field, dict(Fold=self._fold_expr, FH=result, Fhom11=self._fhom_expr, F11=self._f11_expr, Wnew=weight)
        return field

    def reference(self, points, params, chunk_size=1024):
        points = self._points(points);expr = self.expression(params)
        if not len(points):
            return np.empty(0)
        return np.concatenate([self.wrapper.evaluate(expr, points[i:i+chunk_size]) for i in range(0, len(points), chunk_size)])

    def metadata(self, params):
        params = self._params(params);components = {}
        for key, index in [('shoulder', 0), ('trapezius', 1), ('anterior_fan', 4)]:
            q = self.contracted_component(key, params[index]);anchor = self.anchors[key]
            angle=math.radians(q['angle_y_degrees']);co,si=math.cos(angle),math.sin(angle);rotation=np.array([[co,0.,si],[0.,1.,0.],[-si,0.,co]])
            world_half_extents=np.sqrt(np.sum((rotation*np.array(q['radii'])[None,:])**2,axis=1))
            components[key] = dict(scale=float(params[index]),anchor_world_right=anchor.tolist(),anchor_world_left=[-float(anchor[0]),float(anchor[1]),float(anchor[2])],anchor_local_normalized=self.anchor_local[key].tolist(),anchor_norm=float(np.linalg.norm(self.anchor_local[key])),parent_center=self.p[key]['center'],parent_radii=self.p[key]['radii'],new_center_right=q['center'],new_radii=q['radii'],radii_meaning='Principal ellipsoid semiaxes; world-axis bounding half-extents reported separately',angle_y_degrees=q['angle_y_degrees'],new_world_axis_half_extents=world_half_extents.tolist(),anchor_is_medial=bool(anchor[0]<self.p[key]['center'][0]),anchor_is_inferior=bool(anchor[2]<self.p[key]['center'][2]),all_three_radii_scaled=True)
        return dict(parameters=dict(zip(PARAMETER_NAMES, params.tolist())),components=components,provenance=self.provenance,gate=dict(zero_z=GATE_ZERO_Z,full_z=GATE_FULL_Z,formula='Fold+smoothstep5((Z-1.34)/.025)*(FH-Fold)',upper_fade=False),hinge=dict(eps_m=HINGE_EPS,maximum_radius_offset_m=HINGE_EPS/2,slope_bounds=[0.,1.]),unchanged_definitions=['breast','upper_arm','posterior_wall','union_order_and_blend_widths'],meaning='RAM construction field only; values are not exact signed distances and no ART or mesh approval follows.')
