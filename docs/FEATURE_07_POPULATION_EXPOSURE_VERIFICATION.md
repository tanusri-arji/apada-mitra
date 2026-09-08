# APADA MITRA — FEATURE 7: REAL POPULATION & EXPOSURE DATA
**SIH Problem Statement ID:** SIH26192  
**Implementation Date:** 2026-09-05  
**Component:** Census-Provenanced Demographics & Multi-Hazard Population Exposure Engine  

---

## 1. Executive Purpose & Scope

Feature 7 replaces synthetic village population numbers with verified, authoritative **Census of India 2011 Primary Census Abstract (PCA)** and **District Census Handbook (DCHB)** demographic records for all 15 monitored Himalayan settlements across Chamoli and Rudraprayag districts.

In addition, it cleanly decouples **Population Data** from **Hazard Exposure Calculation**, computing multi-hazard inundation and slope instability footprints transparently without fabricating parcel-level GIS polygons.

---

## 2. Authoritative Data Source & Provenance

| Parameter | Authoritative Record |
| :--- | :--- |
| **Source Authority** | Office of the Registrar General & Census Commissioner, India (ORGI), Ministry of Home Affairs, Government of India |
| **Dataset Series** | Census of India 2011 — Uttarakhand, Series 06 (Village & Town Primary Census Abstract) |
| **Chamoli Handbook** | `https://censusindia.gov.in/2011census/dchb/0502_PART_B_DCHB_CHAMOLI.pdf` |
| **Rudraprayag Handbook** | `https://censusindia.gov.in/2011census/dchb/0501_PART_B_DCHB_RUDRAPRAYAG.pdf` |
| **National Portal** | `https://censusindia.gov.in/nada/index.php/catalog/284` |
| **Census Year** | 2011 (Official benchmark) |
| **Geographic Resolution** | `VILLAGE_CENSUS_PCA` for rural revenue villages; `TOWN_WARD_PCA` / `WARD_SECTOR_PCA` for monitored riverfront municipal reaches |

---

## 3. Mathematical Methodology & Exposure Modeling

### 3.1 Population Demographics vs. Hazard Exposure
Demographic records establish static baseline headcounts ($P_{\text{total}}$), residential households ($H$), and vulnerable demographic groups ($P_{\text{vuln}}$, comprising 0–6 age children and elderly cohorts).

### 3.2 Hazard-Specific Exposure Fraction
Exposure is calculated independently for each hazard modality:

#### Flash Flood Inundation Exposure ($F_{\text{flood}}$)
$$F_{\text{flood}} = \begin{cases}
\min(1.0, 0.45 + 0.35 \times \frac{R_{\text{flood}}}{100}) & \text{if CRITICAL} \\
\min(1.0, 0.25 + 0.25 \times \frac{R_{\text{flood}}}{100}) & \text{if HIGH} \\
\min(1.0, 0.10 + 0.15 \times \frac{R_{\text{flood}}}{100}) & \text{if MODERATE} \\
\min(1.0, 0.02 + 0.08 \times \frac{R_{\text{flood}}}{100}) & \text{if LOW}
\end{cases}$$

#### Landslide Slope Exposure ($F_{\text{landslide}}$)
$$F_{\text{landslide}} = \begin{cases}
\min(1.0, 0.40 + 0.30 \times \frac{R_{\text{landslide}}}{100}) & \text{if CRITICAL} \\
\min(1.0, 0.20 + 0.20 \times \frac{R_{\text{landslide}}}{100}) & \text{if HIGH} \\
\min(1.0, 0.08 + 0.12 \times \frac{R_{\text{landslide}}}{100}) & \text{if MODERATE} \\
\min(1.0, 0.01 + 0.05 \times \frac{R_{\text{landslide}}}{100}) & \text{if LOW}
\end{cases}$$

### 3.3 Multi-Hazard Spatial Union Envelope
Rather than double-counting residents exposed to both swelling torrents and unstable slopes, the engine applies the probabilistic spatial union:
$$F_{\text{combined}} = 1.0 - (1.0 - F_{\text{flood}}) \times (1.0 - F_{\text{landslide}})$$
$$P_{\text{exposed}} = \min(P_{\text{total}}, \text{round}(P_{\text{total}} \times F_{\text{combined}}))$$
$$P_{\text{vuln\_exposed}} = \min(P_{\text{vuln}}, \text{round}(P_{\text{vuln}} \times F_{\text{combined}}))$$
$$\text{Exposure Percentage} = \frac{P_{\text{exposed}}}{P_{\text{total}}} \times 100.0$$

---

## 4. Data States & Provenance Tracking

- **`REAL_STATIC`**: Official Census 2011 village PCA record matching revenue boundary directly (Confidence: 95%).
- **`ESTIMATED_FROM_REAL_SOURCE`**: Ward / sector reach estimation of municipal town PCA records (Confidence: 90%).
- **`CACHED`**: Locally synchronized verified census data.
- **`OFFLINE_DEMO`**: Fallback dataset when village record is unavailable.
- **`UNAVAILABLE`**: Census data corrupted or missing.

---

## 5. API Endpoints & Runtime Verification

### 5.1 Endpoints
- `GET /api/exposure/villages/{village_id}`: Returns multi-hazard exposure detail and census metadata for a single village.
- `GET /api/exposure/villages`: Returns exposure assessments for all 15 monitored villages.

### 5.2 Runtime Verification Results

#### `VIL-001` (Pipalkoti) — `GET /api/exposure/villages/VIL-001`
```json
{
  "village_id": "VIL-001",
  "village_name": "Pipalkoti",
  "district": "Chamoli",
  "sub_district_or_block": "Dasholi",
  "total_population": 2411,
  "households": 568,
  "vulnerable_population": 432,
  "exposed_population": 1424,
  "vulnerable_exposed": 255,
  "exposure_percentage": 59.06,
  "overall_hazard_level": "HIGH",
  "overall_hazard_score": 61.82,
  "flood_exposure": {
    "hazard_type": "FLASH_FLOOD",
    "risk_score": 57.98,
    "risk_level": "HIGH",
    "exposed_population": 952,
    "exposure_fraction": 0.395,
    "vulnerable_exposed": 171
  },
  "landslide_exposure": {
    "hazard_type": "LANDSLIDE",
    "risk_score": 61.82,
    "risk_level": "HIGH",
    "exposed_population": 780,
    "exposure_fraction": 0.3236,
    "vulnerable_exposed": 140
  },
  "infrastructure_exposed": {
    "schools": 3,
    "health_facilities": 1,
    "bridges_and_roads": 2,
    "critical_structures_count": 6
  },
  "composite_exposure_score": 64.1,
  "calculation_method": "MULTI_HAZARD_SPATIAL_INTERSECTION",
  "data_state": "REAL_STATIC",
  "confidence": 95.0,
  "source_provenance": {
    "source": "Census of India 2011: District Census Handbook Chamoli (Village Directory)",
    "source_url": "https://censusindia.gov.in/2011census/dchb/0502_PART_B_DCHB_CHAMOLI.pdf",
    "source_year": 2011,
    "geographic_level": "VILLAGE_CENSUS_PCA",
    "census_2011_code": "042235",
    "data_state": "REAL_STATIC",
    "confidence": 95.0
  }
}
```

#### `VIL-003` (Govindghat) — `GET /api/exposure/villages/VIL-003`
```json
{
  "village_id": "VIL-003",
  "village_name": "Govindghat",
  "district": "Chamoli",
  "sub_district_or_block": "Joshi Math",
  "total_population": 1237,
  "households": 274,
  "vulnerable_population": 215,
  "exposed_population": 740,
  "vulnerable_exposed": 129,
  "exposure_percentage": 59.82,
  "overall_hazard_level": "HIGH",
  "overall_hazard_score": 65.54,
  "flood_exposure": {
    "hazard_type": "FLASH_FLOOD",
    "risk_score": 59.76,
    "risk_level": "HIGH",
    "exposed_population": 494,
    "exposure_fraction": 0.3994,
    "vulnerable_exposed": 86
  },
  "landslide_exposure": {
    "hazard_type": "LANDSLIDE",
    "risk_score": 65.54,
    "risk_level": "HIGH",
    "exposed_population": 410,
    "exposure_fraction": 0.3311,
    "vulnerable_exposed": 71
  },
  "infrastructure_exposed": {
    "schools": 1,
    "health_facilities": 1,
    "bridges_and_roads": 2,
    "critical_structures_count": 4
  },
  "composite_exposure_score": 44.4,
  "calculation_method": "MULTI_HAZARD_SPATIAL_INTERSECTION",
  "data_state": "REAL_STATIC",
  "confidence": 95.0,
  "source_provenance": {
    "source": "Census of India 2011: District Census Handbook Chamoli (Village Directory)",
    "source_url": "https://censusindia.gov.in/2011census/dchb/0502_PART_B_DCHB_CHAMOLI.pdf",
    "source_year": 2011,
    "geographic_level": "VILLAGE_CENSUS_PCA",
    "census_2011_code": "042031",
    "data_state": "REAL_STATIC",
    "confidence": 95.0
  }
}
```

---

## 6. Test Suite Execution Summary

- **Feature 7 Tests (`backend/tests/test_feature_07_population_exposure.py`):** **11 passed**
  1. `test_census_source_provenance_metadata`: PASSED
  2. `test_village_001_pipalkoti_census_demographics`: PASSED
  3. `test_village_003_govindghat_census_demographics`: PASSED
  4. `test_exposure_calculation_separation_and_bounds`: PASSED
  5. `test_exposure_not_blindly_100_percent`: PASSED
  6. `test_estimated_data_state_properly_labelled`: PASSED
  7. `test_api_get_village_exposure_single`: PASSED
  8. `test_api_get_village_exposure_all`: PASSED
  9. `test_api_invalid_village_exposure_404`: PASSED
  10. `test_legacy_calculate_village_exposure_unmodified`: PASSED
  11. `test_features_1_to_6_integrity_preserved`: PASSED

---

## 7. Limitations & Boundary Conditions

1. **Temporal Horizon**: Census figures represent 2011 government census baselines; decadal population growth is not fabricated.
2. **Transient Pilgrimage Footprint**: Floating tourist and pilgrimage footfalls (e.g. Badrinath, Hemkund Sahib) fluctuate seasonally and are not conflated with permanent resident demographics.
3. **Spatial Aggregation**: Exposure models provide village-scale disaster decision support rather than cadastre-level parcel or individual building GIS polygons.
