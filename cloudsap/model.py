"""Resource hierarchy and workload for the Cloud-SAP simulator.

Hierarchy (paper Sect. 3): containers (EAC/CWO) run inside VMs (CP) of a
provider; the federation manager (FC) can rent VMs from other providers.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class Provider:
    name: str
    vm_price_hour: float
    vm_cores: int = 8
    quota_vms: int = 20
    boot_minutes: int = 3


@dataclass
class State:
    container_cpu: float = 1.0                  # cores per container (vertical knob)
    containers: int = 2                         # replicas (horizontal knob)
    vms: dict = field(default_factory=dict)     # provider -> VM count
    pending: list = field(default_factory=list) # (ready_at_minute, provider)

    def cores(self, providers) -> int:
        return sum(n * providers[p].vm_cores for p, n in self.vms.items())


DEFAULT_PROVIDERS = {
    "private": Provider("private", 0.10, quota_vms=6),
    "public_a": Provider("public_a", 0.40, quota_vms=40),
    "public_b": Provider("public_b", 0.34, quota_vms=40, boot_minutes=5),
}


def workload(minutes: int = 3 * 24 * 60, seed: int = 0, base: float = 1000.0) -> np.ndarray:
    """Requests per second, minute by minute: daily cycle, noise and bursts."""
    rng = np.random.default_rng(seed)
    t = np.arange(minutes)
    daily = 1 + 0.6 * np.sin((t % 1440) / 1440 * 2 * np.pi - np.pi / 2)
    rps = base * daily * (1 + rng.normal(0, 0.05, minutes))
    for s in rng.choice(minutes - 120, 6, replace=False):
        rps[s:s + rng.integers(20, 90)] *= rng.uniform(1.8, 3.0)        # flash crowds
    return np.clip(rps, 10, None)


RPS_PER_CORE = 60.0          # requests one core can serve within the latency target
