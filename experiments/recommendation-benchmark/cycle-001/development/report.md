# Recommendation comparison

Experimental proxy scores; session assistant judged blinded source-backed items. Actual personal curiosity is unmeasured. No production deployment.

| System | Connection | Discovery | Depth | Variety | p95 seconds |
|---|---:|---:|---:|---:|---:|
| V0 | 0.0600 | 0.0450 | 0.0495 | 0.0440 | 0.0589 |
| V1 | 0.1667 | 0.1310 | 0.1372 | 0.1314 | 0.0386 |
| V2 | 0.1467 | 0.1147 | 0.1227 | 0.1194 | 0.0883 |
| V3 | 0.1467 | 0.1147 | 0.1227 | 0.1194 | 0.0193 |
| V3-no-lexical | 0.1467 | 0.1147 | 0.1227 | 0.1194 | 0.0153 |
| V3-no-graph | 0.1467 | 0.1147 | 0.1227 | 0.1194 | 0.0075 |
| V3-no-ranking | 0.1467 | 0.1147 | 0.1227 | 0.1194 | 0.0385 |
| R-connection | 0.1467 | 0.1147 | 0.1227 | 0.1194 | 0.0203 |
| R-depth | 0.1467 | 0.1147 | 0.1227 | 0.1194 | 0.0198 |
| R-outward | 0.1467 | 0.1147 | 0.1227 | 0.1194 | 0.0197 |
| R-variety | 0.1467 | 0.1147 | 0.1227 | 0.1194 | 0.0195 |
| R-small-pool | 0.1467 | 0.1147 | 0.1227 | 0.1194 | 0.0198 |
| R-balance | 0.1467 | 0.1147 | 0.1227 | 0.1194 | 0.0195 |
| R-band | 0.1467 | 0.1147 | 0.1227 | 0.1194 | 0.0193 |
| A-adaptive | 0.6333 | 0.5250 | 0.5428 | 0.5155 | 0.0402 |
| A-connection | 0.6600 | 0.5503 | 0.5705 | 0.5400 | 0.0387 |
| A-depth | 0.6533 | 0.5450 | 0.5628 | 0.5362 | 0.0388 |
| A-variety | 0.5800 | 0.4787 | 0.4970 | 0.4726 | 0.0387 |
| A-outward | 0.5933 | 0.4877 | 0.5038 | 0.4843 | 0.0389 |

Per-metric experimental winners: {"connection": "A-connection", "discovery": "A-connection", "depth": "A-connection", "variety": "A-connection"}

Variety uses a separately frozen hashed TF-IDF angular space. It measures lexical diversity, with weaker semantic interpretation than an independent semantic encoder.
These scores depend on a single assistant rubric. A second judge and repeat/order audit are required before an operational selection. Missing grades and integrity failures prevent selection.
