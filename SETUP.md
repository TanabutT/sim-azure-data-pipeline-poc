# Setup Guide - Azure Data Pipeline POC

Complete step-by-step guide to set up and run the Azure Data Pipeline POC.

## Prerequisites

Before starting, ensure you have:

```
✓ Docker Desktop 4.10+ installed
✓ Python 3.11+ installed
✓ Git installed
✓ 4GB+ free disk space
✓ 4GB+ available RAM
✓ These ports available: 10000, 8888, 8000, 5432
```

### Verify Prerequisites

```bash
# Check Docker
docker --version
docker-compose --version

# Check Python
python3 --version

# Check Git
git --version
```

## Installation Steps

### Step 1: Clone Repository

```bash
cd /path/to/your/workspace
git clone <repository-url>
cd sim-azure-data-pipeline-poc
```

### Step 2: Create Environment File

Copy the example environment file and configure as needed:

```bash
cp .env.example .env
```

Default values in `.env`:

```env
AZURE_STORAGE_ACCOUNT=devstoreaccount1
AZURE_STORAGE_KEY=sharedsecretkey1
AZURITE_ENDPOINT=http://azurite:10000
DB_NAME=data_factory
DB_USER=df_user
DB_PASSWORD=postgres
SPARK_ENDPOINT=http://spark:8888
LOG_LEVEL=INFO
```

**Note**: These defaults work for local development. Change `DB_PASSWORD` for production.

### Step 3: Build Docker Images

Build all container images:

```bash
docker-compose build
```

This will:
- Download base images (PySpark, PostgreSQL, Azurite)
- Install Python dependencies
- Configure Jupyter Lab
- Prepare FastAPI service

**Duration**: 5-10 minutes on first build (depends on internet speed)

### Step 4: Start Services

Start all services in detached mode:

```bash
docker-compose up -d
```

**Output**:
```
✓ poc-azurite Started
✓ poc-postgres Started
✓ poc-spark Started
✓ poc-data-factory Started
```

### Step 5: Wait for Health Checks

Monitor the health status of containers:

```bash
docker-compose ps
```

Wait until all containers show status `Up (healthy)`:

```
NAME                 STATUS
poc-azurite          Up (healthy)
poc-postgres         Up (healthy)
poc-spark            Up (healthy)
poc-data-factory     Up (healthy)
```

**Typical wait time**: 30-60 seconds

### Step 6: Initialize Storage

Create storage containers and folder structure:

```bash
python scripts/init_storage.py
```

**Output**:
```
✓ Created container: raw
✓ Created container: curated
✓ Created container: output
✓ Created folder: raw/inbound/
✓ Uploaded: raw/inbound/sample_data.csv
✓ Storage initialization completed successfully!
```

### Step 7: Verify Setup

Verify all services are working:

```bash
python scripts/verify_setup.py
```

**Successful output**:
```
✓ Azurite Storage: ✓ PASS
✓ PostgreSQL Database: ✓ PASS
✓ Spark/Jupyter: ✓ PASS
✓ Data Factory API: ✓ PASS

✓ All checks passed (4/4)

Setup is ready for use!

Access points:
  - Jupyter Lab: http://localhost:8888
  - Data Factory API: http://localhost:8000/docs
  - Azurite Storage: http://localhost:10000
  - PostgreSQL: localhost:5432
```

## Accessing Services

Once setup is complete, you can access:

### 1. Jupyter Lab (Databricks Simulator)

**URL**: http://localhost:8888

- Create new notebooks for interactive development
- Use PySpark for data transformations
- Access Azurite storage from notebooks

### 2. Data Factory API Documentation

**URL**: http://localhost:8000/docs

Interactive API documentation where you can:
- View all available endpoints
- Test API calls directly
- Try creating and running pipelines

### 3. Azurite Storage Management

**Direct Access**: http://localhost:10000

Use Azure Storage Explorer to browse containers and blobs.

### 4. PostgreSQL Database

**Connection String**:
```
postgresql://df_user:postgres@localhost:5432/data_factory
```

**Access with psql**:
```bash
psql -h localhost -U df_user -d data_factory -c "SELECT * FROM pipelines;"
```

## Testing the Setup

### Test 1: Create a Pipeline

```bash
curl -X POST http://localhost:8000/api/pipelines \
  -H "Content-Type: application/json" \
  -d @pipelines/examples/simple_copy.json
```

**Expected response**:
```json
{
  "status": "success",
  "pipeline": {
    "id": 1,
    "name": "SimpleCopyPipeline",
    "created_at": "2024-01-01T00:00:00.000000"
  }
}
```

### Test 2: List Pipelines

```bash
curl http://localhost:8000/api/pipelines
```

**Expected response**:
```json
{
  "status": "success",
  "count": 1,
  "pipelines": [...]
}
```

### Test 3: Trigger Pipeline Execution

```bash
curl -X POST http://localhost:8000/api/pipelines/SimpleCopyPipeline/run \
  -H "Content-Type: application/json" \
  -d '{"pipeline_name": "SimpleCopyPipeline", "trigger": "Manual"}'
```

**Expected response**:
```json
{
  "status": "success",
  "run_id": 1,
  "pipeline_name": "SimpleCopyPipeline",
  "message": "Pipeline execution started"
}
```

### Test 4: Check Run Status

```bash
curl http://localhost:8000/api/runs/1
```

## Running Tests

### Install Test Dependencies

```bash
pip install pytest pytest-cov
```

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# With coverage report
pytest tests/ --cov=services --cov-report=html
```

## Viewing Logs

### View All Service Logs

```bash
docker-compose logs -f
```

### View Specific Service Logs

```bash
# Data Factory
docker-compose logs -f data-factory

# PySpark/Jupyter
docker-compose logs -f spark

# Azurite Storage
docker-compose logs -f azurite

# PostgreSQL
docker-compose logs -f postgres
```

### Search Logs

```bash
# Find errors in all logs
docker-compose logs | grep ERROR

# View last 100 lines of data-factory logs
docker-compose logs --tail=100 data-factory
```

## Troubleshooting

### Issue: Containers won't start

**Solution**:
```bash
# Check if ports are in use
lsof -i :10000  # Azurite
lsof -i :8888   # Jupyter
lsof -i :5000   # Data Factory
lsof -i :5432   # PostgreSQL

# Free ports or change docker-compose.yml
# Then restart
docker-compose down
docker-compose up -d
```

### Issue: Out of memory errors

**Solution**:
- Allocate more RAM to Docker Desktop
- Reduce number of parallel Spark operations
- Check logs: `docker-compose logs spark`

### Issue: Can't access Jupyter Lab

**Solution**:
```bash
# Check if spark container is healthy
docker-compose ps spark

# Check spark logs
docker-compose logs spark

# Restart spark
docker-compose restart spark

# Wait 30 seconds and try again
```

### Issue: Database connection refused

**Solution**:
```bash
# Check if postgres is running
docker-compose ps postgres

# Check postgres logs
docker-compose logs postgres

# Restart postgres
docker-compose restart postgres

# Test connection
docker-compose exec postgres psql -U df_user -d data_factory -c "SELECT 1"
```

### Issue: Storage (Azurite) not responding

**Solution**:
```bash
# Check azurite status
curl http://localhost:10000

# Check azurite logs
docker-compose logs azurite

# Restart azurite
docker-compose restart azurite

# Reinitialize storage
python scripts/init_storage.py
```

### Issue: API returns 500 errors

**Solution**:
```bash
# View detailed error logs
docker-compose logs -f data-factory

# Check database health
curl http://localhost:5000/api/health/database

# Verify all dependencies are healthy
python scripts/verify_setup.py
```

## Stopping and Cleanup

### Stop Containers (Data Persists)

```bash
docker-compose down
```

Containers stop but volumes persist, so your data is safe.

### Stop and Remove Everything

```bash
docker-compose down -v
```

**Warning**: This deletes all data (pipelines, runs, storage). Use only for complete reset.

### Partial Cleanup

```bash
# Stop specific container
docker-compose stop data-factory

# Restart specific container
docker-compose restart spark

# Remove only database volume
docker volume rm sim-azure-data-pipeline-poc_postgres_data
```

## Performance Optimization

### For Better Performance

1. **Increase Docker memory allocation**:
   - Docker Desktop → Settings → Resources → Memory: 8GB+

2. **Allocate more Spark cores**:
   - Edit `services/databricks/Dockerfile`
   - Add: `--master local[8]` for 8 cores

3. **Use faster disk**:
   - Place project on SSD if possible
   - Avoid network drives

### Monitor Resource Usage

```bash
# Check container resource usage
docker stats

# View memory usage
docker stats --no-stream

# Check disk usage
docker system df
```

## Next Steps

1. ✅ **Setup complete!** All services are running
2. **Explore the architecture**: Read [ARCHITECTURE.md](ARCHITECTURE.md)
3. **Try example pipelines**: Review `pipelines/examples/`
4. **Create custom pipelines**: Use Data Factory API
5. **Develop transformations**: Add jobs to `services/databricks/`
6. **Run tests**: Execute test suite to verify everything works

## Quick Reference

```bash
# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Initialize storage
python scripts/init_storage.py

# Verify setup
python scripts/verify_setup.py

# Run tests
pytest tests/ -v

# Stop services
docker-compose down
```

## Getting Help

- Check [ARCHITECTURE.md](ARCHITECTURE.md) for design details
- Review logs: `docker-compose logs -f <service>`
- Run verification: `python scripts/verify_setup.py`
- Check service health endpoints

## Success Indicators

Setup is successful when:

✓ All 4 containers show "healthy" status  
✓ `verify_setup.py` passes all checks  
✓ Can access Jupyter Lab at http://localhost:8888  
✓ Can access Data Factory API docs at http://localhost:5000/docs  
✓ Can create and run pipelines via API  
✓ Sample data appears in storage  
