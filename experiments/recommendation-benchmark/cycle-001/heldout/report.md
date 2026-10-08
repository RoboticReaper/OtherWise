# Recommendation comparison

Experimental proxy scores; session assistant judged blinded source-backed items. Actual personal curiosity is unmeasured. No production deployment.

| System | Connection | Discovery | Depth | Variety | p95 seconds |
|---|---:|---:|---:|---:|---:|
| V0 | 1.0000 | 0.7656 | 0.8183 | 0.7878 | 0.0665 |
| V1 | 1.0000 | 0.7633 | 0.8050 | 0.7890 | 0.0396 |
| V2 | 1.0000 | 0.7633 | 0.8050 | 0.7890 | 0.0938 |
| V3 | 0.9889 | 0.7700 | 0.8256 | 0.7797 | 0.0194 |
| A-connection | 0.8667 | 0.6928 | 0.7308 | 0.6888 | 0.0348 |

Per-metric experimental winners: {"connection": "V1", "discovery": "V3", "depth": "V3", "variety": "V1"}

Variety uses a separately frozen hashed TF-IDF angular space. It measures lexical diversity, with weaker semantic interpretation than an independent semantic encoder.
These scores depend on a single assistant rubric. A second judge and repeat/order audit are required before an operational selection. Missing grades and integrity failures prevent selection.
