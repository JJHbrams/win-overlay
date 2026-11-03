"""CPU-only numerical/reference check; no optimizer, mesh or file output."""
import json
import time
import numpy as np
from field_numpy import Model, hinge, smoothstep5


def main():
    model = Model();rng = np.random.default_rng(20261103)
    points = np.column_stack([rng.uniform(-.30,.30,4096),rng.uniform(-.19,.14,4096),rng.uniform(1.03,1.50,4096)])
    # Mathematical QA fixtures, not source-fitting/amplitude experiments.
    fixtures = [np.array([1.,1.,0.,0.,1.]),np.array([.65,.55,.035,.02,.9]),np.array([.15,.15,.08,.06,.8])]
    old = model.baseline(points, 'old');f11 = model.baseline(points, '11');hom = model.baseline(points, 'hom11')
    oldref = model.wrapper.evaluate(model._fold_expr,points);homref = model.wrapper.evaluate(model._fhom_expr,points);f11ref = model.wrapper.evaluate(model._f11_expr,points)
    baseline_error = max(np.max(abs(old-oldref)),np.max(abs(hom-homref)),np.max(abs(f11-f11ref)))
    assert baseline_error<5e-14
    errors=[];nest=[];lower=points[:,2]<=1.34
    for params in fixtures:
        q = model.evaluate(points,params);ref=model.reference(points,params)
        error=float(np.max(abs(q-ref)));errors.append(error);assert error<5e-14
        assert np.array_equal(q[lower],old[lower])
        assert np.min(q-f11)>=-5e-14
        assert np.min(model.changed_union(points,params)-hom)>=-5e-14
        nest.append(float(np.min(q-f11)))
    assert np.min(f11-old)>=-5e-14
    assert np.min(hom-old)>=-5e-14
    old_gate=model.p['shoulder11']
    assert np.min(smoothstep5((points[:,2]-1.34)/.025)-smoothstep5((points[:,2]-old_gate['gate_zero_z'])/(old_gate['gate_full_z']-old_gate['gate_zero_z'])))>=-5e-14
    eps=.001;d=np.linspace(-.001,.002,3001);q=np.clip(d/eps,0.,1.);expected_derivative=smoothstep5(q)
    step=1e-8;numerical=(hinge(d+step)-hinge(d-step))/(2*step)
    assert np.max(abs(numerical-expected_derivative))<2e-8
    assert np.min(hinge(d))>=-1e-16 and np.max(hinge(d)-np.maximum(d,0.))<1e-15
    assert np.max(np.maximum(d,0.)-hinge(d))<=eps/2+1e-15
    zz=np.linspace(1.35,1.50,2001)
    for key,shift in [('x_radius',.035),('y_radius',.02)]:
        ro=model._profile(zz,key);rs=model._profile(zz+shift,key);new=ro-hinge(ro-rs)
        assert np.max(new-ro)<=1e-15 and np.max(np.diff(new))<=1e-14
    start=time.perf_counter()
    for _ in range(20):model.evaluate(points,fixtures[1])
    elapsed=(time.perf_counter()-start)/20
    result=dict(status='NUMERIC_EXPRESSION_CHECK_PASS_NOT_ART',point_count=len(points),baseline_max_abs_error=float(baseline_error),H_max_abs_error_by_fixture=errors,minimum_H_minus_F11=nest,lower_Z134_bit_exact=True,H11_nesting=True,hinge_derivative_max_abs_error=float(np.max(abs(numerical-expected_derivative))),profile_upper_monotonic=True,evaluate_4096_seconds=elapsed,metadata=model.metadata(fixtures[1]))
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':main()
