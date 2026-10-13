"""M3 — Purchasing Strategy: break-even, tier choice, spot-checkpoint sim (deck §4).

Run: python missions/m3_purchasing.py
"""
from __future__ import annotations
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from missions._common import load_csv, num, catalog_by_type
from finops import pricing, sustainability

DAYS = 30


def carbon_aware_scheduling(jobs: list[dict], cat: dict) -> dict:
    """Extension 5: Analyze shifting interruptible workloads to green cloud regions."""
    interruptible_jobs = [j for j in jobs if bool(int(num(j["interruptible"])))]
    total_kwh = 0.0
    job_details = []

    for j in interruptible_jobs:
        gtype = j["gpu_type"]
        ngpu = int(num(j["num_gpus"]))
        hpd = num(j["hours_per_day"])
        watts = num(cat[gtype]["watts"])
        monthly_hours = hpd * DAYS * ngpu
        kwh = (monthly_hours * watts) / 1000.0
        total_kwh += kwh
        job_details.append({
            "job_id": j["job_id"],
            "gpu_type": gtype,
            "num_gpus": ngpu,
            "monthly_hours": monthly_hours,
            "watts": watts,
            "kwh": round(kwh, 1),
        })

    region_comparison = {}
    for region, gco2_kwh in sustainability.REGION_CARBON.items():
        price_kwh = sustainability.REGION_PRICE_KWH.get(region, 0.12)
        carbon_kg = (total_kwh * gco2_kwh) / 1000.0
        power_cost = total_kwh * price_kwh
        region_comparison[region] = {
            "carbon_intensity_gco2_kwh": gco2_kwh,
            "price_kwh": price_kwh,
            "carbon_kg": round(carbon_kg, 1),
            "power_cost_usd": round(power_cost, 2),
        }

    base_reg = "us-east-1"
    green_reg = "europe-north1"
    base_carbon = region_comparison[base_reg]["carbon_kg"]
    green_carbon = region_comparison[green_reg]["carbon_kg"]
    carbon_saved_kg = base_carbon - green_carbon
    carbon_saved_pct = (carbon_saved_kg / base_carbon * 100.0) if base_carbon else 0.0

    base_power_cost = region_comparison[base_reg]["power_cost_usd"]
    green_power_cost = region_comparison[green_reg]["power_cost_usd"]
    power_saved_usd = base_power_cost - green_power_cost

    return {
        "interruptible_kwh": round(total_kwh, 1),
        "job_details": job_details,
        "region_comparison": region_comparison,
        "base_region": base_reg,
        "green_region": green_reg,
        "carbon_saved_kg": round(carbon_saved_kg, 1),
        "carbon_saved_pct": round(carbon_saved_pct, 1),
        "power_saved_usd": round(power_saved_usd, 2),
    }


def run(verbose: bool = True) -> dict:
    jobs = load_csv("workloads.csv")
    cat = catalog_by_type()
    on_demand_monthly = optimized_monthly = 0.0
    recs = []
    for j in jobs:
        gtype = j["gpu_type"]
        ngpu = int(num(j["num_gpus"]))
        hpd = num(j["hours_per_day"])
        interruptible = bool(int(num(j["interruptible"])))
        c = cat[gtype]
        gpu_hours = hpd * DAYS * ngpu
        od = num(c["on_demand_hr"])
        on_demand_cost = gpu_hours * od

        tier = pricing.recommend_tier(hpd, interruptible)
        if tier == "spot":
            sim = pricing.spot_checkpoint_cost(gpu_hours, num(c["spot_hr"]), od)
            opt_cost = sim["spot_cost"]
        elif tier == "reserved":
            opt_cost = gpu_hours * num(c["reserved_3yr_hr"])
        else:
            opt_cost = on_demand_cost

        on_demand_monthly += on_demand_cost
        optimized_monthly += opt_cost
        recs.append({"job_id": j["job_id"], "gpu_type": gtype, "tier": tier,
                     "on_demand": round(on_demand_cost), "optimized": round(opt_cost)})

    savings = on_demand_monthly - optimized_monthly
    savings_pct = savings / on_demand_monthly * 100 if on_demand_monthly else 0.0

    carbon_analysis = carbon_aware_scheduling(jobs, cat)

    if verbose:
        print("== M3 Purchasing Strategy ==")
        print(f"break-even utilization @ 45% reserved discount = {pricing.break_even_utilization(0.45):.0%}")
        print(f"{'job':18}{'gpu':7}{'tier':11}{'on-demand':>12}{'optimized':>12}")
        for r in recs:
            print(f"{r['job_id']:18}{r['gpu_type']:7}{r['tier']:11}${r['on_demand']:>11,}${r['optimized']:>11,}")
        print(f"\nmonthly: on-demand ${on_demand_monthly:,.0f} -> optimized ${optimized_monthly:,.0f}  ({savings_pct:.1f}% saved)")

        print("\n-- Extension 5: Carbon-aware Scheduling (5-Region Comparison) --")
        print(f"Interruptible workloads total electricity: {carbon_analysis['interruptible_kwh']:,} kWh/month across {len(carbon_analysis['job_details'])} jobs")
        print(f"{'region':17}{'carbon(g/kWh)':15}{'price($/kWh)':14}{'carbon(kg)':14}{'power_cost':>12}")
        for reg, data in carbon_analysis["region_comparison"].items():
            print(f"{reg:17}{data['carbon_intensity_gco2_kwh']:<15}{data['price_kwh']:<14.3f}{data['carbon_kg']:<14.1f}${data['power_cost_usd']:>11.2f}")
        print(f"\nRouting interruptible jobs {carbon_analysis['base_region']} -> {carbon_analysis['green_region']}:")
        print(f"  Carbon reduction : {carbon_analysis['carbon_saved_kg']} kg CO2e ({carbon_analysis['carbon_saved_pct']}% saved)")
        print(f"  Power cost delta : -${carbon_analysis['power_saved_usd']:.2f}/month")
        print("  Latency trade-off: 0ms user impact (workloads are asynchronous batch/train)")

    return {
        "recommendations": recs,
        "on_demand_monthly": round(on_demand_monthly),
        "optimized_monthly": round(optimized_monthly),
        "savings_pct": round(savings_pct, 1),
        "carbon_scheduling": carbon_analysis,
    }


if __name__ == "__main__":
    run()

