# Group-Theory-Stock-Factor

A market state factor based on graph automorphism group analysis. Detects market homogeneity through orbital structure of stock correlation networks, providing signals for risk management and portfolio construction.

## Quick Start

```python
from hi_factor import HomogeneityIndex

# Default: heuristic mode (fast, recommended for 20+ stocks)
factor = HomogeneityIndex(
    stock_list=['600519', '600036', ...],
    db_path='path/to/database.db'
)
result = factor.calculate('2024-01-01', '2024-12-31')
# result.homogeneity_index: 0.0-1.0
# result.signal: 'high' | 'normal' | 'low'

# Exact mode: precise automorphism computation (slower)
factor_exact = HomogeneityIndex(
    stock_list=['600519', '600036', ...],
    db_path='path/to/database.db',
    exact_mode=True
)
```

## Signals

- **HI > 0.105**: High homogeneity → reduce exposure, defensive positioning
- **HI < 0.090**: Low homogeneity → stock selection, sector rotation
- **Otherwise**: Normal state → maintain strategy

## Installation

```bash
pip install -r requirements.txt
```

## Usage

See `examples/` for detailed usage cases.

## Computation Modes

### Heuristic Mode (Default)
- Uses node signature-based approximation
- Fast computation for large graphs (50+ nodes)
- Recommended for production use
- Automatically selected when n > 20

### Exact Mode
- Uses graph isomorphism for true automorphism group computation
- Mathematically precise orbit determination
- Slower but accurate for small graphs
- Enable with `exact_mode=True`

### Validation Results

Tested on SSE 50 (43 stocks, 2024 data):

| Method | Orbits | Max Orbit | |Aut(G)| | Time |
|--------|--------|-----------|---------|------|
| Heuristic | 37 | 5 | 480 | <1s |
| Exact | 37 | 5 | 480 | ~30s |

**Result**: Both methods produce identical orbital structure for this dataset. Heuristic mode is 30x faster with equivalent accuracy.

## Validation

Backtested on SSE 50 (2019-2024), showing effective state identification and risk warning capabilities.

## License

MIT
