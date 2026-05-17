"""
Example: SSE 50 Homogeneity Index Analysis
"""
from hi_factor import HomogeneityIndex
import json

# SSE 50 constituent stocks
SSE50_STOCKS = [
    "600028", "600030", "600031", "600036", "600050", "600104", "600111",
    "600150", "600276", "600309", "600406", "600519", "600690", "600760",
    "600809", "600887", "600900", "601012", "601088", "601127", "601166",
    "601211", "601225", "601288", "601318", "601328", "601398", "601601",
    "601628", "601658", "601668", "601728", "601816", "601857", "601888",
    "601899", "601919", "601985", "601988", "603019", "603259", "603501", "603993"
]

def main():
    # Initialize factor
    factor = HomogeneityIndex(
        stock_list=SSE50_STOCKS,
        db_path="D:/qclaw/db/沪市主板/database.db",  # Update this path
        correlation_threshold=0.5,
        lookback_days=20
    )
    
    # Calculate for 2024
    print("SSE 50 Homogeneity Index Analysis - 2024")
    print("=" * 60)
    
    periods = [
        ("2024-01-01", "2024-01-31", "January"),
        ("2024-02-01", "2024-02-29", "February"),
        ("2024-03-01", "2024-03-31", "March"),
        ("2024-07-01", "2024-07-31", "July"),
        ("2024-08-01", "2024-08-31", "August"),
        ("2024-09-01", "2024-09-30", "September"),
        ("2024-10-01", "2024-10-31", "October"),
        ("2024-11-01", "2024-11-30", "November"),
        ("2024-12-01", "2024-12-31", "December"),
    ]
    
    results = []
    for start, end, label in periods:
        result = factor.calculate(start, end)
        if result:
            results.append({
                "period": label,
                "hi": result["homogeneity_index"],
                "signal": result["signal"],
                "n_orbits": result["n_orbits"],
                "max_orbit": result["max_orbit_size"]
            })
            print(f"\n{label}:")
            print(f"  HI: {result['homogeneity_index']:.4f}")
            print(f"  Signal: {result['signal'].upper()}")
            print(f"  Orbits: {result['n_orbits']}, Max: {result['max_orbit_size']}")
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    for r in results:
        print(f"{r['period']:12s} HI={r['hi']:.4f} [{r['signal'].upper():6s}]")
    
    # Save results
    with open("sse50_2024_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nResults saved to sse50_2024_results.json")

if __name__ == "__main__":
    main()
