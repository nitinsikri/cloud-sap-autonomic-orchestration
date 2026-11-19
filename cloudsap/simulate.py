"""Run the multi-layer (Cloud-SAP style) controller and a single-layer baseline."""
from __future__ import annotations

import math

import numpy as np

from .managers import ContainerManager, InstanceManager, Knowledge
from .model import DEFAULT_PROVIDERS, State, RPS_PER_CORE, workload


def run_multilayer(rps: np.ndarray, providers=DEFAULT_PROVIDERS, federation: bool = True) -> dict:
    s = State(vms={"private": 2})
    kb = Knowledge()
    cm, im = ContainerManager(), InstanceManager(federation)
    cost = violations = 0.0
    for now, r in enumerate(rps):
        cm.step(now, r, s, kb, providers)
        im.step(now, s, kb, providers)
        usable = min(s.containers * s.container_cpu, s.cores(providers))
        if r / RPS_PER_CORE > usable:
            violations += 1
        cost += sum(n * providers[p].vm_price_hour for p, n in s.vms.items()) / 60
        kb.history.append((now, s.containers, round(s.container_cpu, 2), dict(s.vms)))
    return _summary("multi-layer" + ("" if federation else " (no federation)"), rps, cost,
                    violations, kb)


def run_single_layer(rps: np.ndarray, providers=DEFAULT_PROVIDERS, high=0.8, low=0.4,
                     cooldown=10) -> dict:
    """Baseline: a single VM-level autoscaler. Containers are fixed-size and one per
    core, so every change in demand is handled by adding or removing VMs. It uses the
    private cloud first and then one public provider (no federation broker)."""
    order = [providers["private"], providers["public_a"]]
    vms = {"private": 2, "public_a": 0}
    pending, last = [], -10 ** 9
    cost = violations = 0.0
    cores = lambda: sum(vms[p.name] * p.vm_cores for p in order)
    for now, r in enumerate(rps):
        util = r / RPS_PER_CORE / cores()
        if util > high and now - last >= cooldown:
            need = r / RPS_PER_CORE / 0.65 - cores()
            for prov in order:
                while need > 0 and vms[prov.name] + sum(1 for _, q in pending if q == prov.name) < prov.quota_vms:
                    pending.append((now + prov.boot_minutes, prov.name))
                    need -= prov.vm_cores
            last = now
        elif util < low and cores() > 8 and now - last >= cooldown:
            for prov in reversed(order):                 # release expensive VMs first
                if vms[prov.name]:
                    vms[prov.name] -= 1
                    break
            last = now
        for t, name in [x for x in pending if x[0] <= now]:
            vms[name] += 1
        pending = [x for x in pending if x[0] > now]
        if r / RPS_PER_CORE > cores():
            violations += 1
        cost += sum(vms[p.name] * p.vm_price_hour for p in order) / 60
    return _summary("single-layer", rps, cost, violations, None)


def _summary(name, rps, cost, violations, kb):
    out = {"controller": name, "cost_usd": round(cost, 2),
           "sla_violation_minutes": int(violations),
           "sla_violation_share": round(violations / len(rps), 4)}
    if kb is not None:
        out["final_state"] = kb.history[-1][1:]
    return out


def compare(days: int = 3, seed: int = 0):
    rps = workload(days * 1440, seed)
    return [run_single_layer(rps), run_multilayer(rps, federation=False), run_multilayer(rps)]
