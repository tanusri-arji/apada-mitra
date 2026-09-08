"""
Base Data Source Adapter Interface for APADA MITRA.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.models.domain import NormalizedEnvironmentObservation


class DataSourceAdapter(ABC):
    """
    Abstract base adapter for external/internal hydrological and meteorological data sources.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the data source provider."""
        pass

    @property
    @abstractmethod
    def source_type(self) -> str:
        """Category type (e.g. METEOROLOGICAL_API, HYDROLOGICAL_API, OFFLINE_DEMO)."""
        pass

    @abstractmethod
    def fetch(self, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """
        Fetches raw observations for given geographic coordinates.
        Returns raw JSON dictionary or None if provider is unreachable/unconfigured.
        """
        pass

    @abstractmethod
    def normalize(self, raw_payload: Dict[str, Any], latitude: float, longitude: float) -> NormalizedEnvironmentObservation:
        """
        Normalizes provider-specific payload into canonical NormalizedEnvironmentObservation model.
        """
        pass

    def metadata(self) -> Dict[str, Any]:
        """Returns provider metadata."""
        return {
            "name": self.name,
            "source_type": self.source_type,
        }
