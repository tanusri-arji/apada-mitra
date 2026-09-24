r"""
APADA MITRA — Demo IoT Seed Generator (Feature 3 enabler).

Standalone helper that injects realistic, *fresh* IoT sensor readings into the
running APADA MITRA backend so the IoT data-priority path is visible during a
demo / evaluation without any physical sensors deployed.

It POSTs to  POST /api/iot/sensors/ingest  for a handful of villages. Once
ingested, the data pipeline automatically prioritises these LIVE_IOT_SENSOR
readings over Open-Meteo for the freshness window (LIVE <= 10 min), so a
GET /api/villages/{id} response will then report rainfall_source ==
"LIVE_IOT_SENSOR" for the seeded villages.

This script is ADDITIVE ONLY: it does not modify any project engine, route, or
test. It simply talks to the existing (auth-gated) ingestion endpoint.

Usage:
    venv\Scripts\python.exe backend/scripts/iot_seed_generator.py             # one burst
    venv\Scripts\python.exe backend/scripts/iot_seed_generator.py --interval 180
    python backend/scripts/iot_seed_generator.py --base-url http://127.0.0.1:8000

Configuration via env:
    BASE_URL / --base-url        Target base URL (default http://127.0.0.1:8000)
    IOT_INGEST_API_KEY           If set to a real (non-placeholder) value, requests are
                                 sent with `Authorization: Bearer <key>` (matches the
                                 backend auth gate). If absent/placeholder, demo mode
                                 (open ingestion) is used.
"""
import argparse
import json
import time
import os
import urllib.request
import urllib.error
from datetime import datetime, timezone

DEFAULT_BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")
INGEST_PATH = "/api/iot/sensors/ingest"
_PLACEHOLDER = "<INSERT_YOUR_IOT_API_KEY>"

# Synthetic-but-realistic demo sensors across the 3 disjoint regions.
# Values are plausible for the Himalayan hill-stream environment.
SEED_SENSORS = [
    {"sensor_id": "IOT-VIL001-RAIN", "sensor_type": "rainfall",
     "village_id": "VIL-001", "value": 3.2, "unit": "mm/h"},
    {"sensor_id": "IOT-VIL003-RAIN", "sensor_type": "rainfall",
     "village_id": "VIL-003", "value": 9.6, "unit": "mm/h"},
    {"sensor_id": "IOT-VIL003-SOIL", "sensor_type": "soil_moisture",
     "village_id": "VIL-003", "value": 0.48, "unit": "m3/m3"},
    {"sensor_id": "IOT-VIL003-WATR", "sensor_type": "water_level",
     "village_id": "VIL-003", "value": 2.15, "unit": "m"},
    {"sensor_id": "IOT-VIL011-RAIN", "sensor_type": "rainfall",
     "village_id": "VIL-011", "value": 14.4, "unit": "mm/h"},
    {"sensor_id": "IOT-VIL013-SOIL", "sensor_type": "soil_moisture",
     "village_id": "VIL-013", "value": 0.61, "unit": "m3/m3"},
]


def _bearer_headers():
    key = os.getenv("IOT_INGEST_API_KEY", _PLACEHOLDER)
    headers = {"Content-Type": "application/json"}
    if key and key != _PLACEHOLDER:
        headers["Authorization"] = f"Bearer {key}"
    return headers


def ingest_once(base_url):
    url = base_url + INGEST_PATH
    headers = _bearer_headers()
    now_iso = datetime.now(timezone.utc).isoformat()
    results = []
    for s in SEED_SENSORS:
        payload = {**s, "timestamp": now_iso}
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                results.append({
                    "sensor_id": body.get("sensor_id"),
                    "status": body.get("status"),
                    "value": body.get("value"),
                    "source": body.get("source"),
                })
        except urllib.error.HTTPError as e:
            results.append({"sensor_id": s["sensor_id"], "error": f"HTTP {e.code}",
                            "detail": json.loads(e.read().decode('utf-8')).get('detail', str(e))})
        except Exception as e:  # network / timeout
            results.append({"sensor_id": s["sensor_id"], "error": str(e)})
    return results


def main():
    ap = argparse.ArgumentParser(description="Seed APADA MITRA demo IoT sensors.")
    ap.add_argument("--base-url", default=DEFAULT_BASE_URL, help=f"Backend base URL (default: {DEFAULT_BASE_URL})")
    ap.add_argument("--interval", type=float, default=0.0,
                    help="If >0, re-ingest every N seconds (keeps sensors LIVE). Default: one burst.")
    args = ap.parse_args()

    print(f"[{datetime.now(timezone.utc).isoformat()}] Seeding IoT sensors -> {args.base_url}")
    while True:
        res = ingest_once(args.base_url)
        ok = sum(1 for r in res if "error" not in r)
        errs = sum(1 for r in res if "error" in r)
        print(f"[{datetime.now(timezone.utc).isoformat()}] ingested: {ok} OK / {errs} ERR")
        for r in res:
            print("  ", r)
        if not args.interval or args.interval <= 0:
            break
        print(f"    ...sleeping {args.interval}s")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
