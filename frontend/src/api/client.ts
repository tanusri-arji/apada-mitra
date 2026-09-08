import {
  ScenarioType,
  ScenarioStateResponse,
  ReadinessResponse,
  VillageRiskDetail,
  RiskOverviewResponse,
  ImpactSummary,
  VillageBase,
  LandslideRiskDetail,
  EvacuationPriority,
  RoadSegment,
  Shelter,
  EvacuationRouteResult,
  ShelterRecommendationResult,
  WhatIfSimulationInput,
  WhatIfSimulationResponse,
  VillageLeadTimeDetail,
  IMDStatus,
  IMDWarning,
  IMDVillageWarningResponse,
  IMDDistrictWarningResponse,
  CandidateShelterEvaluation,
  VillageShelterRecommendation,
  ShelterCoverageSummaryResponse,
  HydrographPredictionResponse,
  WhatIfHydrographRequest,
  ModelBenchmarkInfoResponse,
} from '../types';

const API_BASE = '/api';

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error('Backend server unavailable');
  return res.json();
}

export async function fetchReadiness(): Promise<ReadinessResponse> {
  const res = await fetch(`${API_BASE}/readiness`);
  if (!res.ok) throw new Error('Backend readiness check failed');
  return res.json();
}

export async function fetchScenarioState(): Promise<ScenarioStateResponse> {
  const res = await fetch(`${API_BASE}/scenario`);
  if (!res.ok) throw new Error('Failed to fetch scenario state');
  return res.json();
}

export async function updateScenario(scenario: ScenarioType): Promise<ScenarioStateResponse> {
  const res = await fetch(`${API_BASE}/scenario`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ scenario }),
  });
  if (!res.ok) throw new Error('Failed to update scenario');
  return res.json();
}

export async function fetchVillagesList(): Promise<VillageBase[]> {
  const res = await fetch(`${API_BASE}/villages`);
  if (!res.ok) throw new Error('Failed to fetch villages');
  return res.json();
}

export async function fetchVillageDetail(id: string): Promise<VillageRiskDetail> {
  const res = await fetch(`${API_BASE}/villages/${id}`);
  if (!res.ok) throw new Error(`Failed to fetch detail for village ${id}`);
  return res.json();
}

export async function fetchRiskOverview(): Promise<RiskOverviewResponse> {
  const res = await fetch(`${API_BASE}/risk`);
  if (!res.ok) throw new Error('Failed to fetch risk overview');
  return res.json();
}

export async function fetchImpactSummary(): Promise<ImpactSummary> {
  const res = await fetch(`${API_BASE}/impact`);
  if (!res.ok) throw new Error('Failed to fetch impact summary');
  return res.json();
}

export async function fetchLandslideOverview(): Promise<LandslideRiskDetail[]> {
  const res = await fetch(`${API_BASE}/landslide`);
  if (!res.ok) throw new Error('Failed to fetch landslide risk overview');
  return res.json();
}

export async function fetchEvacuationPriorities(): Promise<EvacuationPriority[]> {
  const res = await fetch(`${API_BASE}/evacuation/priorities`);
  if (!res.ok) throw new Error('Failed to fetch evacuation priorities');
  return res.json();
}

export async function fetchRoadNetwork(): Promise<RoadSegment[]> {
  const res = await fetch(`${API_BASE}/roads`);
  if (!res.ok) throw new Error('Failed to fetch mountain road network');
  return res.json();
}

export async function computeEvacuationRoute(
  origin_village_id: string,
  destination_shelter_id: string
): Promise<EvacuationRouteResult> {
  const res = await fetch(`${API_BASE}/evacuation/route`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ origin_village_id, destination_shelter_id }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to compute evacuation route');
  }
  return res.json();
}

export async function fetchShelters(): Promise<Shelter[]> {
  const res = await fetch(`${API_BASE}/shelters`);
  if (!res.ok) throw new Error('Failed to fetch shelters list');
  return res.json();
}

export async function fetchShelterRecommendation(
  village_id: string
): Promise<ShelterRecommendationResult> {
  const res = await fetch(`${API_BASE}/evacuation/shelter-recommendation/${village_id}`);
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to fetch shelter recommendation');
  }
  return res.json();
}

export async function fetchSafestShelterRecommendation(
  village_id: string
): Promise<VillageShelterRecommendation> {
  const res = await fetch(`${API_BASE}/evacuation/shelter/${village_id}`);
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to fetch safest shelter recommendation');
  }
  return res.json();
}

export async function fetchVillageShelterCandidates(
  village_id: string
): Promise<CandidateShelterEvaluation[]> {
  const res = await fetch(`${API_BASE}/shelters/villages/${village_id}`);
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to fetch shelter candidates');
  }
  return res.json();
}

export async function fetchShelterAlternatives(
  village_id: string
): Promise<CandidateShelterEvaluation[]> {
  const res = await fetch(`${API_BASE}/evacuation/shelter/${village_id}/alternatives`);
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to fetch shelter alternatives');
  }
  return res.json();
}

export async function fetchShelterCoverage(): Promise<ShelterCoverageSummaryResponse> {
  const res = await fetch(`${API_BASE}/shelters/coverage`);
  if (!res.ok) throw new Error('Failed to fetch shelter coverage summary');
  return res.json();
}

export async function fetchVillageCandidateShelters(
  village_id: string
): Promise<CandidateShelterEvaluation[]> {
  const res = await fetch(`${API_BASE}/shelters/villages/${village_id}/candidates`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to fetch candidate shelters for village ${village_id}`);
  }
  return res.json();
}


export async function runWhatIfSimulation(
  inputData: WhatIfSimulationInput
): Promise<WhatIfSimulationResponse> {
  const res = await fetch(`${API_BASE}/simulation/what-if`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(inputData),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'What-If simulation request failed');
  }
  return res.json();
}

export async function fetchVillageHistoricalLandslideSummary(village_id: string): Promise<any> {
  const res = await fetch(`${API_BASE}/landslides/historical/${village_id}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to fetch historical landslide summary for village ${village_id}`);
  }
  return res.json();
}

export async function fetchVillageLeadTime(
  village_id: string
): Promise<VillageLeadTimeDetail> {
  const res = await fetch(`${API_BASE}/lead-time/villages/${village_id}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to fetch lead time for village ${village_id}`);
  }
  return res.json();
}

export async function fetchIMDStatus(): Promise<IMDStatus> {
  const res = await fetch(`${API_BASE}/imd/status`);
  if (!res.ok) throw new Error('Failed to fetch IMD CAP status');
  return res.json();
}

export async function fetchIMDWarnings(): Promise<IMDWarning[]> {
  const res = await fetch(`${API_BASE}/imd/warnings`);
  if (!res.ok) throw new Error('Failed to fetch IMD CAP warnings');
  return res.json();
}

export async function fetchIMDWarningsForVillage(villageId: string): Promise<IMDVillageWarningResponse> {
  const res = await fetch(`${API_BASE}/imd/villages/${villageId}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to fetch IMD warnings for village ${villageId}`);
  }
  return res.json();
}

export async function fetchIMDWarningsForDistrict(districtName: string): Promise<IMDDistrictWarningResponse> {
  const res = await fetch(`${API_BASE}/imd/districts/${encodeURIComponent(districtName)}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to fetch IMD warnings for district ${districtName}`);
  }
  return res.json();
}

export async function fetchVillageHydrograph(
  villageId: string,
  scenario: ScenarioType = 'HEAVY_RAIN'
): Promise<HydrographPredictionResponse> {
  const res = await fetch(`${API_BASE}/ml/hydrograph/${villageId}?scenario=${scenario}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to fetch hydrograph for village ${villageId}`);
  }
  return res.json();
}

export async function simulateCustomHydrograph(
  payload: WhatIfHydrographRequest
): Promise<HydrographPredictionResponse> {
  const res = await fetch(`${API_BASE}/ml/predict-hydrograph`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to simulate custom hydrograph');
  }
  return res.json();
}

export async function fetchModelBenchmarkInfo(): Promise<ModelBenchmarkInfoResponse> {
  const res = await fetch(`${API_BASE}/ml/model-info`);
  if (!res.ok) throw new Error('Failed to fetch ML model benchmark info');
  return res.json();
}




