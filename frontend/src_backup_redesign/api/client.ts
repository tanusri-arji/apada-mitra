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


