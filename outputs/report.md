# NimbusAI — GPU Cost Optimization Report

**Period:** monthly  
**Baseline spend:** $27,133  
**Optimized spend:** $14,626  
**Projected savings:** $12,507  (**46%**)

## Savings by lever

| Lever | Savings (USD) |
|---|---|
| Inference (cascade/cache/batch) | $1,212 |
| Purchasing (spot/reserved) | $10,040 |
| Right-size util-lies | $655 |
| Kill idle GPUs | $600 |

## Sustainability

- Energy per query: 0.24 Wh
- Carbon per query: 0.091 gCO2e
- Cheapest+cleanest region: europe-north1

## Advanced FinOps Extensions

### Extension 3: Prompt Caching Economics (`cache_is_worth_it`)
- Small model break-even reads: 1.39 reads
- Large model break-even reads: 1.39 reads
- Observed average reuse: ~600.0 reads (positive ROI: True)

### Extension 5: Carbon-aware Scheduling (Shift Interruptible Workloads)
- Workloads eligible: 5 batch/training jobs (4,227.0 kWh/month)
- Target green region: `europe-north1` (vs baseline `us-east-1`)
- Carbon reduction: 1,479.5 kg CO2e (**92.1% cut**)
- Electricity cost delta: -$126.81/month
- Latency impact: 0ms user impact (asynchronous batch processing)

_Figures are June-2026 as-of snapshots; re-baseline before acting._