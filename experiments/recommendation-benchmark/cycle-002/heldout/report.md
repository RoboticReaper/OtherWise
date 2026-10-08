# Recommendation comparison

Experimental proxy scores; session assistant judged blinded source-backed items. Actual personal curiosity is unmeasured. No production deployment.

| System | Connection | Discovery | Depth | Variety | p95 seconds |
|---|---:|---:|---:|---:|---:|
| V0 | 0.6389 | 0.5017 | 0.5481 | 0.5112 | 0.0620 |
| V1 | 0.7444 | 0.5839 | 0.6386 | 0.5928 | 0.0427 |
| V2 | 0.7444 | 0.5839 | 0.6386 | 0.5928 | 0.0829 |
| V3 | 0.7444 | 0.5828 | 0.6369 | 0.5930 | 0.0203 |
| K-connection | 0.7833 | 0.6303 | 0.6763 | 0.6315 | 0.0284 |
| K-canonical | 0.6889 | 0.5661 | 0.6047 | 0.5606 | 0.0289 |
| K-literal | 0.7056 | 0.5733 | 0.6122 | 0.5691 | 0.0284 |
| K-wide | 0.6556 | 0.5375 | 0.5760 | 0.5302 | 0.0288 |

Per-metric experimental winners: {"connection": "K-connection", "discovery": "K-connection", "depth": "K-connection", "variety": "K-connection"}

Variety uses a separately frozen hashed TF-IDF angular space. It measures lexical diversity, with weaker semantic interpretation than an independent semantic encoder.
These scores depend on a single assistant rubric. A second judge and repeat/order audit are required before an operational selection. Missing grades and integrity failures prevent selection.
