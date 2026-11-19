import numpy as np

from cloudsap import run_multilayer, run_single_layer, workload, DEFAULT_PROVIDERS


def test_workload_shape():
    w = workload(1440, seed=1)
    assert len(w) == 1440 and w.min() >= 10


def test_controllers_run_and_cost_positive():
    w = workload(720, seed=2)
    for r in (run_single_layer(w), run_multilayer(w), run_multilayer(w, federation=False)):
        assert r["cost_usd"] > 0
        assert 0 <= r["sla_violation_share"] <= 1


def test_quota_respected():
    w = np.full(600, 50_000.0)          # far more than the quota can serve
    r = run_multilayer(w)
    vms = r["final_state"][2]
    for name, n in vms.items():
        assert n <= DEFAULT_PROVIDERS[name].quota_vms
