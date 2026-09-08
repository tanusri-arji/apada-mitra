import React from 'react';
import { useDisasterData } from '../hooks/useDisasterData';
import { Header } from '../components/Header';
import { Sidebar } from '../components/Sidebar';
import { OperationalLayout } from '../layouts/OperationalLayout';
import { AppRouter } from './AppRouter';
import { ScenarioControl } from '../components/ScenarioControl';
import { EmergencySmsModal } from '../components/EmergencySmsModal';
import { AlertCircle, RefreshCw } from 'lucide-react';

export const AppShell: React.FC = () => {
  const {
    scenarioState,
    readinessState,
    riskOverview,
    priorities,
    roads,
    shelters,
    shelterRec,
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
  } = useDisasterData();

  return (
    <OperationalLayout
      sidebar={
        <Sidebar
          activeTab={activeTab}
          onTabChange={setActiveTab}
          villages={currentVillages}
          evacuationPriorities={priorities}
          selectedVillageId={selectedVillageId}
          onSelectVillage={setSelectedVillageId}
          loading={loading}
        />
      }
      topBar={
        <Header
          scenarioState={scenarioState}
          readinessState={readinessState}
          onScenarioChangeClick={() => setIsScenarioModalOpen(true)}
          onDemoReset={handleDemoReset}
          backendError={backendError}
          activeTab={activeTab}
          isSimulationActive={!!activeSimulation}
          villages={currentVillages}
          onSelectVillage={setSelectedVillageId}
        />
      }
      banner={
        backendError ? (
          <div className="absolute top-20 left-1/2 -translate-x-1/2 z-50 bg-red-950/90 border border-red-500/80 text-red-200 px-6 py-3 rounded-2xl shadow-2xl backdrop-blur-md flex items-center gap-3 font-mono text-xs max-w-xl">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
            <div className="flex-1">{backendError}</div>
            <button
              onClick={loadData}
              className="bg-red-600 text-white font-extrabold px-3 py-1 rounded-xl hover:bg-red-500 transition flex items-center gap-1.5 cursor-pointer"
            >
              <RefreshCw className="w-3.5 h-3.5" /> Retry
            </button>
          </div>
        ) : null
      }
    >
      {/* Dynamic View Router based on active operational phase */}
      <AppRouter
        activeTab={activeTab}
        villages={currentVillages}
        selectedVillageId={selectedVillageId}
        onSelectVillage={setSelectedVillageId}
        selectedVillageDetail={selectedVillageDetail}
        selectedLandslide={selectedLandslide}
        priorities={priorities}
        roads={roads}
        shelters={shelters}
        shelterRec={shelterRec}
        impact={riskOverview?.impact_summary || null}
        loading={loading}
        dataMode={readinessState?.data_mode}
        activeSimulation={activeSimulation}
        onSimulationUpdate={setActiveSimulation}
        onCalculateRoute={handleCalculateRoute}
        routeLoading={routeLoading}
        onOpenSmsModal={() => setIsSmsModalOpen(true)}
      />

      {/* Hydro-Meteorological Scenario Selector Modal */}
      <ScenarioControl
        isOpen={isScenarioModalOpen}
        onClose={() => setIsScenarioModalOpen(false)}
        currentScenario={scenarioState?.scenario || 'HEAVY_RAIN'}
        onSelectScenario={handleSelectScenario}
        loading={scenarioUpdating}
      />

      {/* Emergency Alert Dispatch Simulation Modal */}
      <EmergencySmsModal
        isOpen={isSmsModalOpen}
        onClose={() => setIsSmsModalOpen(false)}
        village={selectedVillageDetail}
        shelterRec={shelterRec}
        priorityDetail={priorities.find((p) => p.village_id === selectedVillageId)}
      />
    </OperationalLayout>
  );
};

export default AppShell;
