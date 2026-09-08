import { StationRegionInfo } from '../types';
import {
  CANONICAL_VILLAGES_MAP,
  CANONICAL_VILLAGES_METADATA,
  getCanonicalVillageMetadata,
} from '../data/canonicalVillages';

export {
  CANONICAL_VILLAGES_METADATA,
  CANONICAL_VILLAGES_MAP,
  getCanonicalVillageMetadata,
};

/**
 * Regional dialects and descriptors aligned directly with canonical backend village data.
 */
const REGIONAL_DESCRIPTORS: Record<
  string,
  {
    stationNumber: number;
    region: string;
    primaryLanguage: string;
    fallbackLanguage: string;
    technicalLanguage: string;
  }
> = {
  'VIL-001': {
    stationNumber: 1,
    region: 'Alaknanda Valley, Chamoli',
    primaryLanguage: 'Garhwali',
    fallbackLanguage: 'Hindi',
    technicalLanguage: 'English',
  },
  'VIL-002': {
    stationNumber: 2,
    region: 'Alaknanda Valley, Chamoli',
    primaryLanguage: 'Garhwali',
    fallbackLanguage: 'Hindi',
    technicalLanguage: 'English',
  },
  'VIL-003': {
    stationNumber: 3,
    region: 'Hemkund Corridor, Chamoli',
    primaryLanguage: 'Garhwali',
    fallbackLanguage: 'Hindi',
    technicalLanguage: 'English',
  },
  'VIL-004': {
    stationNumber: 4,
    region: 'Badrinath Valley, Chamoli',
    primaryLanguage: 'Garhwali',
    fallbackLanguage: 'Hindi',
    technicalLanguage: 'English',
  },
  'VIL-005': {
    stationNumber: 5,
    region: 'Alaknanda Basin, Chamoli',
    primaryLanguage: 'Garhwali',
    fallbackLanguage: 'Hindi',
    technicalLanguage: 'English',
  },
  'VIL-006': {
    stationNumber: 6,
    region: 'Nandakini Confluence, Chamoli',
    primaryLanguage: 'Garhwali',
    fallbackLanguage: 'Hindi',
    technicalLanguage: 'English',
  },
  'VIL-007': {
    stationNumber: 7,
    region: 'Mandakini Sangam, Rudraprayag',
    primaryLanguage: 'Garhwali',
    fallbackLanguage: 'Hindi',
    technicalLanguage: 'English',
  },
  'VIL-008': {
    stationNumber: 8,
    region: 'Mandakini Valley, Rudraprayag',
    primaryLanguage: 'Garhwali',
    fallbackLanguage: 'Hindi',
    technicalLanguage: 'English',
  },
  'VIL-009': {
    stationNumber: 9,
    region: 'Mandakini Valley, Rudraprayag',
    primaryLanguage: 'Garhwali',
    fallbackLanguage: 'Hindi',
    technicalLanguage: 'English',
  },
  'VIL-010': {
    stationNumber: 10,
    region: 'Mandakini Valley, Rudraprayag',
    primaryLanguage: 'Garhwali',
    fallbackLanguage: 'Hindi',
    technicalLanguage: 'English',
  },
  'VIL-011': {
    stationNumber: 11,
    region: 'Mandakini Gorge, Rudraprayag',
    primaryLanguage: 'Garhwali',
    fallbackLanguage: 'Hindi',
    technicalLanguage: 'English',
  },
  'VIL-012': {
    stationNumber: 12,
    region: 'Mandakini Confluence, Rudraprayag',
    primaryLanguage: 'Garhwali',
    fallbackLanguage: 'Hindi',
    technicalLanguage: 'English',
  },
  'VIL-013': {
    stationNumber: 13,
    region: 'Beas Gorge, Mandi',
    primaryLanguage: 'Mandyali',
    fallbackLanguage: 'Hindi',
    technicalLanguage: 'English',
  },
  'VIL-014': {
    stationNumber: 14,
    region: 'Vythiri Basin, Wayanad',
    primaryLanguage: 'Malayalam',
    fallbackLanguage: 'English',
    technicalLanguage: 'English',
  },
  'VIL-015': {
    stationNumber: 15,
    region: 'Vellarimala Slope, Wayanad',
    primaryLanguage: 'Malayalam',
    fallbackLanguage: 'English',
    technicalLanguage: 'English',
  },
};

/**
 * Canonical STATION_METADATA_MAP derived from backend dataset source of truth.
 * Guaranteed consistent village names, states, and coordinates with backend DEMO_VILLAGES.
 */
export const STATION_METADATA_MAP: Record<string, StationRegionInfo> = Object.fromEntries(
  CANONICAL_VILLAGES_METADATA.map((canonical) => {
    const desc = REGIONAL_DESCRIPTORS[canonical.village_id] || {
      stationNumber: 1,
      region: `${canonical.district}, ${canonical.state}`,
      primaryLanguage: 'Hindi',
      fallbackLanguage: 'Hindi',
      technicalLanguage: 'English',
    };
    return [
      canonical.village_id,
      {
        villageId: canonical.village_id,
        stationNumber: desc.stationNumber,
        villageName: canonical.village_name,
        region: desc.region,
        state: canonical.state,
        primaryLanguage: desc.primaryLanguage,
        fallbackLanguage: desc.fallbackLanguage,
        technicalLanguage: desc.technicalLanguage,
      },
    ];
  })
);

export function getStationMetadata(villageId?: string | null): StationRegionInfo {
  if (!villageId || !STATION_METADATA_MAP[villageId]) {
    return STATION_METADATA_MAP['VIL-001'];
  }
  return STATION_METADATA_MAP[villageId];
}
