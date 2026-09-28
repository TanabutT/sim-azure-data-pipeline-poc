# Azure Data Pipeline POC

Docker-based simulation of Azure data pipeline services including Blob Storage (ADLS Gen2), Azure Databricks, and Azure Data Factory.

## Quick Start

### Prerequisites

- Docker Desktop 4.10+ (or Docker + Docker Compose)
- Python 3.11+ (for CLI tools)
- Git
- 4GB+ available disk space
- 4GB+ available RAM

### Setup (5 minutes)

```bash
# 1. Clone and navigate
git clone <repo>
cd sim-azure-data-pipeline-poc

# 2. Create environment file
cp .env.example .env

# 3. Build containers
docker-compose build

# 4. Start services
docker-compose up -d

# 5. Wait for containers to be healthy
docker-compose ps

# 6. Initialize storage
python scripts/init_storage.py

# 7. Verify setup
python scripts/verify_setup.py
```

### Access Services

Once setup is complete:

- **Jupyter Lab**: http://localhost:8888
- **Data Factory API**: http://localhost:8000/docs
- **Azurite Storage**: http://localhost:10000
- **PostgreSQL**: localhost:5432

## Project Structure

```
sim-azure-data-pipeline-poc/
├── docker-compose.yml           # Multi-container orchestration
├── .env.example                 # Environment template
├── ARCHITECTURE.md              # Detailed architecture guide
├── README.md                    # This file
│
├── services/
│  ├── common/                   # Shared utilities
│  │  ├── config.py
│  │  ├── storage_client.py
│  │  └── exceptions.py
│  ├── databricks/               # PySpark + Jupyter
│  │  ├── Dockerfile
│  │  ├── requirements.txt
│  │  ├── spark_factory.py
│  │  ├── transformations/
│  │  └── notebooks/
│  ├── data-factory/             # Orchestration API
│  │  ├── Dockerfile
│  │  ├── requirements.txt
│  │  ├── app.py
│  │  ├── orchestrator.py
│  │  ├── activities.py
│  │  ├── scheduler.py
│  │  ├── models.py
│  │  └── database.py
│  └── storage/
│     └── init-db.sql            # Database initialization
│
├── pipelines/
│  └── examples/
│     ├── simple_copy.json       # Copy activity example
│     └── end_to_end.json        # Full pipeline example
│
├── data/
│  └── sample/
│     └── sample_data.csv        # Sample input data
│
├── scripts/
│  ├── init_storage.py           # Initialize storage
│  └── verify_setup.py           # Verify system
│
└── tests/
   ├── unit/
   │  └── test_storage_client.py
   └── integration/
      └── test_e2e_pipeline.py
```

## Components

### 1. Azurite (Blob Storage Emulator)

Emulates Azure Blob Storage and ADLS Gen2. Provides REST API compatible with Azure Storage.

- **Port**: 10000 (Blob), 10001 (Queue), 10002 (Table)
- **Connection String**: `DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=sharedsecretkey1;BlobEndpoint=http://azurite:10000/`

### 2. PySpark + Jupyter (Databricks Simulator)

Apache Spark with Delta Lake support for data transformations.

- **Port**: 8888 (Jupyter)
- **Features**: Interactive notebooks, Delta Lake, Data transformations

### 3. Data Factory API

FastAPI-based orchestration engine for pipeline execution and scheduling.

- **Port**: 8000 (REST API)
- **API Docs**: http://localhost:8000/docs

### 4. PostgreSQL

Metadata and execution tracking database.

- **Port**: 5432
- **Database**: data_factory

## Usage

### Create a Pipeline

```bash
curl -X POST http://localhost:8000/api/pipelines \
  -H "Content-Type: application/json" \
  -d @pipelines/examples/simple_copy.json
```

### Run a Pipeline

```bash
curl -X POST http://localhost:8000/api/pipelines/SimpleCopyPipeline/run \
  -H "Content-Type: application/json" \
  -d '{
    "pipeline_name": "SimpleCopyPipeline",
    "trigger": "Manual"
  }'
```

### Check Pipeline Status

```bash
curl http://localhost:8000/api/runs/1
```

### List All Pipelines

```bash
curl http://localhost:8000/api/pipelines
```

## Development

### Running Tests

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# All tests with coverage
pytest tests/ --cov=services --cov-report=html
```

### Using Jupyter Lab

1. Open http://localhost:8888
2. Create a new notebook
3. Use the `SparkSessionFactory` to create Spark sessions

```python
from services.databricks import SparkSessionFactory

spark = SparkSessionFactory.create_session()
df = spark.read.csv("wasbs://raw@azurite:10000/inbound/data.csv")
```

### Adding Custom Transformations

1. Create a new file in `services/databricks/transformations/`
2. Extend the `Transformation` base class
3. Implement the `execute()` method

Example:
```python
from services.databricks.transformations.base import Transformation

class MyTransform(Transformation):
    def execute(self, input_df):
        # Your transformation logic
        return output_df
```

## Monitoring

### Database Queries

Connect to PostgreSQL and query execution history:

```sql
SELECT * FROM pipelines;
SELECT * FROM runs ORDER BY created_at DESC;
SELECT * FROM activity_executions WHERE run_id = 1;
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f data-factory
docker-compose logs -f spark
```

## Troubleshooting

### Containers won't start

```bash
# Check Docker status
docker ps
docker-compose ps

# View logs
docker-compose logs
```

### Can't connect to Azurite

```bash
# Test connectivity
curl http://localhost:10000

# Restart Azurite
docker-compose restart azurite
```

### Database connection issues

```bash
# Test PostgreSQL
psql -h localhost -U df_user -d data_factory

# Check logs
docker-compose logs postgres
```

### Jupyter Lab not accessible

```bash
# Restart Spark container
docker-compose restart spark

# View logs
docker-compose logs spark
```

## Environment Variables

See `.env.example` for all configurable options:

- `AZURE_STORAGE_ACCOUNT` - Storage account name
- `AZURE_STORAGE_KEY` - Storage account key
- `AZURITE_ENDPOINT` - Azurite endpoint URL
- `DATABASE_URL` - PostgreSQL connection string
- `SPARK_ENDPOINT` - Spark/Jupyter endpoint
- `LOG_LEVEL` - Application log level (INFO, DEBUG, etc.)

## Stopping Services

```bash
# Stop containers (data persists)
docker-compose down

# Stop and remove all volumes (complete reset)
docker-compose down -v
```

## Architecture Documentation

For detailed architecture information, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Next Steps

1. Review [ARCHITECTURE.md](ARCHITECTURE.md) for detailed design
2. Explore pipeline examples in `pipelines/examples/`
3. Create sample transformations in `services/databricks/transformations/`
4. Build custom pipelines using the Data Factory API

## Contributing

Contributions are welcome! Please ensure:

- All tests pass: `pytest tests/ -v`
- Code follows Python conventions
- Documentation is updated

## License

MIT License
