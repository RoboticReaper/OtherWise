# Recommendation comparison

Experimental proxy scores; session assistant judged blinded source-backed items. Actual personal curiosity is unmeasured. No production deployment.

| System | Connection | Discovery | Depth | Variety | p95 seconds |
|---|---:|---:|---:|---:|---:|
| V0 | 0.4125 | 0.3023 | 0.3316 | 0.3229 | 0.0606 |
| V1 | 0.4792 | 0.3565 | 0.3814 | 0.3780 | 0.0883 |
| V2 | 0.4667 | 0.3463 | 0.3723 | 0.3705 | 0.0751 |
| V3 | 0.4667 | 0.3471 | 0.3810 | 0.3695 | 0.0197 |
| A-connection | 0.7583 | 0.6071 | 0.6402 | 0.6131 | 0.0388 |
| K-connection | 0.8083 | 0.6150 | 0.6533 | 0.6477 | 0.0316 |
| K-depth | 0.7458 | 0.6273 | 0.6580 | 0.6101 | 0.0315 |
| K-discovery | 0.7833 | 0.6210 | 0.6561 | 0.6307 | 0.0313 |
| K-variety | 0.7542 | 0.6090 | 0.6395 | 0.6103 | 0.0317 |
| K-no-content | 0.8042 | 0.6133 | 0.6473 | 0.6453 | 0.0319 |
| K-canonical | 0.8042 | 0.6385 | 0.6795 | 0.6488 | 0.0311 |
| K-literal | 0.8083 | 0.6356 | 0.6730 | 0.6510 | 0.0310 |
| K-near | 0.4667 | 0.3438 | 0.3723 | 0.3692 | 0.0086 |
| K-wide | 0.7708 | 0.6223 | 0.6530 | 0.6247 | 0.0318 |
| K-deep-content | 0.6708 | 0.5800 | 0.6021 | 0.5535 | 0.0312 |
| K-diverse | 0.6833 | 0.5725 | 0.5977 | 0.5613 | 0.0308 |

Per-metric experimental winners: {"connection": "K-literal", "discovery": "K-canonical", "depth": "K-canonical", "variety": "K-literal"}

Variety uses a separately frozen hashed TF-IDF angular space. It measures lexical diversity, with weaker semantic interpretation than an independent semantic encoder.
These scores depend on a single assistant rubric. A second judge and repeat/order audit are required before an operational selection. Missing grades and integrity failures prevent selection.
