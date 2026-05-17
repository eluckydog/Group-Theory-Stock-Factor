# Group-Theory-Stock-Factor

## Description

A market state factor based on graph automorphism group analysis. Computes homogeneity index from stock correlation networks to identify market regimes.

## Core Concepts

### Homogeneity Index (HI)

Weighted composite of:
- Base homogeneity rate (orbit count / stock count)
- Max cluster ratio (largest orbit / stock count)
- Graph density (edges / max possible edges)
- Concentration (entropy complement)

### Graph Construction

1. Calculate return correlation matrix
2. Threshold filtering (default: 0.5)
3. Build adjacency graph
4. Compute orbital structure (see Computation Modes)

### Computation Modes

**Heuristic Mode (Default)**
- Uses node signature-based approximation (degree + neighbor structure)
- Fast computation: O(n²)
- Recommended for graphs with 20+ nodes
- Provides good approximation for market state identification

**Exact Mode**
- Uses graph isomorphism (NetworkX GraphMatcher) for true automorphism group
- Computes precise orbital structure
- Computationally expensive: O(n³) worst case
- Recommended for small graphs (≤20 nodes) or validation purposes

The heuristic mode is sufficient for most practical applications. The exact mode
is provided for mathematical rigor and validation of the approximation quality.

## Usage

### Basic

```python
from hi_factor import HomogeneityIndex

hi = HomogeneityIndex(
    stock_list=['600519', '600036', ...],
    db_path='path/to/database.db'
)

result = hi.calculate('2024-01-01', '2024-12-31')
print(f"HI: {result['homogeneity_index']:.4f}")
```

### With Signal

```python
if result['homogeneity_index'] > 0.105:
    signal = "HIGH_HOMOGENEITY"
elif result['homogeneity_index'] < 0.090:
    signal = "LOW_HOMOGENEITY"
else:
    signal = "NORMAL"
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| correlation_threshold | 0.5 | Edge threshold for graph construction |
| lookback_days | 20 | Window for return calculation |
| min_stocks | 10 | Minimum valid stocks required |

## Output

```json
{
  "homogeneity_index": 0.0980,
  "n_orbits": 37,
  "max_orbit_size": 5,
  "n_stocks": 43,
  "graph_density": 0.162
}
```

## Examples

See `examples/sse50_analysis.py` for complete analysis workflow.

## License

MIT
