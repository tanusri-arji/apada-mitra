/**
 * Canonical Shelter Metadata Source for APADA MITRA.
 * Sourced directly from the authoritative backend datasets (backend/app/adapters/shelter_adapter.py and backend/app/data/shelters.py).
 * Guaranteed exact match for IDs SH-01 through SH-08.
 */

export interface CanonicalShelterMetadata {
  shelter_id: string;
  name: string;
  state: 'Uttarakhand' | 'Himachal Pradesh' | 'Kerala';
  district: string;
  latitude: number;
  longitude: number;
  elevation: number;
}

export const CANONICAL_SHELTERS_METADATA: CanonicalShelterMetadata[] = [
  { shelter_id: 'SH-01', name: 'Pipalkoti Central High School Relief Complex', state: 'Uttarakhand', district: 'Chamoli', latitude: 30.4400, longitude: 79.4100, elevation: 1380.0 },
  { shelter_id: 'SH-02', name: 'Gopeshwar District Sports Stadium & Hall', state: 'Uttarakhand', district: 'Chamoli', latitude: 30.4200, longitude: 79.3200, elevation: 1620.0 },
  { shelter_id: 'SH-03', name: 'Rudraprayag Army Base Emergency Camp', state: 'Uttarakhand', district: 'Rudraprayag', latitude: 30.2950, longitude: 78.9600, elevation: 990.0 },
  { shelter_id: 'SH-04', name: 'Ukhimath Ridge High Plateau Shelter', state: 'Uttarakhand', district: 'Rudraprayag', latitude: 30.5200, longitude: 79.1400, elevation: 1560.0 },
  { shelter_id: 'SH-05', name: 'Kedarnath Valley Emergency Base Camp (Guptkashi Crest)', state: 'Uttarakhand', district: 'Rudraprayag', latitude: 30.6400, longitude: 79.0500, elevation: 1950.0 },
  { shelter_id: 'SH-06', name: 'Badrinath Safe Ridge Relief Center', state: 'Uttarakhand', district: 'Chamoli', latitude: 30.7500, longitude: 79.4700, elevation: 3250.0 },
  { shelter_id: 'SH-07', name: 'Mandi / Aut Disaster Relief Camp', state: 'Himachal Pradesh', district: 'Mandi', latitude: 31.7450, longitude: 77.1700, elevation: 1080.0 },
  { shelter_id: 'SH-08', name: 'Wayanad High Ridge Relief Shelter', state: 'Kerala', district: 'Wayanad', latitude: 11.5600, longitude: 76.1300, elevation: 860.0 },
  { shelter_id: 'SH-09', name: 'Government Primary School Pipalkoti', state: 'Uttarakhand', district: 'Chamoli', latitude: 30.4375, longitude: 79.4290, elevation: 1340.0 },
  { shelter_id: 'SH-10', name: 'Helang Panchayat Community Hall Complex', state: 'Uttarakhand', district: 'Chamoli', latitude: 30.5280, longitude: 79.4890, elevation: 1520.0 },
  { shelter_id: 'SH-11', name: 'Govindghat Gurudwara Relief & Assembly Grounds', state: 'Uttarakhand', district: 'Chamoli', latitude: 30.6260, longitude: 79.5580, elevation: 1820.0 },
  { shelter_id: 'SH-12', name: 'Pandukeshwar Secondary School Campus', state: 'Uttarakhand', district: 'Chamoli', latitude: 30.6350, longitude: 79.5490, elevation: 1920.0 },
  { shelter_id: 'SH-13', name: 'Hanuman Chatti GMVN Guest House Complex', state: 'Uttarakhand', district: 'Chamoli', latitude: 30.7020, longitude: 79.5080, elevation: 2420.0 },
  { shelter_id: 'SH-14', name: 'Badrinath Bus Stand Multi-Purpose Shelter Hall', state: 'Uttarakhand', district: 'Chamoli', latitude: 30.7420, longitude: 79.4920, elevation: 3110.0 },
  { shelter_id: 'SH-15', name: 'Lambagarh Emergency Helipad & Assembly Area', state: 'Uttarakhand', district: 'Chamoli', latitude: 30.6720, longitude: 79.5250, elevation: 2150.0 },
  { shelter_id: 'SH-16', name: 'Karnaprayag Government Inter College Campus', state: 'Uttarakhand', district: 'Chamoli', latitude: 30.2610, longitude: 79.2220, elevation: 860.0 },
  { shelter_id: 'SH-17', name: 'Nandaprayag Town Hall & Relief Center', state: 'Uttarakhand', district: 'Chamoli', latitude: 30.3340, longitude: 79.3170, elevation: 920.0 },
  { shelter_id: 'SH-18', name: 'Rudraprayag District Hospital Annex & Relief Center', state: 'Uttarakhand', district: 'Rudraprayag', latitude: 30.2880, longitude: 78.9810, elevation: 890.0 },
  { shelter_id: 'SH-19', name: 'Tilwara Community Hall & Playground Complex', state: 'Uttarakhand', district: 'Rudraprayag', latitude: 30.3540, longitude: 78.9760, elevation: 940.0 },
  { shelter_id: 'SH-20', name: 'Augustmuni Sports Stadium & Relief Assembly Complex', state: 'Uttarakhand', district: 'Rudraprayag', latitude: 30.3950, longitude: 79.0280, elevation: 1020.0 },
  { shelter_id: 'SH-21', name: 'Guptkashi Government Inter College Campus', state: 'Uttarakhand', district: 'Rudraprayag', latitude: 30.5260, longitude: 79.0760, elevation: 1480.0 },
  { shelter_id: 'SH-22', name: 'Phata Helipad Relief Assembly Center', state: 'Uttarakhand', district: 'Rudraprayag', latitude: 30.5740, longitude: 79.0390, elevation: 1540.0 },
  { shelter_id: 'SH-23', name: 'Sonprayag Evacuation Staging Complex', state: 'Uttarakhand', district: 'Rudraprayag', latitude: 30.6320, longitude: 79.0160, elevation: 1820.0 },
  { shelter_id: 'SH-24', name: 'Gaurikund Safe Staging Area', state: 'Uttarakhand', district: 'Rudraprayag', latitude: 30.6540, longitude: 79.0240, elevation: 1980.0 },
  { shelter_id: 'SH-25', name: 'Aut Government Senior Secondary School Relief Complex', state: 'Himachal Pradesh', district: 'Mandi', latitude: 31.7420, longitude: 77.2030, elevation: 1060.0 },
  { shelter_id: 'SH-26', name: 'Mandi Town Paddal Ground & Indoor Stadium Complex', state: 'Himachal Pradesh', district: 'Mandi', latitude: 31.7080, longitude: 76.9320, elevation: 760.0 },
  { shelter_id: 'SH-27', name: 'Pandoh Hydro Colony Community Center Shelter', state: 'Himachal Pradesh', district: 'Mandi', latitude: 31.6710, longitude: 77.0540, elevation: 890.0 },
  { shelter_id: 'SH-28', name: 'Bali Chowki Tehsil Relief Center Campus', state: 'Himachal Pradesh', district: 'Mandi', latitude: 31.6020, longitude: 77.1850, elevation: 1240.0 },
  { shelter_id: 'SH-29', name: 'Meppadi Government Higher Secondary School Relief Complex', state: 'Kerala', district: 'Wayanad', latitude: 11.5490, longitude: 76.1260, elevation: 780.0 },
  { shelter_id: 'SH-30', name: 'Chooralmala Community Hall & Relief Staging Center', state: 'Kerala', district: 'Wayanad', latitude: 11.5380, longitude: 76.1680, elevation: 740.0 },
  { shelter_id: 'SH-31', name: 'Vellarimala St. Joseph High School Relief Grounds', state: 'Kerala', district: 'Wayanad', latitude: 11.5280, longitude: 76.1750, elevation: 790.0 },
  { shelter_id: 'SH-32', name: 'Vythiri Model Higher Secondary School Relief Complex', state: 'Kerala', district: 'Wayanad', latitude: 11.5540, longitude: 76.0420, elevation: 700.0 },
  { shelter_id: 'SH-33', name: 'Kalpetta SKMJ Higher Secondary School Relief Grounds', state: 'Kerala', district: 'Wayanad', latitude: 11.6080, longitude: 76.0840, elevation: 780.0 },
];

export const CANONICAL_SHELTERS_MAP: Record<string, CanonicalShelterMetadata> = Object.fromEntries(
  CANONICAL_SHELTERS_METADATA.map((s) => [s.shelter_id, s])
);

export function getCanonicalShelterMetadata(shelterId?: string | null): CanonicalShelterMetadata | undefined {
  if (!shelterId) return undefined;
  return CANONICAL_SHELTERS_MAP[shelterId];
}
