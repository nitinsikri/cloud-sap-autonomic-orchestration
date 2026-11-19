# Cloud-SAP: Multi-Tier Autonomic Resource Orchestration (Simulator)

Reference implementation of the method described in:

**Nitin Sikri.** *Multi-Tier Autonomic Resource Orchestration Framework for Dynamic Service Elasticity across Federated Cloud Environments.* Proceedings of the International Conference on Responsible, Risk-aware, and Regulated AI (RRRAI 2026), Atlantis Press (Springer Nature), 2026. DOI: [10.2991/978-94-6239-723-1_31](https://doi.org/10.2991/978-94-6239-723-1_31)

> **Reference implementation.** This repository was written in November 2026, after the paper was accepted, to illustrate the method described in the paper and to make it easy to reuse. It is **not** the original experimental code, it runs on **synthetic data**, and its numbers will **differ** from the results reported in the paper. Please cite the paper for the method and its reported results.

## What the paper proposes

Cloud-SAP keeps tenant QoS with a hierarchy of autonomic managers – execution-environment and container managers, application-stack managers, cloud-instance provisioners and a federation manager – each running a MAPE loop. Coordinated vertical and horizontal scaling across layers, with cloud bursting to federated providers, is compared with single-layer scaling.

## What this repository contains

- `cloudsap/model.py` – providers (private, two public), quotas, prices, boot times; synthetic traffic with a daily cycle and flash crowds
- `cloudsap/managers.py` – shared knowledge base with cooldowns and policies; container manager (vertical then horizontal scaling); instance manager with cheapest-first provisioning and federation bursting
- `cloudsap/simulate.py` – multi-layer controller, single-layer VM autoscaler baseline, comparison
- `examples/compare_controllers.py`, `tests/`

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. python examples/compare_controllers.py
python -m pytest -q
```



## How it maps to the paper

| Paper | Code |
|---|---|
| Managed resources hierarchy (3.2) | `State`, `Provider` |
| MAPE autonomic manager + knowledge base (3.3) | `ContainerManager`, `InstanceManager`, `Knowledge` |
| Federation manager / cloud bursting (3.4, 5.4) | `InstanceManager(federation=True)` |
| Single-layer comparison (5.2–5.3) | `run_single_layer`, `compare` |

## Limitations

- A discrete-time Python simulator replaces the paper's OpenNebula proof of concept.
- In this simplified simulator the multi-layer controller mainly reduces SLA-violation minutes at a similar cost; it does **not** reproduce the paper's 20 % cost reduction, which came from the real deployment.
- The application-stack manager is folded into the container manager.

## How to cite

If you use this code, please cite the paper:

```bibtex
@inproceedings{sikri2026cloudsap,
  author    = {Sikri, Nitin},
  title     = {Multi-Tier Autonomic Resource Orchestration Framework for Dynamic Service Elasticity across Federated Cloud Environments},
  booktitle = {Proceedings of the International Conference on Responsible, Risk-aware, and Regulated AI (RRRAI 2026)},
  publisher = {Atlantis Press (Springer Nature)},
  year      = {2026},
  doi       = {10.2991/978-94-6239-723-1_31}
}
```

GitHub also shows a **"Cite this repository"** button generated from `CITATION.cff`.

## Licence

MIT – see [LICENSE](LICENSE).
