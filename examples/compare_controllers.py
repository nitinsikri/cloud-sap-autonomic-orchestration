"""Three days of synthetic traffic with flash crowds: single-layer VM autoscaling
vs coordinated multi-layer control, with and without federation (cloud bursting)."""
from cloudsap import compare

rows = compare(days=3)
base = rows[0]["cost_usd"]
print(f"{'controller':28s} {'cost $':>8s} {'vs single':>10s} {'SLA-miss min':>13s}")
for r in rows:
    print(f"{r['controller']:28s} {r['cost_usd']:8.2f} {r['cost_usd'] / base - 1:+10.1%} "
          f"{r['sla_violation_minutes']:13d}")
