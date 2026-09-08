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
  state?: string;
  district?: string;
  latitude: number;
  longitude: number;
  population: number;
  elevation: number;
  slope?: number;
  scenario: ScenarioType;
  flash_flood_risk_score: number;
  risk_probability: number;
  confidence: number;
  risk_level: RiskLevel;
  landslide_risk_score?: number;
  landslide_risk_level?: RiskLevel | string;
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
  state?: string;
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
  state?: string;
  district?: string;
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
  garhwali: string;
  kumaoni: string;
  nepali: string;
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

export type TopLevelView =
  | 'LIVE_MONITORING'
  | 'PREDICTION'
  | 'EVACUATION_ACTION'
  | 'VALIDATION_REPLAY';

export interface StationRegionInfo {
  villageId: string;
  stationNumber: number;
  villageName: string;
  region: string;
  state: string;
  primaryLanguage: string;
  fallbackLanguage: string;
  technicalLanguage: string;
}

export interface CanonicalVillageMetadata {
  village_id: string;
  village_name: string;
  state: string;
  district: string;
  latitude: number;
  longitude: number;
  slope?: number;
}

export interface VillageLeadTimeDetail {
  village_id: string;
  village_name: string;
  calculated_at: string;
  current_risk_score: number;
  current_risk_level: string;
  hazard_escalation_estimate_minutes?: number | null;
  evacuation_time_minutes: number;
  preparation_time_minutes: number;
  total_required_time_minutes: number;
  available_lead_time_minutes?: number | null;
  safety_margin_minutes?: number | null;
  decision_status: string;
  confidence: number;
  calculation_method: string;
  data_state: string;
  assumptions: string[];
}

export interface IMDWarning {
  warning_id: string;
  source: string;
  source_url: string;
  issued_at?: string | null;
  effective_at?: string | null;
  expires_at?: string | null;
  event?: string | null;
  severity?: string | null;
  urgency?: string | null;
  certainty?: string | null;
  headline?: string | null;
  description?: string | null;
  area_description?: string | null;
  affected_districts: string[];
  affected_states: string[];
  instruction?: string | null;
  status?: string | null;
  retrieved_at: string;
  data_state: 'REAL_LIVE_OFFICIAL' | 'CACHED_OFFICIAL' | 'UNAVAILABLE' | string;
  scope: 'DISTRICT' | 'SUBDIVISION' | 'STATE' | 'UNMATCHED' | string;
}

export interface IMDStatus {
  source: string;
  source_url: string;
  data_state: 'REAL_LIVE_OFFICIAL' | 'CACHED_OFFICIAL' | 'UNAVAILABLE' | string;
  last_successful_fetch?: string | null;
  retrieved_at: string;
  warning_count: number;
  active_warning_count: number;
  coverage: string;
  error?: string | null;
}

export interface IMDVillageWarningResponse {
  village_id: string;
  village_name: string;
  district: string;
  state: string;
  data_state: 'REAL_LIVE_OFFICIAL' | 'CACHED_OFFICIAL' | 'UNAVAILABLE' | string;
  has_active_warning: boolean;
  warnings: IMDWarning[];
  evidence_context: string;
}

export interface IMDDistrictWarningResponse {
  district: string;
  data_state: string;
  has_active_warning: boolean;
  warnings: IMDWarning[];
  evidence_context: string;
}

export interface CandidateShelterEvaluation {
  shelter_id: string;
  shelter_name: string;
  latitude: number;
  longitude: number;
  elevation: number;
  is_accessible: boolean;
  rejection_reason?: string | null;
  route_distance_km?: number | null;
  travel_time_minutes?: number | null;
  route_safety_score?: number | null;
  shelter_hazard_score: number;
  shelter_hazard_level: string;
  suitability_score?: number | null;
  total_capacity?: number | null;
  available_capacity?: number | null;
  capacity_status: string;
  data_state: string;
  source: string;
}

export interface VillageShelterRecommendation {
  village_id: string;
  village_name: string;
  status: string;
  selected_shelter_id?: string | null;
  selected_shelter_name?: string | null;
  suitability_score?: number | null;
  route_distance_km?: number | null;
  travel_time_minutes?: number | null;
  route_safety_score?: number | null;
  shelter_hazard_score?: number | null;
  shelter_hazard_level?: string | null;
  capacity?: number | null;
  available_capacity?: number | null;
  capacity_status?: string | null;
  road_status?: string | null;
  blocked_segments: string[];
  degraded_segments: string[];
  data_state: string;
  source: string;
  source_url: string;
  calculation_method: string;
  suitability_weights: Record<string, number>;
  alternatives: CandidateShelterEvaluation[];
  coverage_status: string;
  nearest_verified_shelter_distance?: number | null;
  nearest_candidate_distance?: number | null;
  number_of_candidates: number;
  number_of_verified_shelters: number;
  number_of_route_accessible_shelters: number;
  rejected_candidates: CandidateShelterEvaluation[];
  all_candidates_evaluated: CandidateShelterEvaluation[];
  selection_reason: string;
}

export interface ShelterCoverageItem {
  village_id: string;
  village_name: string;
  district: string;
  state: string;
  nearest_verified_shelter_distance?: number | null;
  nearest_candidate_distance?: number | null;
  number_of_candidates: number;
  number_of_verified_shelters: number;
  number_of_route_accessible_shelters: number;
  recommended_shelter_id?: string | null;
  recommended_shelter_name?: string | null;
  coverage_status: string;
}

export interface ShelterCoverageSummaryResponse {
  total_monitored_villages: number;
  total_shelter_candidates: number;
  villages_with_good_coverage: number;
  villages_with_limited_coverage: number;
  villages_with_no_safe_shelter: number;
  coverage_details: ShelterCoverageItem[];
}

export interface HydrographPoint {
  lead_hour: number;
  forecast_timestamp: string;
  stage_m: number;
  discharge_cumec: number;
  warning_level_m: number;
  danger_level_m: number;
  status: 'NORMAL' | 'ALERT' | 'WARNING' | 'DANGER';
}

export interface HydrographPredictionResponse {
  village_id: string;
  village_name: string;
  river_name: string;
  monitoring_station_id: string;
  monitoring_station_name: string;
  current_rainfall_mm_h: number;
  current_soil_moisture_pct: number;
  initial_stage_m: number;
  peak_stage_m: number;
  peak_lead_hour: number;
  peak_timestamp: string;
  warning_exceeded: boolean;
  danger_exceeded: boolean;
  confidence_score: number;
  model_architecture: string;
  training_provenance: string;
  validation_metrics: {
    nash_sutcliffe_efficiency: number;
    coefficient_of_determination_r2: number;
    root_mean_squared_error_m: number;
    peak_crest_timing_error_hours: number;
  };
  series: HydrographPoint[];
}

export interface WhatIfHydrographRequest {
  village_id?: string;
  rainfall_intensity_mm_h: number;
  soil_saturation_pct: number;
  upstream_stage_offset_m?: number;
}

export interface ModelBenchmarkInfoResponse {
  model_name: string;
  framework: string;
  architecture: string;
  loss_function: string;
  training_epochs: number;
  dataset_records_count: number;
  catchments_covered: string[];
  features_used: string[];
  benchmarks: Record<string, number>;
  compliance_standards: string[];
}



