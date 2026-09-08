"""
Authoritative DEM (Digital Elevation Model) Data Adapter & Terrain Derivation Engine.
Fetches real DEM elevation rasters from Open-Meteo / Open-Elevation APIs (Copernicus DEM GLO-90),
and derives 2D vector gradient slope and true D8 single flow direction hydrological accumulation.

Source Provenance Documentation:
- Open-Meteo Elevation API officially uses the Copernicus DEM GLO-90 (90m resolution).
- Open-Elevation API provides DEM data from Copernicus DEM / SRTM 90m.
"""
import json
import math
import heapq
import logging
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)


class OpenElevationDEMAdapter:
    """
    Adapter for Open-Meteo & Open-Elevation REST APIs (Copernicus DEM GLO-90 at 90m resolution).
    Fetches DEM elevation rasters and derives:
    1. Horn 2D finite difference vector gradient slope steepness.
    2. True D8 single flow direction matrix and accumulated upstream catchment cells.
    """

    def __init__(self):
        self._cooldown_until = None
        self._cooldown_seconds = 30.0

    @property
    def name(self) -> str:
        return "Open-Meteo Elevation API (Copernicus DEM GLO-90)"

    @property
    def dem_resolution(self) -> str:
        return "90m (Copernicus DEM GLO-90)"

    def fetch_raster_grid(self, latitude: float, longitude: float, grid_size: int = 9) -> Optional[Dict[str, Any]]:
        """
        Fetches an NxN DEM elevation raster matrix centered at (latitude, longitude).
        Default grid_size=9 (81 cell points).
        """
        now = datetime.now(timezone.utc)
        if self._cooldown_until is not None and now < self._cooldown_until:
            return None

        step = 0.001  # ~100m grid step in WGS84 coordinates
        half = grid_size // 2

        grid_coords = []
        lats_str = []
        lons_str = []

        for r in range(grid_size):
            # Row 0 is North (+lat), Row grid_size-1 is South (-lat)
            offset_lat = (half - r) * step
            row_coords = []
            for c in range(grid_size):
                # Col 0 is West (-lon), Col grid_size-1 is East (+lon)
                offset_lon = (c - half) * step
                p_lat = round(latitude + offset_lat, 4)
                p_lon = round(longitude + offset_lon, 4)
                row_coords.append((p_lat, p_lon))
                lats_str.append(f"{p_lat:.4f}")
                lons_str.append(f"{p_lon:.4f}")
            grid_coords.append(row_coords)

        # 1. Primary Source: Open-Meteo Elevation REST API (Copernicus DEM GLO-90)
        try:
            url = f"https://api.open-meteo.com/v1/elevation?latitude={','.join(lats_str)}&longitude={','.join(lons_str)}"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "APADA-MITRA-Disaster-Intelligence/1.0"}
            )
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    elevations = data.get("elevation", [])
                    if len(elevations) == grid_size * grid_size:
                        matrix = []
                        idx = 0
                        for r in range(grid_size):
                            row = []
                            for c in range(grid_size):
                                row.append(float(elevations[idx]))
                                idx += 1
                            matrix.append(row)
                        self._cooldown_until = None
                        return {
                            "matrix": matrix,
                            "center_elevation": matrix[half][half],
                            "grid_size": grid_size,
                                                    "source": "Open-Meteo Elevation API (Copernicus DEM GLO-90)",
                            "resolution": self.dem_resolution,
                            "window_size": f"{grid_size}x{grid_size} grid (~1km x 1km local window)",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
        except Exception as e:
            logger.info(f"Open-Meteo DEM fetch skipped/unreachable: {e}. Trying fallback Open-Elevation POST API...")

        # 2. Secondary Fallback: Open-Elevation POST REST API
        try:
            locations = [{"latitude": float(la), "longitude": float(lo)} for la, lo in zip(lats_str, lons_str)]
            payload = json.dumps({"locations": locations}).encode("utf-8")
            req2 = urllib.request.Request(
                "https://api.open-elevation.com/api/v1/lookup",
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "APADA-MITRA-Disaster-Intelligence/1.0",
                }
            )
            with urllib.request.urlopen(req2, timeout=4.0) as resp2:
                if resp2.status == 200:
                    data2 = json.loads(resp2.read().decode("utf-8"))
                    results = data2.get("results", [])
                    if len(results) == grid_size * grid_size:
                        matrix = []
                        idx = 0
                        for r in range(grid_size):
                            row = []
                            for c in range(grid_size):
                                row.append(float(results[idx]["elevation"]))
                                idx += 1
                            matrix.append(row)

                        return {
                            "matrix": matrix,
                            "center_elevation": matrix[half][half],
                            "grid_size": grid_size,
                            "source": "Open-Elevation API (Copernicus DEM 90m)",
                            "resolution": self.dem_resolution,
                            "window_size": f"{grid_size}x{grid_size} grid (~1km x 1km local window)",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
        except Exception as e2:
                       logger.info(f"Secondary Open-Elevation POST fetch skipped/unreachable: {e2}")

        self._cooldown_until = datetime.now(timezone.utc) + timedelta(seconds=self._cooldown_seconds)
        return None
    def derive_slope(self, matrix: List[List[float]], cell_size_m: float = 90.0) -> float:
        """
        Derives slope in degrees at matrix center using Horn 2D finite difference vector gradients:
        dz/dx = (z_east - z_west) / (2 * cell_size)
        dz/dy = (z_north - z_south) / (2 * cell_size)
        slope = arctan(sqrt((dz/dx)^2 + (dz/dy)^2))
        """
        rows = len(matrix)
        cols = len(matrix[0])
        r_c = rows // 2
        c_c = cols // 2

        z_e = matrix[r_c][c_c + 1]
        z_w = matrix[r_c][c_c - 1]
        z_n = matrix[r_c - 1][c_c]
        z_s = matrix[r_c + 1][c_c]

        dz_dx = (z_e - z_w) / (2.0 * cell_size_m)
        dz_dy = (z_n - z_s) / (2.0 * cell_size_m)

        slope_rad = math.atan(math.sqrt(dz_dx**2 + dz_dy**2))
        slope_deg = round(math.degrees(slope_rad), 1)

        return min(90.0, max(0.0, slope_deg))

    def fill_depressions(self, matrix: List[List[float]], epsilon: float = 0.01) -> List[List[float]]:
        """
        Hydro-enforces DEM raster by resolving sinks/pits using the Wang & Liu / Planchon & Darboux priority-flood algorithm.
        Guarantees monotonic drainage path connectivity to the raster boundary.
        """
        rows = len(matrix)
        cols = len(matrix[0])
        filled = [[float("inf") for _ in range(cols)] for _ in range(rows)]
        pq = []

        # Initialize raster boundaries as spill outlets
        for r in range(rows):
            for c in range(cols):
                if r == 0 or r == rows - 1 or c == 0 or c == cols - 1:
                    filled[r][c] = matrix[r][c]
                    heapq.heappush(pq, (matrix[r][c], r, c))

        neighbors = [
            (-1, 0), (1, 0), (0, -1), (0, 1),
            (-1, -1), (-1, 1), (1, -1), (1, 1)
        ]

        while pq:
            elev, r, c = heapq.heappop(pq)
            for dr, dc in neighbors:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols:
                    if filled[nr][nc] == float("inf"):
                        new_elev = max(matrix[nr][nc], elev + epsilon)
                        filled[nr][nc] = new_elev
                        heapq.heappush(pq, (new_elev, nr, nc))

        return filled

    def derive_d8_flow_accumulation(
        self,
        matrix: List[List[float]],
        cell_size_m: float = 90.0,
        target_row: Optional[int] = None,
        target_col: Optional[int] = None,
        apply_depression_filling: bool = True,
    ) -> Tuple[List[List[float]], float, float]:
        """
        Derives D8 hydrological flow direction matrix and calculates true upstream flow accumulation cell routing across the DEM raster.
        
        Returns:
            Tuple of (full_accumulation_matrix, target_cell_log_index, target_cell_raw_accumulated_cells)
        """
        # 1. Depression handling
        work_matrix = self.fill_depressions(matrix) if apply_depression_filling else matrix

        rows = len(work_matrix)
        cols = len(work_matrix[0])
        r_t = target_row if target_row is not None else rows // 2
        c_t = target_col if target_col is not None else cols // 2

        # 8 Neighbor offsets: (dr, dc), distance multiplier
        neighbors = [
            (-1, 0, 1.0),            # N
            (1, 0, 1.0),             # S
            (0, 1, 1.0),             # E
            (0, -1, 1.0),            # W
            (-1, 1, math.sqrt(2)),   # NE
            (-1, -1, math.sqrt(2)),  # NW
            (1, 1, math.sqrt(2)),    # SE
            (1, -1, math.sqrt(2)),   # SW
        ]

        # 2. D8 Flow Direction Pointers: find neighbor with max positive drop gradient
        flow_dir = [[None for _ in range(cols)] for _ in range(rows)]
        for r in range(rows):
            for c in range(cols):
                z_curr = work_matrix[r][c]
                max_drop = 0.0
                best_dest = None

                for dr, dc, dist_factor in neighbors:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols:
                        z_neigh = work_matrix[nr][nc]
                        drop = (z_curr - z_neigh) / (dist_factor * cell_size_m)
                        if drop > max_drop:
                            max_drop = drop
                            best_dest = (nr, nc)

                flow_dir[r][c] = best_dest

        # 3. D8 Flow Accumulation: sort cells by elevation descending and accumulate runoff
        acc = [[1.0 for _ in range(cols)] for _ in range(rows)]
        cell_list = []
        for r in range(rows):
            for c in range(cols):
                cell_list.append((work_matrix[r][c], r, c))

        cell_list.sort(key=lambda item: item[0], reverse=True)

        for _, r, c in cell_list:
            dest = flow_dir[r][c]
            if dest is not None:
                dr, dc = dest
                acc[dr][dc] += acc[r][c]

        raw_accumulated_cells = float(acc[r_t][c_t])

        # Log10 index scaling into domain range [1.0, 5.0]
        log_index = round(min(5.0, max(1.0, math.log10(raw_accumulated_cells + 1.0) * 2.5)), 2)

        return acc, log_index, raw_accumulated_cells
