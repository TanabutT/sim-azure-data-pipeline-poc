# Quick Start - 5 Minutes

## Prerequisites Check

```bash
# Verify you have everything
docker --version              # Should be 4.10+
docker-compose --version      # Should exist
python3 --version             # Should be 3.11+
git --version                 # Should exist
```

## Step 1: Prepare (1 min)

```bash
# Navigate to project
cd sim-azure-data-pipeline-poc

# Create environment file
cp .env.example .env
```

## Step 2: Build & Start (3 mins)

```bash
# Build containers
docker-compose build

# Start all services
docker-compose up -d

# Wait for health checks
docker-compose ps
# Wait until all show "healthy"
```

## Step 3: Initialize (1 min)

```bash
# Initialize storage
python scripts/init_storage.py

# Verify setup
python scripts/verify_setup.py
```

## 🎉 You're Done!

### Access Points

| Service | URL |
|---------|-----|
| **Jupyter Lab** (Data Transformation) | http://localhost:8888 |
| **Data Factory API** (Orchestration) | http://localhost:8000/docs |
| **Azurite Storage** (Blob Storage) | http://localhost:10000 |
| **PostgreSQL** (Database) | localhost:5432 |

---

## Try It Out

### Create a Pipeline

```bash
curl -X POST http://localhost:8000/api/pipelines \
  -H "Content-Type: application/json" \
  -d @pipelines/examples/simple_copy.json
```

### Run the Pipeline

```bash
curl -X POST http://localhost:8000/api/pipelines/SimpleCopyPipeline/run \
  -H "Content-Type: application/json" \
  -d '{"pipeline_name": "SimpleCopyPipeline", "trigger": "Manual"}'
```

### Check Status

```bash
curl http://localhost:8000/api/runs/1
```

---

## Useful Commands

```bash
# View service status
docker-compose ps

# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f data-factory
docker-compose logs -f spark

# Run tests
pytest tests/ -v

# Stop services
docker-compose down

# Full reset (careful!)
docker-compose down -v
```

---

## Documentation

- **Full Setup Guide**: [SETUP.md](SETUP.md)
- **Architecture Details**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **Implementation Status**: [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)
- **Main README**: [README.md](README.md)

---

## Troubleshooting

### Containers won't start?
```bash
docker-compose logs
# Check for error messages
```

### Can't access Jupyter?
```bash
docker-compose restart spark
# Wait 30 seconds, try http://localhost:8888
```

### API not responding?
```bash
curl http://localhost:5000/health
# Should return {"status": "healthy"}
```

### Database issues?
```bash
python scripts/verify_setup.py
# Shows detailed health status
```

---

## Next Steps

1. ✅ Services are running
2. 📚 Read [ARCHITECTURE.md](ARCHITECTURE.md) to understand the system
3. 🚀 Create custom pipelines using the API
4. 🔧 Add transformations in `services/databricks/transformations/`
5. 📊 Explore data in Jupyter Lab
6. 🧪 Run tests: `pytest tests/ -v`

---

## Need Help?

- **Setup Issues?** → See [SETUP.md](SETUP.md)
- **Architecture Questions?** → See [ARCHITECTURE.md](ARCHITECTURE.md)
- **API Usage?** → Open http://localhost:5000/docs
- **Implementation Details?** → See [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)

---

**Everything is ready to go! 🎉**

Your Azure Data Pipeline POC is fully functional and ready to use.
