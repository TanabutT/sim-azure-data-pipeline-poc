# Azure Data Pipeline POC - Architecture & Implementation Plan

**Project**: Docker-based Azure Data Pipeline Proof of Concept  
**Objective**: Simulate Azure Blob Storage (ADLS Gen2), Azure Databricks, and Azure Data Factory in a local Docker environment

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Docker Containerization Strategy](#docker-containerization-strategy)
3. [Data Pipeline Flow](#data-pipeline-flow)
4. [Technology Stack](#technology-stack)
5. [Implementation Phases](#implementation-phases)
6. [Project Directory Structure](#project-directory-structure)
7. [Local Development Setup](#local-development-setup)
8. [Testing & Validation](#testing--validation)
9. [Critical Implementation Decisions](#critical-implementation-decisions)
10. [Constraints & Trade-offs](#constraints--trade-offs)
11. [Validation Checklist](#validation-checklist)

---

## Architecture Overview

The POC consists of 5 containerized services orchestrated via Docker Compose. The system simulates an enterprise data pipeline with storage, compute, and orchestration layers.

### System Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    LOCAL DOCKER ENVIRONMENT                 │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────┐   ┌──────────────────────┐        │
│  │   ADLS Gen2 Emulator │   │  Data Source / Mock  │        │
│  │   (Azurite)          │   │     (CSV/Parquet)    │        │
│  │  - Blob Storage      │◄──┤                      │        │
│  │  - Data Lake Gen2    │   └──────────────────────┘        │
│  │  - APIs Compatible   │                                    │
│  └──────────┬───────────┘                                    │
│             │                                                 │
│             ▼                                                 │
│  ┌──────────────────────┐                                   │
│  │ PySpark Container    │   (Simulates Databricks)          │
│  │  - Jupyter Notebook  │                                   │
│  │  - PySpark Jobs      │                                   │
│  │  - Delta Lake Format │                                   │
│  │  - Transformation    │                                   │
│  └──────────┬───────────┘                                    │
│             │                                                 │
│             ▼                                                 │
│  ┌──────────────────────────────┐                           │
│  │   Data Factory Simulator      │                          │
│  │  - Python/FastAPI Container  │                          │
│  │  - Orchestration Logic       │                          │
│  │  - Pipeline Definitions      │                          │
│  │  - Activity Execution        │                          │
│  └──────────┬───────────────────┘                           │
│             │                                                 │
│             ▼                                                 │
│  ┌──────────────────────┐                                   │
│  │  PostgreSQL Database │                                   │
│  │  - Execution History │                                   │
│  │  - Metrics & Logs    │                                   │
│  └──────────────────────┘                                   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Shared Network (docker-compose)              │   │
│  │    - Environment variables                           │   │
│  │    - Shared storage volumes                          │   │
│  │    - Health checks                                   │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Docker Containerization Strategy

### Container 1: Azurite (ADLS Gen2 + Blob Storage Emulator)

**Purpose**: Emulate Azure Blob Storage and Data Lake Storage Gen2

**Image**: `mcr.microsoft.com/azure-storage/azurite:latest`

**Key Features**:
- REST API compatible with Azure Blob Storage
- Hierarchical namespace support (Data Lake Gen2)
- Local file persistence via volumes
- Connection string: `DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;...`

**Configuration**:
- **Port**: 10000 (Blob), 10001 (Queue), 10002 (Table)
- **Volume**: Mount `/data/` for persistence
- **Health Check**: REST API endpoint validation

**Why Azurite**: Official Microsoft emulator, production-grade quality, full ADLS Gen2 support, actively maintained

---

### Container 2: PySpark/Databricks Simulator

**Purpose**: Simulate Azure Databricks compute environment with transformation capabilities

**Base Image**: `jupyter/pyspark-notebook:latest` or custom

**Key Features**:
- Apache Spark with Delta Lake support
- Jupyter Lab for interactive development
- Pre-installed libraries: pyspark, delta-spark, pandas, numpy, pyarrow
- Ability to read/write from Azurite
- Support for Delta table format (ACID transactions, schema evolution)

**Configuration**:
- **Port**: 8888 (Jupyter)
- **Volumes**:
  - Shared notebooks directory
  - Spark warehouse directory
  - Connection to Azurite

**Environment Variables**:
```
AZURE_STORAGE_ACCOUNT=devstoreaccount1
AZURE_STORAGE_KEY=sharedsecretkey1
AZURITE_ENDPOINT=http://azurite:10000
```

**Why PySpark**: Open-source, Delta Lake support, runs locally, skill transfer to real Databricks

---

### Container 3: Data Factory Orchestrator

**Purpose**: Simulate Azure Data Factory pipeline orchestration and scheduling

**Base Image**: `python:3.11-slim`

**Framework**: FastAPI + APScheduler

**Key Features**:
- JSON-based pipeline definitions (mimic ARM templates)
- Schedule/trigger simulation with APScheduler
- Activity execution framework
- Linked services configuration
- Logging and monitoring
- Support for Copy, Spark, and custom activities

**Configuration**:
- **Port**: 8000 (REST API)
- **Endpoints**:
  - `GET /api/pipelines` — List pipelines
  - `POST /api/pipelines/{id}/run` — Trigger execution
  - `GET /api/runs` — View execution history
  - `GET /api/runs/{id}` — Pipeline run details

**Activities Supported**:
- **CopyActivity**: Transfer data between storage locations
- **SparkActivity**: Execute PySpark transformations
- **WebActivity**: Call external APIs
- **WaitActivity**: Delays between activities
- **IfConditionActivity**: Branching logic

**Why Custom**: Full control, lightweight, testable, learnable architecture

---

### Container 4: PostgreSQL Database

**Purpose**: Store pipeline execution history, metrics, and metadata

**Image**: `postgres:15-alpine`

**Configuration**:
- **Port**: 5432
- **Volume**: Persistent data storage

**Database Schema**:
```sql
-- Pipelines table
CREATE TABLE pipelines (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) UNIQUE,
  definition JSONB,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Pipeline runs table
CREATE TABLE runs (
  id SERIAL PRIMARY KEY,
  pipeline_id INT REFERENCES pipelines(id),
  status VARCHAR(50), -- pending, running, succeeded, failed
  start_time TIMESTAMP,
  end_time TIMESTAMP,
  error_message TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Activity executions table
CREATE TABLE activity_executions (
  id SERIAL PRIMARY KEY,
  run_id INT REFERENCES runs(id),
  activity_name VARCHAR(255),
  activity_type VARCHAR(50),
  status VARCHAR(50),
  start_time TIMESTAMP,
  end_time TIMESTAMP,
  output JSONB
);
```

---

### Container 5: Control/CLI Container (Optional)

**Purpose**: Run utility commands, tests, and administrative tasks

**Base Image**: `python:3.11-slim`

**Use Cases**:
- Data ingestion and validation
- Pipeline testing
- Monitoring commands
- Administrative operations

---

## Data Pipeline Flow

### Standard Data Journey

```
PHASE 1: Data Ingestion
└─ Source Data (CSV/Parquet files)
   └─ Upload to Azurite (Raw Zone)
   
PHASE 2: Data Transformation (Databricks Simulator)
└─ PySpark job reads from Raw zone
   └─ Performs transformations (filtering, aggregation, enrichment)
   └─ Writes to Curated zone (Delta Lake format)
   └─ Stores metadata/schema

PHASE 3: Orchestration (Data Factory Simulator)
└─ Triggers transformation pipeline on schedule
   └─ Monitors execution status
   └─ Handles error scenarios (retries, alerts)
   └─ Records execution metrics to PostgreSQL
   
PHASE 4: Validation & Output
└─ Quality checks on output data
   └─ Publish to final output zone
   └─ Generate execution reports
```

### Data Zones Architecture

```
Azurite Storage Hierarchy:
/raw/
  /inbound/
    - source_data.csv
    - transaction_logs.parquet
    - customer_data.csv
/curated/
  /transformed_data/
    - delta_table_v1/
      - _delta_log/
      - part-00000.parquet
      - part-00001.parquet
/output/
  - final_reports/
    - monthly_summary.parquet
    - aggregated_metrics.csv
```

### Sample Pipeline Execution

1. **Trigger**: Scheduled time or manual trigger via API
2. **Fetch Pipeline Definition**: Read JSON configuration
3. **Execute Activities**:
   - Copy: Move data from inbound to processing zone
   - Spark: Transform data using PySpark job
   - Copy: Move curated data to output zone
4. **Log Execution**: Record status, timing, outputs to PostgreSQL
5. **Handle Errors**: Retry logic, error notifications
6. **Notify**: Completion status (webhook, logs, API)

---

## Technology Stack

| Component | Technology | Why | Key Libraries |
|-----------|-----------|-----|---|
| **Blob Storage** | Azurite | Official emulator, full API compatibility | azure-storage-blob |
| **Databricks** | PySpark + Jupyter | Open-source, Delta Lake, runs locally | pyspark, delta-spark, pyarrow |
| **Data Factory** | FastAPI + APScheduler | Modern, lightweight, testable | fastapi, uvicorn, apscheduler |
| **Data Format** | Delta Lake / Parquet | Open format, ACID, schema evolution | delta, pandas, pyarrow |
| **Configuration** | JSON + YAML | Version-controllable, familiar | jsonschema |
| **Metadata DB** | PostgreSQL | SQL queryable, lightweight, standard | psycopg2, sqlalchemy |
| **Monitoring** | PostgreSQL + Logs | Track execution, queryable history | python logging |
| **Container Orchestration** | Docker Compose | Simple, built-in, no extra tools | docker-compose |

---

## Implementation Phases

### Phase 1: Foundation & Setup (Week 1)

**Objective**: Establish Docker infrastructure and basic connectivity

**Tasks**:
1. Create `docker-compose.yml` with Azurite + PostgreSQL
2. Set up `.env` configuration file for credentials/endpoints
3. Create `Dockerfile` for Data Factory orchestrator
4. Build custom Jupyter+PySpark image with dependencies
5. Establish shared Docker network
6. Create volume structure for data persistence
7. Health check endpoints for all containers

**Deliverables**:
- `docker-compose.yml`
- `.env.example`
- `Dockerfile.data-factory`
- `Dockerfile.pyspark`
- `requirements.txt` (Python dependencies)
- `docker-compose.override.yml` (local dev overrides)

---

### Phase 2: Azurite + Storage Integration (Week 1-2)

**Objective**: Set up ADLS Gen2 emulation and basic data loading

**Tasks**:
1. Configure Azurite container with proper storage account settings
2. Create container initialization script (create folders/containers)
3. Develop data ingestion script (upload sample datasets)
4. Create Azure SDK client wrappers with connection string abstraction
5. Implement data validation utilities
6. Set up volume mounts for persistent storage

**Deliverables**:
- `services/storage/azurite-init.sh` (initialization script)
- `services/storage/connection_factory.py` (Azure SDK wrapper)
- `data/sample/` (sample datasets)
- `scripts/upload_data.py` (data ingestion)
- `scripts/validate_storage.py` (validation)

---

### Phase 3: Databricks Simulator - PySpark Layer (Week 2-3)

**Objective**: Build transformation engine using PySpark + Delta Lake

**Tasks**:
1. Create PySpark Dockerfile with Delta Lake dependencies
2. Implement Spark session factory with Azurite configuration
3. Develop transformation job templates:
   - Read from raw zone
   - Apply transformations
   - Write to curated zone (Delta format)
4. Create Jupyter notebooks for interactive development
5. Implement schema validation and data quality checks
6. Set up Spark logging and monitoring

**Deliverables**:
- `services/databricks/Dockerfile`
- `services/databricks/spark_factory.py` (Spark session setup)
- `services/databricks/transformations/` (transformation jobs)
- `services/databricks/notebooks/` (Jupyter notebooks)
- `services/databricks/schema_registry.py` (schema management)
- `services/databricks/requirements.txt`

---

### Phase 4: Data Factory Orchestrator (Week 3-4)

**Objective**: Build pipeline orchestration and scheduling

**Tasks**:
1. Create Data Factory simulator structure:
   - Pipeline definition parser (JSON → execution plan)
   - Activity executor (executes Copy, Spark, Wait activities)
   - Trigger/schedule manager (APScheduler)
   - Linked services manager (connection strings)
2. Implement activity types:
   - **CopyActivity**: Transfer data between storage locations
   - **SparkActivity**: Execute PySpark transformations
   - **WebActivity**: Call external APIs
   - **WaitActivity**: Delays
   - **IfConditionActivity**: Branching logic
3. Create REST API for pipeline management
4. Implement execution logging and state persistence
5. Add retry logic and error handling
6. Create pipeline definition schema

**Deliverables**:
- `services/data-factory/Dockerfile`
- `services/data-factory/app.py` (FastAPI app)
- `services/data-factory/orchestrator.py` (core engine)
- `services/data-factory/activities.py` (activity implementations)
- `services/data-factory/scheduler.py` (scheduling)
- `services/data-factory/models.py` (data models/schemas)
- `services/data-factory/database.py` (database connection)
- `services/data-factory/api/routes.py` (API endpoints)
- `services/data-factory/requirements.txt`
- `pipelines/definitions/` (example pipelines)

---

### Phase 5: Integration & End-to-End Flow (Week 4-5)

**Objective**: Connect all components into working pipeline

**Tasks**:
1. Test Azurite → PySpark connection
2. Test PySpark → Azurite storage output
3. Configure Data Factory to execute PySpark jobs
4. Create sample end-to-end pipeline
5. Implement pipeline execution monitoring dashboard
6. Set up logging aggregation
7. Create execution history queries

**Deliverables**:
- `docker-compose.yml` (finalized)
- `pipelines/examples/end-to-end.json` (sample pipeline)
- `services/monitoring/query_execution_history.py`
- `tests/integration/` (integration tests)

---

### Phase 6: CLI & Developer Tools (Week 5)

**Objective**: Developer experience and operational tooling

**Tasks**:
1. Create CLI for common operations:
   - `docker-compose up`
   - `./cli.py run-pipeline <pipeline-name>`
   - `./cli.py upload-data <source>`
   - `./cli.py query-history`
   - `./cli.py reset-all`
2. Create health check dashboard
3. Develop seed data scripts
4. Create troubleshooting documentation

**Deliverables**:
- `cli.py` (CLI tool)
- `scripts/` (utility scripts)
- `docs/OPERATIONS.md`

---

## Project Directory Structure

```
sim-azure-data-pipeline-poc/
├── docker-compose.yml              # Main orchestration
├── docker-compose.override.yml     # Local dev overrides
├── .env.example                    # Environment template
├── .gitignore                      # Git ignore rules
├── README.md                        # Project overview
├── ARCHITECTURE.md                 # Architecture documentation
├── cli.py                          # CLI tool
│
├── services/
│  ├── storage/                     # Azurite configuration
│  │  ├── Dockerfile                # Custom Azurite (if needed)
│  │  ├── azurite-init.sh          # Initialize containers
│  │  └── config.json              # Azurite settings
│  │
│  ├── databricks/                  # PySpark Jupyter layer
│  │  ├── Dockerfile               # Custom Jupyter+PySpark
│  │  ├── requirements.txt
│  │  ├── spark_factory.py          # Spark session factory
│  │  ├── transformations/
│  │  │  ├── __init__.py
│  │  │  ├── base.py               # Base transformation class
│  │  │  ├── data_cleaner.py       # Example: cleaning transforms
│  │  │  └── aggregations.py       # Example: aggregation transforms
│  │  ├── notebooks/
│  │  │  ├── 01_exploration.ipynb
│  │  │  └── 02_transformations.ipynb
│  │  └── schema_registry.py
│  │
│  ├── data-factory/                # Orchestration layer
│  │  ├── Dockerfile
│  │  ├── requirements.txt
│  │  ├── app.py                   # FastAPI application
│  │  ├── orchestrator.py           # Execution engine
│  │  ├── activities.py             # Activity implementations
│  │  ├── scheduler.py              # Schedule/trigger handler
│  │  ├── models.py                # Data models/schemas
│  │  ├── database.py              # PostgreSQL connection
│  │  ├── api/
│  │  │  ├── __init__.py
│  │  │  └── routes.py             # API endpoints
│  │  └── __init__.py
│  │
│  ├── monitoring/                  # Monitoring utilities
│  │  ├── __init__.py
│  │  ├── logger.py
│  │  └── query_execution_history.py
│  │
│  └── common/                      # Shared utilities
│     ├── __init__.py
│     ├── config.py
│     ├── storage_client.py         # Azure SDK wrapper
│     └── exceptions.py
│
├── pipelines/                      # Pipeline definitions
│  ├── definitions/
│  │  └── schema.json              # JSON schema for pipelines
│  ├── examples/
│  │  ├── simple_copy.json         # Copy activity example
│  │  ├── spark_transform.json     # Spark job example
│  │  └── end_to_end.json          # Full pipeline
│  └── templates/
│     └── pipeline_template.json
│
├── data/                           # Data management
│  ├── sample/
│  │  ├── input.csv
│  │  └── transactions.parquet
│  ├── seed/
│  │  └── init_data.csv
│  └── .gitkeep
│
├── scripts/                        # Utility scripts
│  ├── __init__.py
│  ├── upload_data.py              # Ingest data to storage
│  ├── init_storage.py             # Initialize containers/folders
│  ├── verify_setup.py             # Health checks
│  ├── reset_all.py                # Clean slate reset
│  └── generate_sample_data.py     # Create test datasets
│
├── tests/                          # Test suite
│  ├── __init__.py
│  ├── unit/
│  │  ├── __init__.py
│  │  ├── test_spark_transforms.py
│  │  ├── test_activities.py
│  │  └── test_storage_client.py
│  ├── integration/
│  │  ├── __init__.py
│  │  ├── test_e2e_pipeline.py
│  │  └── test_databricks_storage.py
│  ├── fixtures/
│  │  └── pipeline_definitions.json
│  └── conftest.py                # Pytest fixtures
│
├── docs/
│  ├── ARCHITECTURE.md             # Architecture details (this file)
│  ├── SETUP.md                    # Setup instructions
│  ├── OPERATIONS.md               # Running pipelines
│  ├── DEVELOPMENT.md              # Dev guide
│  ├── API.md                      # Data Factory API docs
│  └── TROUBLESHOOTING.md         # Common issues
│
└── .claude/
   └── CLAUDE.md                   # Codebase documentation
```

---

## Local Development Setup

### Prerequisites

```yaml
Software:
  - Docker Desktop >= 4.10 (or Docker + Docker Compose)
  - Python 3.11+ (for CLI tools and local testing)
  - Git
  - curl or Postman (for API testing)

Hardware:
  - 4GB+ available disk space
  - 4GB+ RAM available for containers
  - Available ports: 10000, 8888, 5000, 5432

System:
  - macOS 11+, Windows 10/11, or Linux
  - Docker Desktop with sufficient resources allocated
```

### Initial Setup Steps

```bash
# 1. Clone and navigate to project
git clone <repo>
cd sim-azure-data-pipeline-poc

# 2. Create environment file
cp .env.example .env

# 3. Build all containers
docker-compose build

# 4. Start services (detached mode)
docker-compose up -d

# 5. Wait for health checks (all should show "healthy")
docker-compose ps

# 6. Initialize storage (create containers and folders)
python scripts/init_storage.py

# 7. Verify full connectivity
python scripts/verify_setup.py

# 8. Access services:
# - Jupyter: http://localhost:8888
# - Data Factory API: http://localhost:5000/docs (Swagger UI)
# - Azurite: http://localhost:10000
# - PostgreSQL: localhost:5432
```

### Stopping and Cleanup

```bash
# Stop all containers (data persists)
docker-compose down

# Stop and remove all volumes (complete reset)
docker-compose down -v

# View logs for specific service
docker-compose logs -f data-factory

# Interactive shell in container
docker-compose exec spark bash
```

---

## Testing & Validation

### Unit Tests

Test transformation logic, activity executors, and connection factories in isolation.

**File**: `tests/unit/test_spark_transforms.py`

```bash
pytest tests/unit/ -v
```

### Integration Tests

Test component interactions and end-to-end data flow.

**File**: `tests/integration/test_e2e_pipeline.py`

**Test Scenarios**:
- Storage connectivity (create/read/write containers)
- PySpark integration (read from Azurite, transform, write back)
- Data Factory orchestration (execute pipeline, track status, retry)
- End-to-end pipeline (full data journey)

```bash
pytest tests/integration/ -v
```

### Data Validation Tests

- Schema compliance
- Data quality checks (nulls, types, ranges)
- Record counts before/after
- Delta Lake integrity

### Test Execution

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=services --cov-report=html

# Run specific test file
pytest tests/integration/test_e2e_pipeline.py -v

# Run with logging output
pytest tests/ -v -s
```

---

## Critical Implementation Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Blob Emulator** | Azurite | Official Microsoft product, production-grade, maintained, full ADLS Gen2 support |
| **Compute Simulator** | PySpark + Jupyter | Open-source, Delta Lake native, skill transfer, lightweight |
| **Orchestration** | Custom Python/FastAPI | Full control, lightweight, testable, learnable |
| **Metadata DB** | PostgreSQL | Lightweight, SQL queryable, standard, easy to inspect |
| **Config Format** | JSON + YAML | Version controllable, tooling available, familiar to data engineers |
| **Container Networking** | Docker Compose native | Simple, built-in, no extra tools, service discovery automatic |
| **Data Persistence** | Named volumes | Better than bind mounts for cross-platform consistency |

---

## Constraints & Trade-offs

### What's FULLY Simulated ✅

- **Azure Blob Storage**: Azurite is production-grade emulator
- **Storage Hierarchy**: ADLS Gen2 folders and containers
- **Spark Compute**: PySpark is open-source Spark runtime
- **Delta Lake Format**: Delta-Spark library provides ACID tables
- **Pipeline Orchestration**: Custom engine mimics Data Factory

### What's PARTIALLY Simulated ⚠️

- **Databricks UI**: We use Jupyter Lab instead (no workspace/cluster UI)
- **Data Factory UI**: We provide REST API + CLI instead of Azure portal
- **Monitoring Dashboards**: Basic PostgreSQL queries vs. Azure Monitor
- **Identity & RBAC**: Connection strings instead of Managed Identity

### What's NOT Included ❌

- **Real Databricks**: Too resource-intensive, cloud-only service
- **Real Data Factory**: Cloud-only managed service
- **Azure AD Integration**: Use environment variables for secrets
- **Advanced Features**: Auto-scaling, Unity Catalog, Notebooks shared state
- **Azure Synapse Integration**: Requires cloud resources

### Performance Expectations

- Spark jobs run single-machine (not distributed cluster)
- Azurite suitable for < 10GB datasets
- Good for POCs and development; not for load testing
- Typical small pipeline execution: 30 seconds - 5 minutes

---

## Sample Docker Compose Configuration

```yaml
version: '3.8'

services:
  azurite:
    image: mcr.microsoft.com/azure-storage/azurite:latest
    ports:
      - "10000:10000"
      - "10001:10001"
      - "10002:10002"
    volumes:
      - azurite_data:/data
    environment:
      AZURITE_ACCOUNTS: devstoreaccount1:sharedsecretkey1
    healthcheck:
      test: curl -f http://localhost:10000 || exit 1
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - poc-network

  spark:
    build:
      context: services/databricks
      dockerfile: Dockerfile
    ports:
      - "8888:8888"
    volumes:
      - ./services/databricks/notebooks:/home/jovyan/work
      - spark_warehouse:/home/jovyan/spark_warehouse
      - ./data:/data
    environment:
      - AZURE_STORAGE_ACCOUNT=devstoreaccount1
      - AZURE_STORAGE_KEY=sharedsecretkey1
      - AZURITE_ENDPOINT=http://azurite:10000
    depends_on:
      azurite:
        condition: service_healthy
    networks:
      - poc-network

  postgres:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: data_factory
      POSTGRES_USER: df_user
      POSTGRES_PASSWORD: ${DB_PASSWORD:-postgres}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: pg_isready -U df_user
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - poc-network

  data-factory:
    build:
      context: services/data-factory
      dockerfile: Dockerfile
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://df_user:${DB_PASSWORD:-postgres}@postgres:5432/data_factory
      - AZURITE_ENDPOINT=http://azurite:10000
      - SPARK_ENDPOINT=http://spark:8888
      - LOG_LEVEL=INFO
    depends_on:
      postgres:
        condition: service_healthy
      azurite:
        condition: service_healthy
    networks:
      - poc-network

volumes:
  azurite_data:
  spark_warehouse:
  postgres_data:

networks:
  poc-network:
    driver: bridge
```

---

## Validation Checklist

Use this checklist to verify the POC works end-to-end:

### Infrastructure Setup
- [ ] Docker Compose starts all containers
- [ ] All containers show "healthy" status
- [ ] Docker network created and accessible
- [ ] All volumes mounted correctly

### Azurite / Storage
- [ ] Azurite REST API responds to health checks
- [ ] Can list containers via API
- [ ] Can upload file to Azurite storage
- [ ] Can list uploaded file
- [ ] File persists after container restart

### PySpark / Jupyter
- [ ] Jupyter Lab loads at http://localhost:8888
- [ ] Can create new notebook
- [ ] Spark session initializes
- [ ] Can read CSV file from Azurite
- [ ] Can write Parquet to Azurite
- [ ] Delta table creation works
- [ ] Delta log (_delta_log folder) created

### Data Factory Orchestrator
- [ ] API serves requests at http://localhost:5000
- [ ] Swagger UI accessible at /docs
- [ ] Can list pipelines via API
- [ ] Can create pipeline definition
- [ ] Can trigger pipeline execution
- [ ] Execution returns tracking ID

### Database / Metadata
- [ ] PostgreSQL accepts connections
- [ ] Tables created on startup
- [ ] Execution records saved to database
- [ ] Can query execution history

### End-to-End Pipeline
- [ ] Can execute complete pipeline
- [ ] Data flows: Azurite → PySpark → Azurite
- [ ] Pipeline status tracked
- [ ] Output data format preserved
- [ ] Execution timing recorded
- [ ] Error scenarios handled gracefully

---

## Next Steps

1. **Create foundational files**: docker-compose.yml, .env, base Dockerfiles
2. **Set up Azurite**: Initialize storage containers and test connectivity
3. **Configure PySpark**: Build Jupyter image, test Spark session
4. **Build Data Factory API**: Create FastAPI app and activity executors
5. **Integration testing**: Test end-to-end pipeline execution
6. **Documentation**: Create SETUP.md, OPERATIONS.md, API.md

---

## References

- [Azurite Documentation](https://github.com/Azure/Azurite)
- [PySpark Documentation](https://spark.apache.org/docs/latest/api/python/)
- [Delta Lake Documentation](https://docs.delta.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Azure Data Factory Documentation](https://learn.microsoft.com/en-us/azure/data-factory/)
