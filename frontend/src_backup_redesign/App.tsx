import React, { useEffect, useState, useCallback } from 'react';
import { Header } from './components/Header';
import { MetricsBar } from './components/MetricsBar';
import { Sidebar } from './components/Sidebar';
import { MapView } from './components/MapView';
import { VillageDetailPanel } from './components/VillageDetailPanel';
import { WhatIfSimulator } from './components/WhatIfSimulator';
import { ScenarioControl } from './components/ScenarioControl';
import {
  fetchScenarioState,
  fetchReadiness,
  fetchRiskOverview,
  updateScenario,
  fetchVillageDetail,
  fetchLandslideOverview,
  fetchEvacuationPriorities,
  fetchRoadNetwork,
  fetchShelters,
  fetchShelterRecommendation,
} from './api/client';
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
} from './types';
import { AlertCircle, RefreshCw } from 'lucide-react';

export const App: React.FC = () => {
  const [scenarioState, setScenarioState] = useState<ScenarioStateResponse | null>(null);
  const [readinessState, setReadinessState] = useState<ReadinessResponse | null>(null);
  const [riskOverview, setRiskOverview] = useState<RiskOverviewResponse | null>(null);
  const [landslides, setLandslides] = useState<LandslideRiskDetail[]>([]);
  const [priorities, setPriorities] = useState<EvacuationPriority[]>([]);
  const [roads, setRoads] = useState<RoadSegment[]>([]);
  const [shelters, setShelters] = useState<Shelter[]>([]);
  const [shelterRec, setShelterRec] = useState<ShelterRecommendationResult | null>(null);

  const [activeTab, setActiveTab] = useState<'COMMAND_CENTER' | 'WHAT_IF'>('COMMAND_CENTER');
  const [activeSimulation, setActiveSimulation] = useState<WhatIfSimulationResponse | null>(null);

  const [selectedVillageId, setSelectedVillageId] = useState<string | null>('VIL-001');
  const [selectedVillageDetail, setSelectedVillageDetail] = useState<VillageRiskDetail | null>(null);
  const [isScenarioModalOpen, setIsScenarioModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [routeLoading, setRouteLoading] = useState(false);
  const [scenarioUpdating, setScenarioUpdating] = useState(false);
  const [backendError, setBackendError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setBackendError(null);
      const [sc, read, risk, ls, prio, rd, sh] = await Promise.all([
        fetchScenarioState(),
        fetchReadiness().catch(() => null),
        fetchRiskOverview(),
        fetchLandslideOverview(),
        fetchEvacuationPriorities(),
        fetchRoadNetwork(),
        fetchShelters(),
      ]);
      setScenarioState(sc);
      setReadinessState(read);
      setRiskOverview(risk);
      setLandslides(ls);
      setPriorities(prio);
      setRoads(rd);
      setShelters(sh);
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
  }, [loadData]);

  // Reset shelter recommendation when village changes
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
      setSelectedVillageId(null);
      setShelterRec(null);
      setActiveSimulation(null);
      setActiveTab('COMMAND_CENTER');
      await updateScenario('HEAVY_RAIN');
      await loadData();
    } catch (err) {
      console.error('Reset error:', err);
    }
  };

  // Determine active view models (using activeSimulation overlays if present)
  const currentVillages = activeSimulation?.simulated_villages_flood || riskOverview?.villages_risk || [];
  const currentLandslides = activeSimulation?.simulated_landslide_overview || landslides;
  const currentPriorities = activeSimulation?.simulated_evacuation_priorities || priorities;
  const currentRoads = activeSimulation?.simulated_roads || roads;
  const currentShelters = activeSimulation?.simulated_shelters || shelters;
  const activeRoute = activeSimulation?.simulated_route || shelterRec?.route || null;

  const selectedLandslide = currentLandslides.find((l) => l.village_id === selectedVillageId) || null;
  const selectedPriority = currentPriorities.find((p) => p.village_id === selectedVillageId) || null;

  return (
    <div className="flex flex-col h-screen w-screen bg-command-bg text-command-text overflow-hidden font-sans">
      {/* Header */}
      <Header
        scenarioState={scenarioState}
        readinessState={readinessState}
        onScenarioChangeClick={() => setIsScenarioModalOpen(true)}
        onDemoReset={handleDemoReset}
        backendError={backendError}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        isSimulationActive={!!activeSimulation}
      />

      {/* Metrics Summary Bar */}
      <MetricsBar
        impact={riskOverview?.impact_summary || null}
        loading={loading}
      />

      {/* Main Command Center Layout */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Backend Error Banner */}
        {backendError && (
          <div className="absolute top-4 left-1/2 -translate-x-1/2 z-50 bg-red-950/90 border border-red-600/80 text-red-200 px-6 py-3 rounded-lg shadow-2xl backdrop-blur-md flex items-center gap-3 font-mono text-xs max-w-xl">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
            <div className="flex-1">{backendError}</div>
            <button
              onClick={loadData}
              className="bg-red-600 text-white font-bold px-3 py-1 rounded hover:bg-red-500 transition flex items-center gap-1"
            >
              <RefreshCw className="w-3.5 h-3.5" /> Retry
            </button>
          </div>
        )}

        {/* Left Navigation Sidebar */}
        <Sidebar
          villages={currentVillages}
          evacuationPriorities={currentPriorities}
          selectedVillageId={selectedVillageId}
          onSelectVillage={setSelectedVillageId}
          loading={loading}
        />

        {/* Center Interactive Disaster Map */}
        <main className="flex-1 relative h-full">
          <MapView
            villages={currentVillages}
            roads={currentRoads}
            shelters={currentShelters}
            activeRoute={activeRoute}
            selectedVillageId={selectedVillageId}
            onSelectVillage={setSelectedVillageId}
            isSimulationActive={!!activeSimulation}
          />
        </main>

        {/* Right Panel: View Dependent */}
        {activeTab === 'WHAT_IF' ? (
          <WhatIfSimulator
            onSimulationUpdate={setActiveSimulation}
            activeSimulation={activeSimulation}
          />
        ) : (
          <VillageDetailPanel
            village={selectedVillageDetail}
            landslideDetail={selectedLandslide}
            priorityDetail={selectedPriority}
            shelterRecommendation={activeSimulation?.simulated_shelter_recommendation || shelterRec}
            onCalculateRoute={handleCalculateRoute}
            routeLoading={routeLoading}
            onClose={() => setSelectedVillageId(null)}
          />
        )}
      </div>

      {/* Hydro-Meteorological Scenario Selector Modal */}
      <ScenarioControl
        isOpen={isScenarioModalOpen}
        onClose={() => setIsScenarioModalOpen(false)}
        currentScenario={scenarioState?.scenario || 'HEAVY_RAIN'}
        onSelectScenario={handleSelectScenario}
        loading={scenarioUpdating}
      />
    </div>
  );
};
