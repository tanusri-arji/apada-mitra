import { useState, useEffect, useCallback } from 'react';
import {
  fetchScenarioState,
  fetchReadiness,
  fetchVillagesList,
  fetchRiskOverview,
  updateScenario,
  fetchVillageDetail,
  fetchLandslideOverview,
  fetchEvacuationPriorities,
  fetchRoadNetwork,
  fetchShelters,
  fetchShelterRecommendation,
} from '../services/api';
import {
  ScenarioStateResponse,
  ReadinessResponse,
  RiskOverviewResponse,
  VillageRiskDetail,
  LandslideRiskDetail,
  EvacuationPriority,
  RoadSegment,
  Shelter,
  ShelterRecommendationResult,
  WhatIfSimulationResponse,
  ScenarioType,
  TopLevelView,
} from '../types';

export function useDisasterData() {
  const [scenarioState, setScenarioState] = useState<ScenarioStateResponse | null>(null);
  const [readinessState, setReadinessState] = useState<ReadinessResponse | null>(null);
  const [riskOverview, setRiskOverview] = useState<RiskOverviewResponse | null>(null);
  const [landslides, setLandslides] = useState<LandslideRiskDetail[]>([]);
  const [priorities, setPriorities] = useState<EvacuationPriority[]>([]);
  const [roads, setRoads] = useState<RoadSegment[]>([]);
  const [shelters, setShelters] = useState<Shelter[]>([]);
  const [shelterRec, setShelterRec] = useState<ShelterRecommendationResult | null>(null);

  const [activeTab, setActiveTab] = useState<TopLevelView>('LIVE_MONITORING');
  const [activeSimulation, setActiveSimulation] = useState<WhatIfSimulationResponse | null>(null);

  const [selectedVillageId, setSelectedVillageId] = useState<string | null>('VIL-001');
  const [selectedVillageDetail, setSelectedVillageDetail] = useState<VillageRiskDetail | null>(null);
  const [isScenarioModalOpen, setIsScenarioModalOpen] = useState(false);
  const [isSmsModalOpen, setIsSmsModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [routeLoading, setRouteLoading] = useState(false);
  const [scenarioUpdating, setScenarioUpdating] = useState(false);
  const [backendError, setBackendError] = useState<string | null>(null);

  const [baseVillages, setBaseVillages] = useState<VillageRiskDetail[]>([]);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setBackendError(null);

      // 1. Immediate fast fetch of station list, roads, shelters, and scenario
      fetchVillagesList()
        .then((vList) => {
          if (vList && vList.length > 0) {
            setBaseVillages(
              vList.map((v: any) => ({
                village_id: v.village_id || v.id,
                village_name: v.village_name || v.name,
                latitude: v.latitude,
                longitude: v.longitude,
                population: v.population,
                elevation: v.elevation,
                scenario: 'HEAVY_RAIN',
                flash_flood_risk_score: 35,
                risk_probability: 0.35,
                confidence: 90,
                risk_level: 'MODERATE',
                decision_status: 'MONITOR',
                exposure: {
                  population_exposed: Math.round(v.population * 0.3),
                  exposure_score: 30,
                  infrastructure: { schools: 1, health_facilities: 1, bridges_and_roads: 1, critical_structures_count: 3 },
                },
                factors: [],
                missing_features: [],
                last_updated: new Date().toISOString(),
              }))
            );
          }
        })
        .catch(() => {});

      fetchRoadNetwork().then((rd) => rd && setRoads(rd)).catch(() => {});
      fetchShelters().then((sh) => sh && setShelters(sh)).catch(() => {});
      fetchScenarioState().then((sc) => sc && setScenarioState(sc)).catch(() => {});
      fetchReadiness().then((read) => read && setReadinessState(read)).catch(() => {});

      // 2. Full analytical risk and evacuation priorities load
      const [risk, ls, prio] = await Promise.all([
        fetchRiskOverview().catch(() => null),
        fetchLandslideOverview().catch(() => []),
        fetchEvacuationPriorities().catch(() => []),
      ]);

      if (risk) setRiskOverview(risk);
      if (ls) setLandslides(ls);
      if (prio) setPriorities(prio);
    } catch (err: any) {
      console.error('API Error:', err);
      setBackendError(
        'Backend server disconnected or unreachable. Ensure FastAPI server is running on http://localhost:8000.'
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const intervalId = setInterval(() => {
      loadData();
    }, 60000);

    return () => clearInterval(intervalId);
  }, [loadData]);

   // Sync selected village details
  useEffect(() => {
    setShelterRec(null);
    if (!selectedVillageId) {
      setSelectedVillageDetail(null);
      return;
    }

    const currentVillages = activeSimulation?.simulated_villages_flood || riskOverview?.villages_risk || [];
    const foundInOverview = currentVillages.find((v) => v.village_id === selectedVillageId);

    if (foundInOverview) {
      setSelectedVillageDetail(foundInOverview);
    } else {
      fetchVillageDetail(selectedVillageId)
        .then(setSelectedVillageDetail)
        .catch(console.error);
    }
  }, [selectedVillageId, riskOverview, activeSimulation]);

  const handleCalculateRoute = async () => {
    if (!selectedVillageId) return;
    try {
      setRouteLoading(true);
      const rec = await fetchShelterRecommendation(selectedVillageId);
      setShelterRec(rec);
    } catch (err: any) {
      console.error('Route calculation error:', err);
      alert(err.message || 'Failed to compute evacuation route');
    } finally {
      setRouteLoading(false);
    }
  };

  const handleSelectScenario = async (newScenario: ScenarioType) => {
    try {
      setScenarioUpdating(true);
      setActiveSimulation(null);
      await updateScenario(newScenario);
      await loadData();
      // Auto-close the modal now that the scenario has been applied and data refreshed
      setIsScenarioModalOpen(false);
      if (selectedVillageId) {
        fetchShelterRecommendation(selectedVillageId)
          .then(setShelterRec)
          .catch(() => setShelterRec(null));
      }
    } catch (err: any) {
      console.error('Failed to change scenario:', err);
      setBackendError('Failed to change scenario. Please check backend connection.');
    } finally {
      setScenarioUpdating(false);
    }
  };

  const handleDemoReset = async () => {
    try {
      setSelectedVillageId('VIL-001');
      setShelterRec(null);
      setActiveSimulation(null);
      setActiveTab('LIVE_MONITORING');
      await updateScenario('NORMAL');
      await loadData();
    } catch (err) {
      console.error('Reset error:', err);
    }
  };

  // Determine active view models
  const currentVillages = activeSimulation?.simulated_villages_flood || riskOverview?.villages_risk || baseVillages;
  const currentLandslides = activeSimulation?.simulated_landslide_overview || landslides;
  const currentPriorities = activeSimulation?.simulated_evacuation_priorities || priorities;
  const currentRoads = activeSimulation?.simulated_roads || roads;
  const currentShelters = activeSimulation?.simulated_shelters || shelters;
  const selectedLandslide = currentLandslides.find((l) => l.village_id === selectedVillageId) || null;

  return {
    scenarioState,
    readinessState,
    riskOverview,
    landslides: currentLandslides,
    priorities: currentPriorities,
    roads: currentRoads,
    shelters: currentShelters,
    shelterRec: activeSimulation?.simulated_shelter_recommendation || shelterRec,
    activeTab,
    setActiveTab,
    activeSimulation,
    setActiveSimulation,
    selectedVillageId,
    setSelectedVillageId,
    selectedVillageDetail,
    selectedLandslide,
    isScenarioModalOpen,
    setIsScenarioModalOpen,
    isSmsModalOpen,
    setIsSmsModalOpen,
    loading,
    routeLoading,
    scenarioUpdating,
    backendError,
    loadData,
    handleCalculateRoute,
    handleSelectScenario,
    handleDemoReset,
    currentVillages,
  };
}
