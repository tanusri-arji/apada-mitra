# Architecture & Design Decisions (ADRs) - APADA MITRA

## ADR 001: Stack Selection for Day 1
- **Status**: Accepted
- **Context**: Need a rapid, reliable, and high-performance stack for geospatial visualization and probabilistic disaster risk processing.
- **Decision**:
  - **Frontend**: Vite + React + TypeScript + Tailwind CSS + Leaflet (`react-leaflet`).
  - **Backend**: Python 3.14 + FastAPI + Pydantic v2 + pytest.
- **Rationale**:
  - Leaflet provides lightweight, performant, canvas/SVG rendering for custom markers in high-density GIS maps without complex WebGL configuration.
  - FastAPI + Pydantic enforces strict runtime validation and seamless JSON serialization for domain objects.

## ADR 002: Server-Side Source of Truth for Calculations
- **Status**: Accepted
- **Context**: Risk calculations must be consistent across map visualizations, list filters, and intelligence panels.
- **Decision**: All risk, exposure, and explainability calculations are performed strictly on the backend inside Python service modules. The frontend acts exclusively as a consumer of backend API responses.
- **Rationale**: Prevents logic divergence between UI and analytics, ensuring deterministic behavior during scenario changes.

## ADR 003: Deterministic Data Layer with PostGIS Ready Schema
- **Status**: Accepted
- **Context**: A full PostgreSQL/PostGIS database instance setup could introduce installation overhead or delay vertical slice execution.
- **Decision**: Implement a local in-memory dataset manager in Python (`backend/app/data/dataset.py`) structured with standard GeoJSON-compatible fields (`latitude`, `longitude`, `elevation`, `slope`, `flow_accumulation`, `infrastructure`).
- **Rationale**: Guarantees zero-dependency startup for Day 1 while keeping data schema identical to standard PostGIS geometry tables for Day 2 integration.

## ADR 004: Transparent Factor Contribution Breakdown
- **Status**: Accepted
- **Context**: Disaster management commanders require actionable explanations, not black-box predictions or generic boilerplate text.
- **Decision**: Each feature's weighted impact is calculated mathematically during the risk scoring pass. The top contributing factors are returned in structured JSON with numerical values and percentage contribution.
- **Rationale**: Ensures 100% transparency, accuracy, and auditability for decision support.
