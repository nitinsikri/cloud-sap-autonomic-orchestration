"""Autonomic managers, each a Monitor-Analyse-Plan-Execute loop with a shared
knowledge base (history, cooldowns, policies)."""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from .model import State, RPS_PER_CORE


@dataclass
class Knowledge:
    history: list = field(default_factory=list)
    last_action: dict = field(default_factory=dict)
    policy: dict = field(default_factory=lambda: {
        "target_util": 0.65, "high": 0.80, "low": 0.40,
        "min_cpu": 0.5, "max_cpu": 4.0, "cooldown": {"eac": 2, "cwo": 3, "cp": 10, "fc": 15}})

    def cool(self, who, now):
        return now - self.last_action.get(who, -10 ** 9) >= self.policy["cooldown"][who]


class ContainerManager:
    """EAC + CWO: vertical resize first (cheap, instant), then add/remove replicas."""

    def step(self, now, rps, s: State, kb: Knowledge, providers):
        demand_cores = rps / RPS_PER_CORE
        alloc = s.containers * s.container_cpu
        util = demand_cores / alloc
        p = kb.policy
        if util > p["high"] and kb.cool("eac", now) and s.container_cpu < p["max_cpu"]:
            s.container_cpu = min(p["max_cpu"], s.container_cpu * 1.5)
            kb.last_action["eac"] = now
        elif util > p["high"] and kb.cool("cwo", now):
            s.containers = math.ceil(demand_cores / (p["target_util"] * s.container_cpu))
            kb.last_action["cwo"] = now
        elif util < p["low"] and kb.cool("cwo", now):
            if s.containers > 2:
                s.containers = max(2, math.ceil(demand_cores / (p["target_util"] * s.container_cpu)))
                kb.last_action["cwo"] = now
            elif s.container_cpu > p["min_cpu"] and kb.cool("eac", now):
                s.container_cpu = max(p["min_cpu"], s.container_cpu / 1.5)
                kb.last_action["eac"] = now


class InstanceManager:
    """CP: keep enough VM cores for the containers' allocation, cheapest provider first;
    FC: when local quota is exhausted, burst to the cheapest federated provider."""

    def __init__(self, federation: bool = True):
        self.federation = federation

    def step(self, now, s: State, kb: Knowledge, providers):
        need = s.containers * s.container_cpu
        have = s.cores(providers) + sum(providers[p].vm_cores for _, p in s.pending)
        if need > have and kb.cool("cp", now):
            order = sorted(providers.values(), key=lambda p: p.vm_price_hour)
            if not self.federation:
                order = [providers["private"], providers["public_a"]]
            for prov in order:
                while need > have and s.vms.get(prov.name, 0) + sum(
                        1 for _, q in s.pending if q == prov.name) < prov.quota_vms:
                    s.pending.append((now + prov.boot_minutes, prov.name))
                    have += prov.vm_cores
                if need <= have:
                    break
            kb.last_action["cp"] = now
        elif need < 0.75 * s.cores(providers) and kb.cool("cp", now):
            # release the most expensive VM first
            for name in sorted(s.vms, key=lambda n: -providers[n].vm_price_hour):
                if s.vms[name] and s.cores(providers) - providers[name].vm_cores >= need / 0.85:
                    s.vms[name] -= 1
                    kb.last_action["cp"] = now
                    break
        ready = [x for x in s.pending if x[0] <= now]
        s.pending = [x for x in s.pending if x[0] > now]
        for _, name in ready:
            s.vms[name] = s.vms.get(name, 0) + 1
