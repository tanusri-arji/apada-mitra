import { CanonicalVillageMetadata } from '../types';

/**
 * Canonical Village Metadata Source for APADA MITRA.
 * Sourced directly from the authoritative backend dataset (backend/app/data/dataset.py).
 * Guaranteed exact match for IDs VIL-001 through VIL-015.
 */
export const CANONICAL_VILLAGES_METADATA: CanonicalVillageMetadata[] = [
  {
    village_id: 'VIL-001',
    village_name: 'Pipalkoti',
    state: 'Uttarakhand',
    district: 'Chamoli',
    latitude: 30.4300,
    longitude: 79.4300,
    slope: 28.5,
  },
  {
    village_id: 'VIL-002',
    village_name: 'Helang',
    state: 'Uttarakhand',
    district: 'Chamoli',
    latitude: 30.5200,
    longitude: 79.5100,
    slope: 34.0,
  },
  {
    village_id: 'VIL-003',
    village_name: 'Govindghat',
    state: 'Uttarakhand',
    district: 'Chamoli',
    latitude: 30.6200,
    longitude: 79.5600,
    slope: 36.5,
  },
  {
    village_id: 'VIL-004',
    village_name: 'Badrinath Base Valley',
    state: 'Uttarakhand',
    district: 'Chamoli',
    latitude: 30.7400,
    longitude: 79.4900,
    slope: 22.0,
  },
  {
    village_id: 'VIL-005',
    village_name: 'Karnaprayag Reach',
    state: 'Uttarakhand',
    district: 'Chamoli',
    latitude: 30.2600,
    longitude: 79.2200,
    slope: 18.0,
  },
  {
    village_id: 'VIL-006',
    village_name: 'Nandaprayag Basin',
    state: 'Uttarakhand',
    district: 'Chamoli',
    latitude: 30.3300,
    longitude: 79.3200,
    slope: 21.0,
  },
  {
    village_id: 'VIL-007',
    village_name: 'Rudraprayag Sangam',
    state: 'Uttarakhand',
    district: 'Rudraprayag',
    latitude: 30.2850,
    longitude: 78.9800,
    slope: 19.5,
  },
  {
    village_id: 'VIL-008',
    village_name: 'Tilwara Valley',
    state: 'Uttarakhand',
    district: 'Rudraprayag',
    latitude: 30.3500,
    longitude: 79.0300,
    slope: 16.0,
  },
  {
    village_id: 'VIL-009',
    village_name: 'Augustmuni Stream',
    state: 'Uttarakhand',
    district: 'Rudraprayag',
    latitude: 30.3900,
    longitude: 79.0800,
    slope: 24.0,
  },
  {
    village_id: 'VIL-010',
    village_name: 'Guptkashi Slope',
    state: 'Uttarakhand',
    district: 'Rudraprayag',
    latitude: 30.5250,
    longitude: 79.0800,
    slope: 31.0,
  },
  {
    village_id: 'VIL-011',
    village_name: 'Phata Funnel',
    state: 'Uttarakhand',
    district: 'Rudraprayag',
    latitude: 30.5700,
    longitude: 79.0500,
    slope: 37.5,
  },
  {
    village_id: 'VIL-012',
    village_name: 'Sonprayag Confluence',
    state: 'Uttarakhand',
    district: 'Rudraprayag',
    latitude: 30.6300,
    longitude: 79.0100,
    slope: 38.0,
  },
  {
    village_id: 'VIL-013',
    village_name: 'Aut / Mandi',
    state: 'Himachal Pradesh',
    district: 'Mandi',
    latitude: 31.7400,
    longitude: 77.1600,
    slope: 26.0,
  },
  {
    village_id: 'VIL-014',
    village_name: 'Meppadi / Wayanad',
    state: 'Kerala',
    district: 'Wayanad',
    latitude: 11.5500,
    longitude: 76.1200,
    slope: 24.0,
  },
  {
    village_id: 'VIL-015',
    village_name: 'Chooralmala / Vellarimala',
    state: 'Kerala',
    district: 'Wayanad',
    latitude: 11.5100,
    longitude: 76.1700,
    slope: 32.0,
  },
];

export const CANONICAL_VILLAGES_MAP: Record<string, CanonicalVillageMetadata> = Object.fromEntries(
  CANONICAL_VILLAGES_METADATA.map((v) => [v.village_id, v])
);

export function getCanonicalVillageMetadata(villageId?: string | null): CanonicalVillageMetadata {
  if (!villageId || !CANONICAL_VILLAGES_MAP[villageId]) {
    return CANONICAL_VILLAGES_METADATA[0];
  }
  return CANONICAL_VILLAGES_MAP[villageId];
}
