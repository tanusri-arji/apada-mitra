import React from 'react';
import { TopLevelView, VillageRiskDetail, LandslideRiskDetail, RoadSegment, Shelter, EvacuationPriority, ShelterRecommendationResult, WhatIfSimulationResponse, ImpactSummary } from '../types';
import { LiveMonitoring } from '../views/LiveMonitoring/LiveMonitoring';
import { Prediction } from '../views/Prediction/Prediction';
import { Response } from '../views/Response/Response';
import { Validation } from '../views/Validation/Validation';

interface AppRouterProps {
  activeTab: TopLevelView;
  villages: VillageRiskDetail[];
  selectedVillageId: string | null;
  onSelectVillage: (id: string) => void;
  selectedVillageDetail: VillageRiskDetail | null;
  selectedLandslide: LandslideRiskDetail | null;
  priorities: EvacuationPriority[];
  roads: RoadSegment[];
  shelters: Shelter[];
  shelterRec: ShelterRecommendationResult | null;
  impact: ImpactSummary | null;
  loading: boolean;
  dataMode?: string;
  activeSimulation: WhatIfSimulationResponse | null;
  onSimulationUpdate: (sim: WhatIfSimulationResponse | null) => void;
  onCalculateRoute: () => void;
  routeLoading: boolean;
  onOpenSmsModal: () => void;
}

export const AppRouter: React.FC<AppRouterProps> = ({
  activeTab,
  villages,
  selectedVillageId,
  onSelectVillage,
  selectedVillageDetail,
  selectedLandslide,
  priorities,
  roads,
  shelters,
  shelterRec,
  impact,
  loading,
  dataMode,
  activeSimulation,
  onSimulationUpdate,
  onCalculateRoute,
  routeLoading,
  onOpenSmsModal,
}) => {
  switch (activeTab) {
    case 'LIVE_MONITORING':
      return (
        <LiveMonitoring
          villages={villages}
          selectedVillageId={selectedVillageId}
          onSelectVillage={onSelectVillage}
          selectedVillageDetail={selectedVillageDetail}
          roads={roads}
          shelters={shelters}
          priorities={priorities}
          impact={impact}
          loading={loading}
          dataMode={dataMode}
        />
      );

    case 'PREDICTION':
      return (
        <Prediction
          villages={villages}
          selectedVillageId={selectedVillageId}
          onSelectVillage={onSelectVillage}
          selectedVillageDetail={selectedVillageDetail}
          selectedLandslide={selectedLandslide}
          roads={roads}
          shelters={shelters}
          activeSimulation={activeSimulation}
          onSimulationUpdate={onSimulationUpdate}
        />
      );

    case 'EVACUATION_ACTION':
      return (
        <Response
          villages={villages}
          selectedVillageId={selectedVillageId}
          onSelectVillage={onSelectVillage}
          selectedVillageDetail={selectedVillageDetail}
          priorities={priorities}
          roads={roads}
          shelters={shelters}
          shelterRec={shelterRec}
          onCalculateRoute={onCalculateRoute}
          routeLoading={routeLoading}
          onOpenSmsModal={onOpenSmsModal}
        />
      );

    case 'VALIDATION_REPLAY':
      return (
        <Validation
          villages={villages}
          selectedVillageId={selectedVillageId}
          onSelectVillage={onSelectVillage}
          roads={roads}
          shelters={shelters}
        />
      );

    default:
      return (
        <LiveMonitoring
          villages={villages}
          selectedVillageId={selectedVillageId}
          onSelectVillage={onSelectVillage}
          selectedVillageDetail={selectedVillageDetail}
          roads={roads}
          shelters={shelters}
          priorities={priorities}
          impact={impact}
          loading={loading}
          dataMode={dataMode}
        />
      );
  }
};
