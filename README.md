# PySpark + Azure Blob Storage POC

Docker-based PySpark environment with Azure Blob Storage (ADLS Gen2) emulation for data processing.

## Quick Start

### Prerequisites

- Docker Desktop 4.10+
- Python 3.11+ (for CLI tools)
- Git
- 4GB+ disk space
- 4GB+ RAM

### Setup (3 minutes)

```bash
# Clone and navigate
cd sim-azure-data-pipeline-poc

# Create environment file
cp .env.example .env

# Build and start
docker-compose build
docker-compose up -d

# Wait for services to be healthy
docker-compose ps

# Initialize storage
python scripts/init_storage.py

# Verify setup
python scripts/verify_setup.py
```

### Access Services

- **Jupyter Lab**: http://localhost:8888
- **Azurite Storage**: http://localhost:10000
- **Spark UI**: http://localhost:4040

## What's Included

### Azurite (Blob Storage Emulator)

Emulates Azure Blob Storage and ADLS Gen2.

- **Port**: 10000 (Blob), 10001 (Queue), 10002 (Table)
- Connection String: `DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=sharedsecretkey1;BlobEndpoint=http://azurite:10000/`

### PySpark + Jupyter (Data Processing)

Apache Spark with Delta Lake support for data transformations.

- **Port**: 8888 (Jupyter Lab)
- **Port**: 4040 (Spark UI)
- Libraries: PySpark, Delta Lake, Pandas, NumPy, PyArrow

## Usage

### 1. Open Jupyter Lab

Visit http://localhost:8888 to create notebooks and process data.

### 2. Example: Read from Blob Storage

```python
from services.databricks import SparkSessionFactory

# Create Spark session
spark = SparkSessionFactory.create_session()

# Read CSV from Azurite
df = spark.read.csv(
    "abfss://raw@devstoreaccount1.dfs.core.windows.net/inbound/sample_data.csv",
    header=True
)

# Show data
df.show()
```

### 3. Example: Write to Blob Storage

```python
# Write as Parquet
df.write.parquet(
    "abfss://curated@devstoreaccount1.dfs.core.windows.net/output/",
    mode="overwrite"
)

# Write as Delta Lake
df.write.format("delta").save(
    "abfss://curated@devstoreaccount1.dfs.core.windows.net/delta_output/",
    mode="overwrite"
)
```

### 4. Data Transformations

Create transformation classes in `services/databricks/transformations/`:

```python
from services.databricks.transformations.base import Transformation
from pyspark.sql import functions as F

class MyTransform(Transformation):
    def execute(self, input_df):
        return input_df.filter(F.col("value") > 100)
```

## Project Structure

```
sim-azure-data-pipeline-poc/
├── docker-compose.yml              # Container orchestration
├── .env.example                    # Environment template
├── README.md                        # This file
│
├── services/
│  ├── common/                      # Shared utilities
│  │  ├── config.py
│  │  ├── storage_client.py
│  │  └── exceptions.py
│  └── databricks/                  # PySpark + Jupyter
│     ├── Dockerfile
│     ├── requirements.txt
│     ├── spark_factory.py
│     ├── transformations/
│     │  ├── base.py
│     │  ├── data_cleaner.py
│     │  └── aggregations.py
│     └── notebooks/
│
├── data/                           # Data storage
│  └── sample/
│     └── sample_data.csv
│
└── scripts/
   ├── init_storage.py              # Initialize storage
   └── verify_setup.py              # Verify setup
```

## Common Tasks

### Upload Data to Storage

```bash
python scripts/upload_data.py --file data/my_file.csv --container raw --path inbound/
```

### View Storage Contents

```bash
python scripts/list_storage.py
```

### Run Tests

```bash
pytest tests/ -v
```

### View Logs

```bash
docker-compose logs -f spark
docker-compose logs -f azurite
```

## Stopping Services

```bash
# Stop containers (data persists)
docker-compose down

# Stop and remove all volumes (complete reset)
docker-compose down -v
```

## Creating Transformation Jobs

1. Create a new file in `services/databricks/transformations/`
2. Extend the `Transformation` base class
3. Implement the `execute()` method

Example:
```python
from services.databricks.transformations.base import Transformation
from pyspark.sql import functions as F

class FilterByValue(Transformation):
    def __init__(self, spark, name, min_value):
        super().__init__(spark, name)
        self.min_value = min_value

    def execute(self, input_df):
        return input_df.filter(F.col("value") >= self.min_value)
```

## Next Steps

1. Open Jupyter Lab (http://localhost:8888)
2. Create a new notebook
3. Read data from `abfss://raw@devstoreaccount1.dfs.core.windows.net/`
4. Transform and write to `abfss://curated@devstoreaccount1.dfs.core.windows.net/`
5. Check results in Azure Storage Explorer or via API

## License

MIT License
