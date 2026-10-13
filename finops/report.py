"""Report assembly — the lab's deliverable: baseline vs optimized + savings chart."""
from __future__ import annotations


def build_report(baseline_usd: float, optimized_usd: float, levers: dict,
                 sustainability: dict | None = None, period: str = "monthly",
                 extensions: dict | None = None) -> str:
    """Return a markdown cost-optimization report."""
    savings = baseline_usd - optimized_usd
    pct = (savings / baseline_usd * 100.0) if baseline_usd > 0 else 0.0
    lines = [
        "# NimbusAI — GPU Cost Optimization Report",
        "",
        f"**Period:** {period}  ",
        f"**Baseline spend:** ${baseline_usd:,.0f}  ",
        f"**Optimized spend:** ${optimized_usd:,.0f}  ",
        f"**Projected savings:** ${savings:,.0f}  (**{pct:.0f}%**)",
        "",
        "## Savings by lever",
        "",
        "| Lever | Savings (USD) |",
        "|---|---|",
    ]
    for name, amount in levers.items():
        lines.append(f"| {name} | ${amount:,.0f} |")
    if sustainability:
        lines += [
            "",
            "## Sustainability",
            "",
            f"- Energy per query: {sustainability.get('wh_per_query', 0):.2f} Wh",
            f"- Carbon per query: {sustainability.get('carbon_g', 0):.3f} gCO2e",
            f"- Cheapest+cleanest region: {sustainability.get('best_region', 'n/a')}",
        ]
    if extensions:
        lines += [
            "",
            "## Advanced FinOps Extensions",
            "",
            "### Extension 3: Prompt Caching Economics (`cache_is_worth_it`)",
            f"- Small model break-even reads: {extensions.get('cache', {}).get('small_break_even_reads', 'N/A')} reads",
            f"- Large model break-even reads: {extensions.get('cache', {}).get('large_break_even_reads', 'N/A')} reads",
            f"- Observed average reuse: ~{extensions.get('cache', {}).get('avg_observed_reads', 'N/A')} reads (positive ROI: {extensions.get('cache', {}).get('cache_is_worth_it', True)})",
            "",
            "### Extension 5: Carbon-aware Scheduling (Shift Interruptible Workloads)",
            f"- Workloads eligible: {len(extensions.get('carbon', {}).get('job_details', []))} batch/training jobs ({extensions.get('carbon', {}).get('interruptible_kwh', 0):,} kWh/month)",
            f"- Target green region: `{extensions.get('carbon', {}).get('green_region', 'europe-north1')}` (vs baseline `{extensions.get('carbon', {}).get('base_region', 'us-east-1')}`)",
            f"- Carbon reduction: {extensions.get('carbon', {}).get('carbon_saved_kg', 0):,} kg CO2e (**{extensions.get('carbon', {}).get('carbon_saved_pct', 0)}% cut**)",
            f"- Electricity cost delta: -${extensions.get('carbon', {}).get('power_saved_usd', 0):,.2f}/month",
            "- Latency impact: 0ms user impact (asynchronous batch processing)",
        ]
    lines += ["", "_Figures are June-2026 as-of snapshots; re-baseline before acting._"]
    return "\n".join(lines)



def savings_waterfall(levers: dict, path: str) -> str:
    """Write a simple savings bar chart PNG. Returns the path. No-op if matplotlib absent."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return ""
    names = list(levers.keys())
    vals = [levers[n] for n in names]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(names, vals, color="#2e548a")
    ax.set_ylabel("Savings (USD / month)")
    ax.set_title("GPU cost savings by FinOps lever")
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path
