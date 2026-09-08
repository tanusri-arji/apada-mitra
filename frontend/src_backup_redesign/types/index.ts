export type ScenarioType = 'NORMAL' | 'HEAVY_RAIN' | 'EXTREME_RAIN';

export type RiskLevel = 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';

export type DecisionStatus = 'MONITOR' | 'PREPARE' | 'EVACUATION_READINESS';

export type DataQualityStatus = 'OK' | 'DEGRADED' | 'MISSING';

export interface InfrastructureExposure {
  schools: number;
  health_facilities: number;
  bridges_and_roads: number;
  critical_structures_count: number;
}

export interface VillageBase {
  id: string;
  name: string;
  district: string;
  block: string;
  latitude: number;
  longitude: number;
  population: number;
  elevation: number;
  slope: number;
  flow_accumulation: number;
  drainage_proximity_m: number;
  road_accessibility_score: number;
  infrastructure: InfrastructureExposure;
}

export interface FactorContribution {
  feature_key: string;
  feature_label: string;
  raw_value: number;
  unit: string;
  normalized_value: number;
  weight: number;
  contribution_points: number;
  contribution_percent: number;
}

export interface ExposureMetrics {
  population_exposed: number;
  exposure_score: number;
  infrastructure: InfrastructureExposure;
}

export interface VillageRiskDetail {
  village_id: string;
  village_name: string;
  latitude: number;
  longitude: number;
  population: number;
  elevation: number;
  scenario: ScenarioType;
  flash_flood_risk_score: number;
  risk_probability: number;
  confidence: number;
  risk_level: RiskLevel;
  decision_status: DecisionStatus;
  exposure: ExposureMetrics;
  factors: FactorContribution[];
  missing_features: string[];
  last_updated: string;
}

export interface ImpactSummary {
  scenario: ScenarioType;
  total_villages: number;
  critical_villages_count: number;
  high_villages_count: number;
  moderate_villages_count: number;
  low_villages_count: number;
  total_population_exposed: number;
  average_risk_score: number;
  average_confidence: number;
  data_quality_summary: string;
  last_updated: string;
}

export interface RiskOverviewResponse {
  scenario: ScenarioType;
  impact_summary: ImpactSummary;
  villages_risk: VillageRiskDetail[];
}

export interface ScenarioStateResponse {
  scenario: ScenarioType;
  description: string;
  data_quality_status: DataQualityStatus;
  active_villages_count: number;
  last_updated: string;
}

export interface ReadinessResponse {
  status: string;
  ready: boolean;
  checks: Record<string, boolean>;
  data_mode: string;
  version: string;
}

export interface LandslideRiskDetail {
  village_id: string;
  village_name: string;
  landslide_risk_score: number;
  risk_level: RiskLevel;
  confidence: number;
  contributing_factors: FactorContribution[];
}

export interface EvacuationPriority {
  village_id: string;
  village_name: string;
  evacuation_priority_score: number;
  priority_level: RiskLevel;
  rank: number;
  flash_flood_risk_score: number;
  landslide_risk_score: number;
  population_exposed: number;
  critical_infrastructure_count: number;
  flood_contribution_pts: number;
  landslide_contribution_pts: number;
  population_contribution_pts: number;
  infrastructure_contribution_pts: number;
  factor_breakdown_summary: string;
  primary_urgency_reason: string;
}

export type RoadStatus = 'OPEN' | 'DEGRADED' | 'BLOCKED';

export interface RoadSegment {
  id: string;
  name: string;
  source_id: string;
  target_id: string;
  distance_km: number;
  flood_exposure: number;
  landslide_exposure: number;
  status: RoadStatus;
  coordinates: number[][];
}

export interface Shelter {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  total_capacity: number;
  current_occupancy: number;
  available_capacity: number;
  elevation: number;
  accessibility_score: number;
  hazard_exposure_score: number;
}

export interface EvacuationRouteResult {
  origin_village_id: string;
  origin_village_name: string;
  destination_shelter_id: string;
  destination_shelter_name: string;
  path_village_and_shelter_ids: string[];
  road_segment_ids: string[];
  total_distance_km: number;
  estimated_travel_time_mins: number;
  route_safety_score: number;
  path_coordinates: number[][];
  hazards_encountered: string[];
  rejected_dangerous_alternatives: string[];
}

export interface ShelterRecommendationResult {
  village_id: string;
  village_name: string;
  recommended_shelter: Shelter;
  route: EvacuationRouteResult;
  recommendation_reason: string;
}

export interface WhatIfSimulationInput {
  current_rainfall_mm_hr: number;
  forecast_rainfall_24h_mm: number;
  soil_saturation_pct: number;
  river_level_m: number;
  selected_village_id?: string;
}

export interface ComparisonMetric {
  name: string;
  current_val: number;
  simulated_val: number;
  delta: number;
  unit: string;
  direction: 'INCREASE' | 'DECREASE' | 'NEUTRAL';
}

export interface SimulationComparisonSummary {
  avg_flood_risk: ComparisonMetric;
  avg_landslide_risk: ComparisonMetric;
  critical_villages_count: ComparisonMetric;
  total_population_exposed: ComparisonMetric;
  blocked_roads_count: ComparisonMetric;
  shelter_shortfall_count: ComparisonMetric;
}

export interface MultilingualAlert {
  english: string;
  hindi: string;
  telugu: string;
}

export interface EmergencyOperatorAlert {
  village_id: string;
  village_name: string;
  risk_level: RiskLevel;
  risk_score: number;
  primary_drivers: string[];
  recommended_action: string;
  shelter_name: string;
  safe_route_summary: string;
  roads_to_avoid: string[];
  translations: MultilingualAlert;
}

export interface WhatIfSimulationResponse {
  input: WhatIfSimulationInput;
  preset_used?: string;
  comparison_summary: SimulationComparisonSummary;
  simulated_villages_flood: VillageRiskDetail[];
  simulated_landslide_overview: LandslideRiskDetail[];
  simulated_evacuation_priorities: EvacuationPriority[];
  simulated_roads: RoadSegment[];
  simulated_shelters: Shelter[];
  simulated_route?: EvacuationRouteResult | null;
  simulated_shelter_recommendation?: ShelterRecommendationResult | null;
  shelter_shortfall_count: number;
  shelter_shortfall_warning?: string | null;
  operator_alert?: EmergencyOperatorAlert | null;
}


