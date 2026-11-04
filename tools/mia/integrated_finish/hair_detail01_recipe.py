"""Finite UV pigment signals for ONE early-look trial; no bpy or raster asset.

U wraps a 32-point circumference, V runs root0 -> tip1. Source-v22 hierarchy:
muted ash mass, broad dark separations, sparse tapered finer ink, soft broken
highlight. These are authored cubic paths/windows, not random/noise fibers.
Actual800px/ORTHO0.78m rear widths p10/50/90=8.79/18.43/24.14px; accents6-9px.
Full fine support0.030U would reach0.66px at p10, so use0.045-0.050U with soft
edges and finite V fades. This is not all-view anti-alias/animation approval.
"""
import numpy as np

UV_NAME = 'LockParamUV'
# name, kind, cubic Bezier U controls, outer half-width, V fade/full/fade knots,
# maximum linear pigment contribution. No specular/normal/roughness meaning.
BANDS = (
    ('GroupA', 'dark', (.075, .105, .065, .110), .065, (.07, .18, .78, .94), .18),
    ('GroupB', 'dark', (.305, .270, .330, .290), .072, (.15, .26, .66, .90), .13),
    ('InnerGroup', 'dark', (.610, .630, .580, .640), .070, (.08, .20, .72, .90), .12),
    ('InkA', 'dark', (.170, .150, .205, .190), .0225, (.10, .22, .54, .76), .26),
    ('InkB', 'dark', (.380, .410, .355, .390), .0250, (.26, .38, .70, .86), .22),
    ('InnerInk', 'dark', (.745, .705, .755, .735), .0225, (.16, .30, .60, .84), .22),
    ('SoftHighlight', 'light', (.220, .205, .285, .235), .100, (.20, .36, .58, .78), .065),
)


def smoothstep(value):
    value = np.clip(value, 0, 1)
    return value*value*(3-2*value)


def bezier_coefficients(controls):
    a,b,c,d = controls
    return a, 3*(b-a), 3*(a-2*b+c), -a+3*b-3*c+d


def signals(u, v):
    """CPU counterpart of the explicit node recipe, useful for seam/range QA."""
    u,v = np.broadcast_arrays(np.asarray(u, float), np.asarray(v, float))
    dark = np.zeros_like(u); light = np.zeros_like(u)
    for name,kind,controls,radius,window,gain in BANDS:
        a,b,c,d = bezier_coefficients(controls); center = a+v*(b+v*(c+v*d))
        first,full,stop,last = window
        gate = smoothstep((v-first)/(full-first))*(1-smoothstep((v-stop)/(last-stop)))
        distance = abs((u-center+.5) % 1-.5)
        scale = .55+.45*gate
        inner = radius*.35*scale; outer = radius*scale
        across = 1-smoothstep((distance-inner)/(outer-inner))
        contribution = across*gate*gain
        if kind == 'dark': dark += contribution
        else: light += contribution
    dark = np.minimum(dark, .45)
    factor = np.clip(1-dark+light*(1-.7*dark), .55, 1.065)
    return dict(dark=dark, highlight=light, pigment_factor=factor)


def verify():
    v = np.linspace(0, 1, 513)
    a,b = signals(0,v), signals(1,v)
    seam = max(float(np.max(abs(a[k]-b[k]))) for k in a)
    assert seam < 1e-12
    epsilon = 1e-5
    left, right = signals(-epsilon, v), signals(1-epsilon, v)
    assert max(float(np.max(abs(left[k]-right[k]))) for k in left) < 1e-12
    u,v = np.meshgrid(np.linspace(0, 1, 257), np.linspace(0, 1, 129))
    result = signals(u,v); factor = result['pigment_factor']
    periodic = signals(u+1,v)
    assert max(float(np.max(abs(result[k]-periodic[k]))) for k in result) < 1e-12
    assert np.isfinite(factor).all() and factor.min() >= .55 and factor.max() <= 1.065
    assert np.all(signals(u, np.zeros_like(v))['pigment_factor'] == 1)
    assert np.all(signals(u, np.ones_like(v))['pigment_factor'] == 1)
    return dict(bands=len(BANDS), periodic_U_seam_error=seam,
                pigment_factor_min=float(factor.min()), pigment_factor_max=float(factor.max()),
                mean_factor=float(factor.mean()), root_and_tip_pigment_exact=True,
                maps_generated=False, noise_nodes=False, native_saved=False, ART=False,
                aliasing='Unverified until actual back/obliques/high/low and output-scale review')
