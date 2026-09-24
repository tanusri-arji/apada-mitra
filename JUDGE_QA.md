# APADA MITRA — SIH Judge Q&A Guide

Here are the honest, direct answers you must provide if the judges ask probing questions about the system's infrastructure, data sources, and alerting mechanisms. 

### 1. Where are you getting live Central Water Commission (CWC) data?
**Honest Answer:**  
"We do not have a live integration with the CWC API because their real-time telemetry is restricted and not publicly accessible. In the codebase, the CWC data adapter returns `None` and falls back to a deterministic flow-accumulation model. We designed the data pipeline to easily plug into the CWC API if we are granted access by the government."

### 2. How was your LSTM model trained? What data did you use?
**Honest Answer:**  
"The LSTM hydrograph prediction model was trained entirely on synthetic, physics-based catchment data that we generated to mimic extreme cloudburst events. We did not train it on historical CWC flood data because high-resolution historical flood stage datasets for these micro-watersheds were not available. The model (a lightweight 463 KB JSON weights file) demonstrates the inference architecture, but would need to be retrained on real data before production deployment."

### 3. What AWS infrastructure are you using?
**Honest Answer:**  
"We are currently not using any AWS infrastructure, nor do we have a database (SQL/NoSQL) deployed. The platform is running entirely on free-tier edge computing: the frontend is hosted on Vercel, and the FastAPI backend engine runs in-memory on Render. This guarantees instant deployment and zero infrastructure costs for this demonstration, while being completely Docker/AWS-ready."

### 4. How are SMS alerts being delivered?
**Honest Answer:**  
"No real SMS alerts are being transmitted to public carrier networks. The system dynamically generates the multi-lingual alert text (in English, Hindi, Garhwali, Kumaoni, and Nepali) and routes it internally for decision support. However, we *do* have a live, working integration with the Telegram Bot API which acts as our real-time dispatch fallback to alert response authorities during this demo."

### 5. Why use synthetic datasets for the demo instead of live weather?
**Honest Answer:**  
"We implemented a `NORMAL` mode that ingests live Open-Meteo data. However, for this demonstration, the `HEAVY_RAIN` and `EXTREME_RAIN` scenarios intentionally circuit-break the live API and inject a deterministic synthetic dataset. This ensures we can reliably demonstrate the multi-hazard cascade, the Dijkstra pathfinding over flooded roads, and shelter capacity logic without waiting for a real-life disaster to occur during the presentation."
