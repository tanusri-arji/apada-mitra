"""
Data Source Adapters Package for APADA MITRA.
"""
from app.adapters.base import DataSourceAdapter
from app.adapters.open_meteo import OpenMeteoRainfallAdapter
from app.adapters.offline_demo import OfflineDemoAdapter

__all__ = [
    "DataSourceAdapter",
    "OpenMeteoRainfallAdapter",
    "OfflineDemoAdapter",
]
